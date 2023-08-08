from django.shortcuts import render, redirect
from .models import *
from ayushman.settings import *
from .custom_email import *
from .onetime_share import one_time_share

import json
import datetime
from datetime import timedelta
from datetime import datetime
from django.utils import timezone
import random
import string
import PyPDF2 
import io
import re
import sys
# For Image QR
import qrcode
from PIL import Image

from io import StringIO

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

# For Barcode
import barcode
from barcode import EAN13,EAN8
from barcode.writer import ImageWriter

from django.http import HttpResponse
from django.contrib import messages

from django.contrib.auth.models import User,auth

from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage

#Paginator
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# In-built middleware
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

# For custom user
from django.contrib.auth import get_user_model
User = get_user_model()

# Data Fetch
from PIL import ImageFont, ImageDraw, Image  
import cv2  
import numpy as np 

NEW_DOC_FLAG = False

def get_random_16_name():
    letters = string.ascii_uppercase + string.digits + string.ascii_lowercase
    result_str1 = ''.join(random.choice(letters) for i in range(16))
    pdf_16_name = '{}'.format(result_str1)
    return pdf_16_name


def share_doc(request):
    user = request.user
    global NEW_DOC_FLAG
    if request.method == 'GET':
        user_data = ''
        try:
            id = request.GET['id']
            user_data = User.objects.get(id=id)
        except:
            pass
        state_data = state.objects.all()
        if request.user.is_superuser:
            dis_data = User.objects.filter(is_superuser=False,is_staff=True)
        else:
            dis_data = User.objects.filter(created_by=request.user.email)
        var = {
            'is_photo': False if user.image == '' else True,
            'nbar': 'share',
            'state_data': state_data,
            'dis_data': dis_data,
            'user_data':user_data,
        }
        return render(request, 'share/share_document.html',var)

def share_new_doc(request):
    user = request.user
    if request.method == 'GET':
        user_data = share_doc_path = shareid = ''
        try:
            id = request.GET['id']
            user_data = User.objects.get(id=id)
        except:
            pass

        try:
            shareid = request.GET['shareid']
            share_doc_path = document_shared.objects.get(id=shareid)
            share_doc_path = share_doc_path.document_path
        except:
            pass
        state_data = state.objects.all()
        if request.user.is_superuser:
            dis_data = User.objects.filter(is_superuser=False,is_staff=True)
        else:
            dis_data = User.objects.filter(created_by=request.user.email)

        var = {
            'is_photo': False if user.image == '' else True,
            'nbar': 'sharenew',
            'state_data': state_data,
            'dis_data': dis_data,
            'user_data':user_data,
            'share_doc_path': share_doc_path,
            'shareid': shareid,
            'preview_list': '',
        }
        return render(request, 'share/share_new_document.html',var)

def share_doc_share(request):
    if request.method == 'POST':
        pdfs = request.FILES.getlist('pdfs')
        is_text = request.POST.get('is_text',False)
        is_background = request.POST.get('is_background',False)
        distributer = request.POST['distributer']

        card_text = ''
        if is_text:
            card_text = request.POST['card_text']

        for pdf in pdfs:
            file_name = get_random_16_name()
            fs = FileSystemStorage(location=TEMP_URL)
            file = fs.save(file_name, pdf)
            # fileurl = fs.url(file)
            cardPath = os.path.join(TEMP_URL, file_name)

            try:
                fetch_result = fetch_card_data(cardPath)
            except Exception as e:
                print(e)
                messages.error(request, "Kindly upload appropriate pdf file format")
                return redirect('share-doc')
            # print(fetch_result)

            userImage, delete_files = getLogo(cardPath)
            userImage = userImage[0]
            print(userImage, delete_files)

            # Delete uploaded PDF
            os.remove(cardPath)

            # print(userImage)

            # Delete Files while Photo Selection
            for i in delete_files:
                if not i == userImage:
                    os.remove(i)

            try:
                data = card_data.objects.create(serial_number=fetch_result['serialNumber'],name=fetch_result['name'],yob=fetch_result['yob'],
                    gender=fetch_result['gender'],state=fetch_result['state'],image=userImage,
                    is_text=is_text,extra_text=card_text,is_background=is_background)
                data.save()
            except:
                messages.error(request, "Something wents wrong while saving card data. {}".format(sys.exc_info()))
                return redirect('share-doc')
            
            if not request.user.is_superuser:
                dis_data = User.objects.get(email=request.user.email)
                limit_data = document_limit.objects.get(distributer=dis_data)
                limit_data.remaining_limit = (limit_data.remaining_limit - 1)
                limit_data.save()

            try:
                dis_data = User.objects.get(email=distributer)
            except:
                messages.error(request, "Distributer with given credential not found.")
                return redirect('share-doc')

            shared_data = document_shared.objects.create(distributer=dis_data,document=data,is_downloaded=True).save()
        messages.success(request,"PDFs are shared with {} successfully.".format(distributer))
        return redirect('share-doc')

def share_new_multiple_doc(request):
    if request.method == 'POST':
        result = request.POST

        result = list(result)
        result = result[1:]
        length = len(result)

        # print(result)
        # print(length)

        preview_list = []
        id_list = []

        for i in result:
            id = i.split("doc")[1]

            sh_data = document_shared_temp.objects.get(id=id)
            id_list.append(id)
            path = sh_data.document_path
            # print('-->', path)

            preview_list.append(path)
        
        # print(preview_list)

        if request.user.is_superuser:
            dis_data = User.objects.filter(is_superuser=False,is_staff=True)
        else:
            dis_data = User.objects.filter(created_by=request.user.email)
        var = {
            'nbar': 'share',
            'dis_data': dis_data,
            'preview_list': preview_list,
            'share_doc_path': '',
            'id_list': id_list,
        }
        return render(request, 'share/share_new_document.html',var)

def get_random_qr_name():
    current_year = datetime.now().year
    # choose from [0-9] and [A-Z]
    letters = string.ascii_uppercase + string.digits + string.ascii_lowercase
    result_str1 = ''.join(random.choice(letters) for i in range(4))
    random_name = '{}_{}'.format(current_year,result_str1)
    return random_name

def createQR(unique_id,name):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=20,
        border=1
    )
    qr.add_data(unique_id)

    img = qr.make_image()
    id = get_random_qr_name()
    file_name = '{} {}.png'.format(name,id)
    path = os.path.join(QR_URL, file_name)
    result = img.save(path)
    return path

import code128

def createBar(unique_id,name):

    img = code128.image(unique_id)
    width, height = img.size
    
    left = 0
    top = 0
    right = width
    bottom = height / 4
    
    img = img.crop((left, top, right, bottom))

    id = get_random_qr_name()
    file_name = "{} {}.png".format(name,id)
    path = os.path.join(BAR_URL,file_name)
    img.save(path)

    # # or sure, to an actual file:
    # barcode_writer = ImageWriter()

    # # ean = barcode.get('code128', unique_id, barcode_writer)
    # ean = barcode.get('code39', unique_id, barcode_writer)

    # id = get_random_qr_name()
    # file_name = "{} {}".format(name,id)
    # path = os.path.join(BAR_URL,file_name)

    # with open('barcode.png', 'wb') as f:
    #     EAN13('123456789102', writer=ImageWriter()).write(f)

    # ean.save(path)

    # file_name = "{} {}.png".format(name,id)
    # path = os.path.join(BAR_URL,file_name)
        
    return path

def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

def fetch_card_data(path):
    global NEW_DOC_FLAG
    # datePatten = "([a-zA-Z]{3} [a-zA-Z]{3} \d{2}) (\d{2}):(\d{2}):(\d{2}) IST \d{4}"
    # yobPatten = "YOB :\d{4}"
    # pdfFileObj = open(path, 'rb')

    # pdfReader = PyPDF2.PdfFileReader(pdfFileObj) 
    # pageObj = pdfReader.getPage(0) 
    # pageText = pageObj.extractText()
    # print('----------', pageText, '------------')
    # pageText = pageText.split(': ')[1]

    # pageText = re.sub(datePatten,"",pageText)
    # yob = re.search(yobPatten,pageText)

    # if(yob):
    #     yob = yob.group()
    #     pageText = pageText.replace(yob,"")
    #     yob = yob.split(':')[1]
    # else:
    #     yob = ''
    #     print("No YOB")

    # if re.search("FEMALE",pageText):
    #     gender = 'FEMALE'
    #     pageText = pageText.replace('FEMALE',"")
    # else:
    #     gender = 'MALE'
    #     pageText = pageText.replace('MALE',"")

    # stateList = state.objects.all() 

    # for states in stateList:
    #     s = "{}".format(states.name)
    #     # print("---------",s)
    #     if re.search(s.upper(), pageText):
    #         s = s.upper()
    #         pageText = pageText.replace(s,"")
    #         break
    #     else:
    #         s = ''

    # serialNumber = pageText[-9:]
    # name = pageText.replace(serialNumber,"")    

    # pdfFileObj.close()

    # cardDetails = {
    #     'name': name,
    #     'yob':yob,
    #     'state':s,
    #     'serialNumber':serialNumber,
    #     'gender': gender,
    # }

    # return cardDetails

    yobPatten = "YOB :\d{4}"

    output_string = StringIO()
    with open(path, 'rb') as in_file:
        parser = PDFParser(in_file)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.create_pages(doc):
            interpreter.process_page(page)

    data = output_string.getvalue()

    data = data.split('\n')[:-1]
    data = [i for i in data if i!='']

    print(data)

    cardDetails = {}
    # if 'Card' in data[0]:
    #     cardDetails['name'] = data[1]
    #     cardDetails['yob'] = data[2].replace(' ', '').split(":")[1]
    #     cardDetails['gender'] = data[3]
    #     cardDetails['serialNumber'] = data[4]
    #     cardDetails['state'] = data[5]
    # else:
    #     cardDetails['name'] = data[0]
    #     cardDetails['yob'] = data[1].replace(' ', '').split(":")[1]
    #     cardDetails['gender'] = data[2]
    #     cardDetails['serialNumber'] = data[3]
    #     cardDetails['state'] = data[4]
    #     NEW_DOC_FLAG = True
    #     print('---- else', NEW_DOC_FLAG, '-------')
    # print(cardDetails)

    if 'Card' in data[0]:
        cardDetails['name'] = data[1].replace('\t',' ')
        cardDetails['yob'] = data[2].replace(' ', '').split(":")[1]
        cardDetails['gender'] = data[3]
        cardDetails['serialNumber'] = data[4]
        cardDetails['state'] = data[5].replace('\t',' ')
    else:
        if len(data) == 5:
            cardDetails['name'] = data[0].replace('\t',' ')
            cardDetails['yob'] = data[1].replace(' ', '').split(":")[1]
            cardDetails['gender'] = data[2]
            if hasNumbers(data[3]):
                cardDetails['serialNumber'] = data[3]
                cardDetails['state'] = data[4].replace('\t',' ')
            else:
                cardDetails['state'] = data[3].replace('\t',' ')
                cardDetails['serialNumber'] = data[4]
        
            # print('---- else', NEW_DOC_FLAG, '-------')
        else:
            cardDetails['name'] = data[0].replace('\t',' ') + ' ' + data[1].replace('\t', ' ')
            cardDetails['yob'] = data[2].replace(' ', '').split(":")[1]
            cardDetails['gender'] = data[3]
            if hasNumbers(data[4]):
                cardDetails['serialNumber'] = data[4]
                cardDetails['state'] = data[5].replace('\t',' ')
            else:
                cardDetails['state'] = data[4].replace('\t',' ')
                cardDetails['serialNumber'] = data[5]
        NEW_DOC_FLAG = True
    
    print(cardDetails)

    return cardDetails

def overlayImage(cardPath,qrPath,barPath):

    card = Image.open(cardPath)
    qr = Image.open(qrPath)
    bar = Image.open(barPath)

    qr = qr.resize((round(qr.size[0]*0.25), round(qr.size[1]*0.25)))
    bar = bar.resize((round(bar.size[0]*0.6), round(bar.size[1])))

    width, height = bar.size

    left,top,right,bottom = 0,0,width,height/2
    bar = bar.crop((left, top, right, bottom))

    qrDim = (545,210)
    barDim = (80,350)
    card.paste(qr, qrDim)
    card.paste(bar, barDim)
    
    id = get_random_qr_name()
    file_name = 'card {}.png'.format(id)
    path = os.path.join(TEMP_URL,file_name)
    result = card.save(path)
    return path,file_name
 

def overlayPhoto(addQR, userImage):
    global NEW_DOC_FLAG
    card = Image.open(addQR)
    photo = Image.open(userImage)
    print(NEW_DOC_FLAG)
    if NEW_DOC_FLAG:        
        photo = photo.resize((120,160))
    else:
        photo = photo.resize((round(photo.size[0]*0.75), round(photo.size[1]*0.75)))

    photoDim = (85,135)
    card.paste(photo, photoDim)
    
    id = get_random_qr_name()
    file_name = 'Final Card {}.png'.format(id)
    path = os.path.join(TEMP_URL,file_name)
    result = card.save(path)
    return path,file_name

def fillTextToCard(imgPath,cardDetails,card_text=''):
    image = cv2.imread(imgPath)

    cv2_im_rgb = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)  

    pil_im = Image.fromarray(cv2_im_rgb)  

    draw = ImageDraw.Draw(pil_im)  

    font_path = os.path.join(FONT_URL, 'arial.ttf')
    font = ImageFont.truetype(font_path, 20)
    font1 = ImageFont.truetype(font_path, 15)

    # Name
    nameDim = (250,150)
    draw.text(nameDim, cardDetails['name'], font=font, fill="#000")

    # YOB
    yobDim = (250,180)
    draw.text(yobDim, "YOB :" + cardDetails['yob'], font=font, fill="#000")

    # Gender
    genderDim = (250,210)
    draw.text(genderDim, cardDetails['gender'], font=font, fill="#000")

    # state
    stateDim = (510,350)
    draw.text(stateDim, cardDetails['state'], font=font, fill="#000")

    # serialNumber
    serialDim = (150,380)
    draw.text(serialDim, cardDetails['serialNumber'], font=font, fill="#000")

    # extra Text
    textDim = (510,380)
    draw.text(textDim, card_text, font=font1, fill="#000")

    cv2_im_processed = cv2.cvtColor(np.array(pil_im), cv2.COLOR_RGB2BGR)

    file_name = 'textcard.png'
    path = os.path.join(TEMP_URL,file_name)
    cv2.imwrite(path,cv2_im_processed)
    
    return path

# @csrf_exempt
def change_download_status(request):
    if request.method == 'GET':
        id = request.GET['id']
        dtype = request.GET['type']

        shared_d_data = document_shared.objects.get(id=id)
        cardData = card_data.objects.get(id=shared_d_data.document.id)

        name = cardData.name
        yob = cardData.yob
        gender = cardData.gender
        state = cardData.state
        image = cardData.image
        is_text = cardData.is_text
        extra_text = cardData.extra_text
        is_background = cardData.is_background
        serial_number = cardData.serial_number

        path = one_time_share(name,yob,gender,state,image,is_background,is_text,extra_text,serial_number,dtype)

        shared_d_data.is_downloaded = False
        shared_d_data.save()

        dis_data = User.objects.get(id=shared_d_data.distributer_id)
        limit_data = document_limit.objects.get(distributer=dis_data)
        limit_data.remaining_limit = (limit_data.remaining_limit - 1)
        limit_data.save()

        docPath = os.path.join(BASE_DIR, path)
        with open(docPath, 'rb') as pdf:
            response = HttpResponse(pdf.read(),content_type='application/pdf')
            response['Content-Disposition'] = 'filename=card.pdf'
            return response

def change_download_status_new(request):
    if request.method == 'GET':
        id = request.GET['id']
        shared_d_data = document_shared_temp.objects.get(id=id)
        shared_d_data.is_downloaded = False
        shared_d_data.save()
        dis_data = User.objects.get(id=shared_d_data.distributer_id)
        limit_data = document_limit.objects.get(distributer=dis_data)
        limit_data.remaining_limit = (limit_data.remaining_limit - 1)
        limit_data.save()

        docPath = os.path.join(BASE_DIR, shared_d_data.document_path)
        with open(docPath, 'rb') as pdf:
            response = HttpResponse(pdf.read(),content_type='application/pdf')
            response['Content-Disposition'] = 'filename=card.pdf'
            return response

def createPDF(addPhoto, name):
    path1 = os.path.join(STATIC_ROOT, 'images/preview/back.png')
    path2 = addPhoto
    image1 = Image.open(path2)
    image2 = Image.open(path1)

    im1 = image1.convert('RGB')
    im2 = image2.convert('RGB')

    imagelist = [im2]

    id = get_random_qr_name()
    pdf_name = "{} {}.pdf".format(name,id)
    pdfPath = os.path.join(PDF_URL,pdf_name)
    im1.save(pdfPath, save_all=True, append_images=imagelist)

    return pdfPath,pdf_name

# Find Photo Function
import fitz
# import cv2
from PIL import Image
from pdf2image import convert_from_path, convert_from_bytes
import numpy as np

def L2Norm(H1,H2):
    distance = 0
    for i in range(len(H1)):
        distance += np.square(H1[i]-H2[i])
    return np.sqrt(distance)

def getLogo(pdf):
    global NEW_DOC_FLAG
    doc = fitz.open(pdf)
    files = []
    for i in range(len(doc)):
        for img in doc.getPageImageList(i):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            if pix.n < 5:       # this is GRAY or RGB
                # print(type(pix))
                file_name = os.path.join(PHOTO_URL,"{}.png".format(get_random_qr_name()))
                files.append(file_name)
                pix.writePNG(files[-1])
            else:               # CMYK: convert to RGB first
                pix1 = fitz.Pixmap(fitz.csRGB, pix)
                # print(type(pix))
                file_name = os.path.join(PHOTO_URL,"{}.png".format(get_random_qr_name()))
                files.append(file_name)
                pix1.writePNG(files[-1])
                pix1 = None
            pix = None

    images = convert_from_path(pdf)
    # images = convert_from_bytes(open('RAJENDRA.pdf', 'rb').read())
    image = images[0]
    image = np.asarray(image)

    # print(image.shape)
    print(NEW_DOC_FLAG)
    if not NEW_DOC_FLAG:
        image = image[290:450, 95:245]
        rs = (150, 160)
    else:
        return [files[1]], files
    image = image.flatten()
    errors = {}
    for file in files:
        img = Image.open(file)
        img = np.asarray(img)
        img = cv2.resize(img, (150, 160), interpolation=cv2.INTER_NEAREST)
    #     print(img.shape)
        img = img.flatten()
    #     print(img.shape)
        if(img.shape == image.shape):
    #         errors.append({file: L2Norm(img, image)})
            errors[file] = L2Norm(img, image)

    person = min(errors.items(), key=lambda x: x[1])
    return person, files


def share_new_doc_share(request):
    if request.method == 'POST':
        distributer = request.POST['distributer']
        if not request.user.is_superuser:
            user_data = User.objects.get(id=request.user.id)
            limit_data = document_limit.objects.get(distributer_id=user_data.id)
            if limit_data.remaining_limit < 1:
                messages.error(request, "You have exceed your daily limit.")
                return redirect('share-new-doc')

        try:
            shareid = request.POST['shareid']
            result = request.POST

            result = list(result)
            result = result[4:]
            length = len(result)
            # print(result,length)

            preview_list = []
            id_list = []

            # try:
            for i in result:
                try:
                    sh_data = document_shared_temp.objects.get(id=i)
                    sh_data.is_downloaded = False
                    sh_data.save()
                except:
                    messages.error(request, '{}'.format(sys.exc_info()))
                    return redirect('share-new-doc')

                dis_data = User.objects.get(email=distributer)
                docPath = sh_data.document_path
                docType = "NEW"
                shared_data = document_shared_temp.objects.create(distributer=dis_data,document_path=docPath,
                            is_downloaded=True,document_type=docType).save()
                
                if not request.user.is_superuser:
                    limit_data.remaining_limit = (limit_data.remaining_limit - 1)
                    limit_data.save()                

            messages.success(request,"PDFs is shared with {} successfully.".format(distributer))
            return redirect('share-new-doc')
            # except:
            #     messages.error(request, "Distributer with given credential not found.")
            #     return redirect('share-new-doc')


        except:
        #    pass
             pdfs = request.FILES.getlist('pdfs')
             for pdf in pdfs:
                 fs = FileSystemStorage(location=PDF_URL)
                 file = fs.save(pdf.name, pdf)
                 file_name = pdf.name
                 # fileurl = fs.url(file)
                 cardPath = os.path.join(PDF_URL, file_name)

                 try:
                     dis_data = User.objects.get(email=distributer)
                 except:
                     messages.error(request, "Distributer with given credential not found.")
                     return redirect('share-new-doc')

                 docPath = "media/pdf/{}".format(file_name)
                 docType = "NEW"
                 shared_data = document_shared_temp.objects.create(distributer=dis_data,document_path=docPath,
                             is_downloaded=True,document_type=docType).save()

                 if not request.user.is_superuser:
                     limit_data.remaining_limit = (limit_data.remaining_limit - 1)
                     limit_data.save()

             messages.success(request,"PDFs are shared with {} successfully.".format(distributer))
             return redirect('share-new-doc')

from .onetime_preview import one_time_preview

def share_multiple_doc(request):
    if request.method == 'POST':
        result = request.POST

        result = list(result)
        result = result[1:]
        length = len(result)

        preview_list = []
        id_list = []

        for i in result:
            print(i)
            id = i.split("doc")[1]
            print(id)
            sh_data = document_shared.objects.get(id=id)
            cardData = card_data.objects.get(id=sh_data.document.id)
            id_list.append(id)
            name = cardData.name
            yob = cardData.yob
            gender = cardData.gender
            state = cardData.state
            image = cardData.image
            #print(image, 'image')
            is_text = cardData.is_text
            extra_text = cardData.extra_text
            is_background = cardData.is_background
            serial_number = cardData.serial_number
            path = one_time_preview(name,yob,gender,state,image,is_background,is_text,extra_text,serial_number)
            # print('-->', path)

            preview_list.append(path)
        
        # print(preview_list)
        # print(id_list)

        if request.user.is_superuser:
            dis_data = User.objects.filter(is_superuser=False,is_staff=True)
        else:
            dis_data = User.objects.filter(created_by=request.user.email)
        var = {
            'nbar': 'share',
            'dis_data': dis_data,
            'preview_list': preview_list,
            'id_list': id_list,
        }
        return render(request, 'share/share_multiple_document.html',var)


def share_multiple_doc_share(request):
    if request.method == 'POST':
        
        is_background = request.POST.get('is_background',False)
        distributer = request.POST['distributer']

        try:
            dist_data = User.objects.get(email=distributer)
        except:
            messages.error(request, "Distributer with given credential not found.")
            return redirect('share-doc')

        result = request.POST
        # print(result, '\n')

        result = list(result)
        result = result[4:]
        # length = len(result)

        # print(result, '\n')
        # print(is_background,distributer)

        for i in result:
            sh_data = document_shared.objects.get(id=i)
            cardData = card_data.objects.get(id=sh_data.document.id)
            print(cardData, 'card dat')
            # cardData = card_data.objects.get(id=i)
            cardData.is_background = is_background
            if not request.user.is_superuser:
                dis_data = User.objects.get(email=request.user.email)
                dis_share_data = document_shared.objects.get(distributer=dis_data,document=cardData)
                dis_share_data.is_downloaded = False
                dis_share_data.save()
                limit_data = document_limit.objects.get(distributer=dis_data)
                limit_data.remaining_limit = (limit_data.remaining_limit - 1)
                limit_data.save()
            cardData.save()
            shared_data = document_shared.objects.create(distributer=dist_data,document=cardData,is_downloaded=True).save()

        messages.success(request,"PDFs are shared with {} successfully.".format(distributer))
        return redirect('/')

from .webviews import do_connection
import shutil

def share_multiple_dataentry_doc_share(request):
    if request.method == 'POST':
        
        is_background = request.POST.get('is_background',False)
        distributer = request.POST['distributer']

        try:
            dist_data = User.objects.get(email=distributer)
        except:
            messages.error(request, "Distributer with given credential not found.")
            return redirect('share-doc')

        result = request.POST
        # print(result, '\n')

        result = list(result)
        result = result[4:]
        # length = len(result)

        # print(result, '\n')
        # print(is_background,distributer)

        for i in result:
            # sh_data = document_shared.objects.get(id=i)
            # cardData = card_data.objects.get(id=sh_data.document.id)
            # print(i)
            connection = do_connection()
            if connection.is_connected():
                cursor = connection.cursor()

                sql_command = 'SELECT * FROM account_user_card WHERE id = {}'.format(i)

                cursor.execute(sql_command)
                records = cursor.fetchall()

                cardData = records[0]
                # id_list.append(id)
                name = cardData[2]
                yob = cardData[3]
                gender = cardData[4]
                state = cardData[5]
                image = cardData[6]
                # is_text = cardData.is_text
                extra_text = cardData[7]
                # print("--{}--".format(extra_text))
                is_text = True if extra_text != None else False
                serial_number = cardData[1]
                dest_path = os.path.join(TEMP_URL, image.split('/')[-1])
                shutil.copyfile(image, dest_path)
                image = dest_path

                try:
                    data = card_data.objects.create(serial_number=serial_number,name=name,yob=yob,
                        gender=gender,state=state,image=image,
                        is_text=is_text,extra_text=extra_text,is_background=is_background)
                    data.save()
                    # print(data)
                except:
                    messages.error(request, "Something wents wrong while saving card data. {}".format(sys.exc_info()))
                    return redirect('share-doc')
                if not request.user.is_superuser:
                    dis_data = User.objects.get(email=request.user.email)
                    dis_share_data = document_shared.objects.get(distributer=dis_data,document=data)
                    dis_share_data.is_downloaded = False
                    dis_share_data.save()
                    limit_data = document_limit.objects.get(distributer=dis_data)
                    limit_data.remaining_limit = (limit_data.remaining_limit - 1)
                    limit_data.save()
                shared_data = document_shared.objects.create(distributer=dist_data,document=data,is_downloaded=True).save()

        messages.success(request,"PDFs are shared with {} successfully.".format(distributer))
        return redirect('/')

# from django.core.files import File
# from django.core.files.temp import NamedTemporaryFile
# from urllib.request import urlopen

# def save_image_pro(url):
#     product = card_data()
#     # set all your variables here
#     product.save()
#     print(url)
#     # Save image
#     image_url = url
#     img_temp = NamedTemporaryFile()
#     img_temp.write(urlopen(image_url).read())
#     img_temp.flush()

#     product.image.save("image_%s" % product.pk, File(img_temp))
#     product.save()
#     return True