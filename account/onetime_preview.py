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

def one_time_preview(name,yob,gender,state,image,is_background,is_text,extra_text,serial_number):

    fetch_result = {
        'name': name,
        'yob':yob,
        'state':state,
        'serialNumber':serial_number,
        'gender': gender,
    }

    delete_items = []

    # print(fetch_result)
    qrPath = createQR(serial_number,name)
    delete_items.append(qrPath)

    barPath = createBar(serial_number, name)
    delete_items.append(barPath)

    if is_background:
        frontPath = os.path.join(CSS_URL,'images/preview/front.png')
    else:
        frontPath = os.path.join(CSS_URL,'images/preview/blank.png')

    if is_text:
        addText = fillTextToCard(frontPath, fetch_result, extra_text)
    else:
        addText = fillTextToCard(frontPath, fetch_result)

    delete_items.append(addText)
    addQR, nameOfFile = overlayImage(addText,qrPath,barPath)
    # print(addQR,nameOfFile)
    delete_items.append(addQR)

    # print(userImage)
    # print(addQR)

    addPhoto, addPhoto_name = overlayPhoto(addQR, image)
    # print(addPhoto,addPhoto_name)
    delete_items.append(addPhoto)

    finalPDF, finalName = createPDF(addPhoto,name)

    try:
        unnecessary_data = document_unnecessary.objects.create(document_path=finalPDF).save()
    except:
        pass

    # Delete other PDFs, QR, and Bar
    for i in delete_items:
        os.remove(i)
        
    docPath = "media/temp/{}".format(finalName)
    return docPath


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
        
    return path

def overlayImage(cardPath,qrPath,barPath):

    card = Image.open(cardPath)
    qr = Image.open(qrPath)
    bar = Image.open(barPath)

    qr = qr.resize((round(qr.size[0]*0.25), round(qr.size[1]*0.25)))
    bar = bar.resize((round(bar.size[0]*0.4), round(bar.size[1]*0.4)))

    # left,top,right,bottom = 0,0,0,30
    # bar = bar.crop((left, top, right, bottom))

    qrDim = (545,210)
    barDim = (110,350)
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
    print(userImage)

    # photo = photo.resize((round(photo.size[0]*0.75), round(photo.size[1]*0.75)))
    photo = photo.resize((100,140))

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
    pdfPath = os.path.join(TEMP_URL,pdf_name)
    im1.save(pdfPath, save_all=True, append_images=imagelist)

    return pdfPath,pdf_name


def preview_new_doc(request):
    if request.method == 'POST':
        pdfs = request.FILES.getlist('pdfs')
        distributer = request.POST['distributer']

        preview_list = []

        for pdf in pdfs:
            fs = FileSystemStorage(location=PDF_URL)
            file = fs.save(pdf.name, pdf)
            file_name = pdf.name
            # fileurl = fs.url(file)
            cardPath = os.path.join(PDF_URL, file_name)

            path = 'media/pdf/{}'.format(file_name)

            preview_list.append(path) 
            print('-->',path)      
        
        user_data = ''
        if distributer:
            user_data = User.objects.get(email=distributer)
        # messages.success(request,"PDFs are shared with {} successfully.".format(distributer))

        if request.user.is_superuser:
            dis_data = User.objects.filter(is_superuser=False,is_staff=True)
        else:
            dis_data = User.objects.filter(created_by=request.user.email)
            
        var_preview = {
            'preview_list':preview_list,
            'user_data': user_data,
            'share_doc_path': '',
            'dis_data': dis_data,
        }
        return render(request, 'share/share_new_document.html',var_preview)
        return redirect(request.get_full_path())