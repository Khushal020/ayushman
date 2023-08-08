from django.shortcuts import render, redirect
from .models import *
from ayushman.settings import *
from .custom_email import *

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

# For Image QR
import qrcode
from PIL import Image

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

def share_doc(request):
    user = request.user
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
        }
        return render(request, 'share/share_new_document.html',var)

def share_doc_share(request):
    if request.method == 'POST':
        pdfs = request.FILES.getlist('pdfs')
        is_text = request.POST.get('is_text',False)
        is_background = request.POST.get('is_background',False)
        distributer = request.POST['distributer']

        if is_text:
            card_text = request.POST['card_text']

        for pdf in pdfs:
            fs = FileSystemStorage(location=TEMP_URL)
            file = fs.save(pdf.name, pdf)
            file_name = pdf.name
            # fileurl = fs.url(file)
            cardPath = os.path.join(TEMP_URL, file_name)

            delete_items = []
            delete_items.append(cardPath)
            try:
                fetch_result = fetch_card_data(cardPath)
            except:
                messages.error(request, "Kindly upload appropriate pdf file format")
                return redirect('share-doc')
            # print(fetch_result)
            qrPath = createQR(fetch_result['serialNumber'],fetch_result['name'])
            delete_items.append(qrPath)

            barPath = createBar(fetch_result['serialNumber'],fetch_result['name'])
            delete_items.append(barPath)

            if is_background:
                frontPath = os.path.join(CSS_URL,'images/preview/front.png')
            else:
                frontPath = os.path.join(CSS_URL,'images/preview/blank.png')
            
            if is_text:
                addText = fillTextToCard(frontPath, fetch_result, card_text)
            else:
                addText = fillTextToCard(frontPath, fetch_result)

            delete_items.append(addText)
            addQR, nameOfFile = overlayImage(addText,qrPath,barPath)
            # print(addQR,nameOfFile)
            delete_items.append(addQR)

            userImage, delete_files = getLogo(cardPath)
            userImage = userImage[0]
            # delete_items.append(userImage)
            # print(userImage)
            # print(addQR)

            addPhoto, addPhoto_name = overlayPhoto(addQR, userImage)
            # print(addPhoto,addPhoto_name)
            delete_items.append(addPhoto)

            finalPDF, finalName = createPDF(addPhoto,fetch_result['name']) #PDF's name must be User name

            # Delete Files while Photo Selection
            for i in delete_files:
                os.remove(i)

            # Delete other PDFs, QR, and Bar
            for i in delete_items:
                os.remove(i)

            try:
                dis_data = User.objects.get(email=distributer)
            except:
                messages.error(request, "Distributer with given credential not found.")
                return redirect('share-doc')

            docPath = "media/pdf/{}".format(finalName)
            shared_data = document_shared.objects.create(distributer=dis_data,document_number=fetch_result['serialNumber'],document_path=docPath,
                        is_downloaded=True).save()
        messages.success(request,"PDFs are shared with {} successfully.".format(distributer))
        return redirect('share-doc')


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


def fetch_card_data(path):

    datePatten = "([a-zA-Z]{3} [a-zA-Z]{3} \d{2}) (\d{2}):(\d{2}):(\d{2}) IST \d{4}"
    yobPatten = "YOB :\d{4}"
    pdfFileObj = open(path, 'rb')

    pdfReader = PyPDF2.PdfFileReader(pdfFileObj) 
    pageObj = pdfReader.getPage(0) 
    pageText = pageObj.extractText()
    pageText = pageText.split(': ')[1]

    pageText = re.sub(datePatten,"",pageText)
    yob = re.search(yobPatten,pageText)

    if(yob):
        yob = yob.group()
        pageText = pageText.replace(yob,"")
        yob = yob.split(':')[1]
    else:
        yob = ''
        print("No YOB")

    if re.search("FEMALE",pageText):
        gender = 'FEMALE'
        pageText = pageText.replace('FEMALE',"")
    else:
        gender = 'MALE'
        pageText = pageText.replace('MALE',"")

    stateList = state.objects.all() 

    for states in stateList:
        s = "{}".format(states.name)
        # print("---------",s)
        if re.search(s.upper(), pageText):
            s = s.upper()
            pageText = pageText.replace(s,"")
            break
        else:
            s = ''

    serialNumber = pageText[-9:]
    name = pageText.replace(serialNumber,"")    

    pdfFileObj.close()

    cardDetails = {
        'name': name,
        'yob':yob,
        'state':s,
        'serialNumber':serialNumber,
        'gender': gender,
    }

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

    card = Image.open(addQR)
    photo = Image.open(userImage)

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
        shared_d_data = document_shared.objects.get(id=id)
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
    doc = fitz.open(pdf)
    files = []
    for i in range(len(doc)):
        for img in doc.getPageImageList(i):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            if pix.n < 5:       # this is GRAY or RGB
                # print(type(pix))
                file_name = os.path.join(TEMP_URL,"p%s-%s.png")
                files.append(file_name % (i, xref))
                pix.writePNG(files[-1])
            else:               # CMYK: convert to RGB first
                pix1 = fitz.Pixmap(fitz.csRGB, pix)
                # print(type(pix))
                file_name = os.path.join(TEMP_URL,"p%s-%s.png")
                files.append(file_name % (i, xref))
                pix1.writePNG(files[-1])
                pix1 = None
            pix = None

    images = convert_from_path(pdf)
    # images = convert_from_bytes(open('RAJENDRA.pdf', 'rb').read())
    image = images[0]
    image = np.asarray(image)

    # print(image.shape)
    image = image[290:450, 95:245]
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
            pdf = request.POST['file']
            shareid = request.POST['shareid']

            try:
                try:
                    shared_d_data = document_shared.objects.get(id=shareid)
                    shared_d_data.is_downloaded = False
                    shared_d_data.save()
                except:
                    messages.error(request, "{}".format(sys.exe_info()))
                    return redirect(request.get_full_path())

                dis_data = User.objects.get(email=distributer)
                docPath = pdf
                docType = "NEW"
                shared_data = document_shared.objects.create(distributer=dis_data,document_path=docPath,
                            is_downloaded=True,document_type=docType).save()
                
                if not request.user.is_superuser:
                    limit_data.remaining_limit = (limit_data.remaining_limit - 1)
                    limit_data.save()

                messages.success(request,"PDF is shared with {} successfully.".format(distributer))
                return redirect('share-new-doc')
            except:
                messages.error(request, "Distributer with given credential not found.")
                return redirect('share-new-doc')


        except:
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
                shared_data = document_shared.objects.create(distributer=dis_data,document_path=docPath,
                            is_downloaded=True,document_type=docType).save()

                if not request.user.is_superuser:
                    limit_data.remaining_limit = (limit_data.remaining_limit - 1)
                    limit_data.save()

            messages.success(request,"PDFs are shared with {} successfully.".format(distributer))
            return redirect('share-new-doc')

