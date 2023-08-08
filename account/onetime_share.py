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
import sys
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

def one_time_share(name,yob,gender,state,image,is_background,is_text,extra_text,serial_number,dtype):

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

    if dtype == 'with':
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

    # Delete other PDFs, QR, and Bar
    for i in delete_items:
        os.remove(i)
        
    docPath = "media/pdf/{}".format(finalName)
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

# @csrf_exempt
def change_download_status(request):
    if request.method == 'GET':
        id = request.GET['id']
        dtype = request.GET['type']
        if dtype == 'with':
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

            path = one_time_share(name,yob,gender,state,image,is_background,is_text,extra_text,serial_number)


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



