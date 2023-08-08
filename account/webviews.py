from django.shortcuts import render, redirect
from .models import *
# from .custom_response import Custom
from ayushman.settings import *
from .custom_email import *
from django.contrib.sessions.models import Session

import json
import datetime
from datetime import timedelta
from datetime import datetime
from django.utils import timezone
import random
import string
import csv
import sys

from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view 
from rest_framework import status
from django.http import HttpResponse
from django.contrib import messages

from django.contrib.auth.models import User,auth

from django.views.decorators.csrf import csrf_exempt

# Email Configuration modules
from django.core.mail import EmailMessage, EmailMultiAlternatives, get_connection, send_mail
from django.core.mail.backends.smtp import EmailBackend

#Paginator
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required 

from django.contrib.auth import get_user_model
User = get_user_model()

# Create your views here.

def index(request):
    user = request.user
    if request.user.is_staff:
        if request.method == 'GET':
            # print("-->",user,"|", user.session_key)
            total_admin = User.objects.filter(is_superuser=True).count()
            total_dis = User.objects.filter(is_staff=True,is_superuser=False).count()
            total_user = User.objects.filter(is_staff=False,is_superuser=False).count()

            pop_user = User.objects.filter(is_superuser=True)

            server_user = User.objects.filter(is_active=False)
            page = request.GET.get('page', 1)
            paginator = Paginator(server_user,5)
            try:
                userlist = paginator.page(page)
            except PageNotAnInteger:
                userlist = paginator.page(1)
            except EmptyPage:
                userlist = paginator.page(paginator.num_pages)

            distributer = User.objects.get(email=user)
            shared_data = document_shared.objects.filter(distributer=distributer,document_type="OLD")
            shared_data1 = document_shared_temp.objects.filter(distributer=distributer,document_type="NEW")
            btndisable,limit_data = '', ''
            if not request.user.is_superuser:
                limit_data = document_limit.objects.get(distributer_id=distributer.id)

                btndisable = ''
                if limit_data.remaining_limit <= 0:
                    btndisable = 'disabled'

            page = request.GET.get('page', 1)
            paginator = Paginator(shared_data,50)
            try:
                pdfList = paginator.page(page)
            except PageNotAnInteger:
                pdfList = paginator.page(1)
            except EmptyPage:
                pdfList = paginator.page(paginator.num_pages)

            page1 = request.GET.get('pageNew', 1)
            paginator1 = Paginator(shared_data1,15)
            try:
                pdfListNew = paginator1.page(page1)
            except PageNotAnInteger:
                pdfListNew = paginator1.page(1)
            except EmptyPage:
                pdfListNew = paginator1.page(paginator1.num_pages)

            cardData = card_data.objects.all()

            var = {
                'is_photo': False if user.image == '' else True,
                'nbar': 'home',
                'total_admin': total_admin,
                'total_user': total_user,
                'total_dis': total_dis,
                'userlist':userlist,
                'pdfList':pdfList,
                'limit_data': limit_data,
                'btndisable':btndisable,
                'pdfListNew': pdfListNew,
                'pop_user': pop_user,
                'cardData': cardData,
            }
            return render(request, 'home/index.html',var)
    else:
        if request.method == 'GET':
            distributer = User.objects.get(email=user)
            shared_data = document_shared.objects.filter(distributer=distributer)
            limit_data = document_limit.objects.get(distributer_id=distributer.id)

            btndisable = ''
            if limit_data.remaining_limit <= 0:
                btndisable = 'disabled'

            page = request.GET.get('page', 1)
            paginator = Paginator(shared_data,8)
            try:
                pdfList = paginator.page(page)
            except PageNotAnInteger:
                pdfList = paginator.page(1)
            except EmptyPage:
                pdfList = paginator.page(paginator.num_pages)

            cardData = card_data.objects.all()

            pdfListuser = document_shared_temp.objects.filter(distributer=distributer)

            var = {
                'is_photo': False if user.image == '' else True,
                'nbar': 'home',
                'shared_data': shared_data,
                'pdfList':pdfList,
                'limit_data':limit_data,
                'btndisable':btndisable,
                'cardData': cardData,
                'pdfListuser': pdfListuser,
            }
            return render(request, 'home/index.html',var)

#################### Authentication Section ####################

def check_maintenance():
    try:
        app_setting_data = app_settings.objects.get(id=1)
        maintenance = app_setting_data.is_under_maintenance
        # print("--1>",maintenance)
        if maintenance:
            return True
        else:
            return False
    except:
        return False

def login(request):
    if request.method == 'GET':
        return render(request, 'authentication/login.html')

    elif request.method == 'POST':
        uemail = request.POST['email']
        upass1 = request.POST['password']
        remember = request.POST.get('remember',False)

        User = get_user_model()
        if User.objects.filter(email=uemail).exists() or User.objects.filter(username=uemail).exists():
            if User.objects.filter(email=uemail).exists():
                user_data = User.objects.get(email=uemail)
                if user_data.session_key:
                    messages.error(request, "You already logged in other system. Kindly logout there first to login here.")
                    return redirect('login')
                user = auth.authenticate(username=user_data.username, password=upass1)
            else:
                user_data = User.objects.get(username=uemail)
                if user_data.session_key:
                    messages.error(request, "You already logged in other system. Kindly logout there first to login here.")
                    return redirect('login')
                user = auth.authenticate(username=uemail, password=upass1)

            # print('--{}--'.format(user))

            if user is not None:                    
                auth.login(request,user)
                if remember:
                    request.session.set_expiry(1209600)
                else:
                    # request.session.set_expiry(60)
                    request.session.set_expiry(1814400)
                
                # print(request.session.session_key)
                user_data.session_key = request.session.session_key
                user_data.save()

                if not user.is_superuser:
                    mainResult = check_maintenance()
                    if mainResult:
                        return redirect('logout_11')
                
                return redirect('index')
            else:
                messages.error(request, "Kindly check your password.")
                return redirect('login')
        else:
            messages.error(request, "Email Id/Username does not found in Database.")
            return redirect('login')

def logout(request):
    user = request.user
    auth.logout(request)
    user_data = User.objects.get(email=user.email)
    user_data.session_key = ''
    user_data.save()
    return redirect('login')

def logout_11(request):
    user = request.user
    auth.logout(request)
    user_data = User.objects.get(email=user.email)
    user_data.session_key = ''
    user_data.save()
    return redirect('mainfun')

def forgot(request):
    if request.method == 'GET':
        return render(request, 'authentication/forget_password.html')
    else:
        user_email = request.POST['uemail']
        if User.objects.filter(email=user_email).exists():
            udata = User.objects.get(email=user_email)
            if udata.session_key:
                udata.session_key = ''
                try:
                    session_data = Session.objects.get(session_key=udata.session_key)
                    session_data.delete()
                except:
                    pass
            udata.save()
            psw = get_random_password(udata.username)
            send = user_password_reset(user_email,psw,udata.username)
        else:
            messages.info(request,"Email '"+user_email+"' is not found in database.")
            return redirect('forgot')
        messages.success(request, "Email sent successfully")
        return redirect('forgot')

def mainfun(request):
    return render(request, 'error/500_maintenance.html')

def clear_session(request):
    if request.method == 'GET':
        return render(request, 'authentication/session.html')
    elif request.method == 'POST':
        uemail = request.POST['email']
        upass1 = request.POST['password']

        User = get_user_model()
        if User.objects.filter(email=uemail).exists() or User.objects.filter(username=uemail).exists():
            if User.objects.filter(email=uemail).exists():
                user_data = User.objects.get(email=uemail)
                user = auth.authenticate(username=user_data.username, password=upass1)
            else:
                user_data = User.objects.get(username=uemail)
                user = auth.authenticate(username=uemail, password=upass1)

            if user is not None:
                try:
                    # print("1111",user_data.session_key)
                    session_data = Session.objects.get(session_key=user_data.session_key)
                    # print(session_data)
                    session_data.delete()
                    # print("Deleted Key")
                except:
                    pass
                user_data.session_key = ''
                user_data.save()
                messages.success(request, "Session cleared successfully.")                
                return redirect('login')
            else:
                messages.error(request, "Kindly check your password.")
                return redirect('clear-session')
        else:
            messages.error(request, "Email Id/Username does not found in Database.")
            return redirect('clear-session')


#################### Admin Activity Section ####################

##### User 
@staff_member_required(login_url = '/error/')
def add_user(request):
    user = request.user
    if request.method == 'GET':
        var = {
            'is_photo': False if user.image == '' else True,
            'nbar': 'adduser',
        }
        return render(request, 'authentication/add_user.html',var)
    elif request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        fname = request.POST['fname']
        lname = request.POST['lname']
        phone = request.POST['phone']
        role = request.POST['role']
        gender = request.POST['gender']
        photo = ''
        try:
            photo = request.FILES['photo']
        except:
            pass
        if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
            messages.error(request, "Username/Email is already registered.")
            return redirect('add-user')
        pass1 = get_random_password(username)

        # print(username,email,fname,lname,phone,role,gender,photo,pass1)

        superuser, staff = False, False
        if role == '2':
            staff = True
        elif role == '3':
            superuser = True
            staff = True
        
        is_active,created_by = True,''
        if not request.user.is_superuser:
            is_active = False
            created_by = user.email
        user = User.objects.create_user(password=pass1,username=username,email=email,is_staff=staff,is_superuser=superuser,
                first_name=fname,last_name=lname,phone=phone,gender=gender,image=photo,is_active=is_active,created_by=created_by)
        user.save()
        
        try:
            result = user_password_informer(email,pass1,username)
            messages.success(request, "user added successfully")
            return redirect('add-user')
        except:
            messages.error(request, "User created but something wents wrong while sending user email.")
            return redirect('add-user')

@staff_member_required(login_url = '/error/')
def get_user(request):
    user = request.user
    if request.method == 'GET':
        if request.user.is_superuser:
            server_user = User.objects.filter(is_staff=True)
            # server_user = User.objects.all()
        else:
            server_user = User.objects.filter(created_by=user)
        page = request.GET.get('page', 1)
        paginator = Paginator(server_user,15)
        try:
            userlist = paginator.page(page)
        except PageNotAnInteger:
            userlist = paginator.page(1)
        except EmptyPage:
            userlist = paginator.page(paginator.num_pages)
        var = {
            'userlist':userlist,
            'is_photo': False if user.image == '' else True,
            'nbar': 'getuser',
        }
        return render(request, 'user/get_users.html',var)

@staff_member_required(login_url = '/error/')
def view_dis_user(request):
    if request.method == 'GET':
        if request.user.is_superuser:
            id = request.GET['id']
            user_data = User.objects.get(id=id)
            server_user = User.objects.filter(created_by=user_data.email)
            page = request.GET.get('page', 1)
            paginator = Paginator(server_user,15)
            try:
                userlist = paginator.page(page)
            except PageNotAnInteger:
                userlist = paginator.page(1)
            except EmptyPage:
                userlist = paginator.page(paginator.num_pages)
            var = {
                'userlist':userlist,
                'nbar': 'getuser',
                'disis' : id,
            }
            return render(request, 'user/get_dis_user.html',var)

@staff_member_required(login_url = '/error/')
def update_user(request):
    user = request.user
    if request.method == 'GET':
        id = request.GET['id']
        udata = User.objects.get(id=id)

        if not user.is_superuser:
            if udata.created_by == user.email:
                pass
            else:
                return redirect('error')

        g1 = 'selected' if udata.gender == 'Male' else ''
        g2 = 'selected' if udata.gender == 'Female' else ''
        g3 = 'selected' if udata.gender == 'Other' else ''

        r1 = 'selected' if not (udata.is_staff and udata.is_superuser) else ''
        r2 = 'selected' if udata.is_staff and not udata.is_superuser else ''
        r3 = 'selected' if (udata.is_staff and udata.is_superuser) else ''

        var = {
            'is_photo': False if user.image == '' else True,
            'nbar': 'adduser',
            'udata': udata,
            'g1':g1,
            'g2':g2,
            'g3':g3,
            'r1': r1,
            'r2': r2,
            'r3': r3,
        }
        return render(request, 'user/update_user.html',var)
    elif request.method == 'POST':
        fname = request.POST['fname']
        lname = request.POST['lname']
        id = request.POST['id']
        
        gender = request.POST['gender']
        phone = request.POST['phone']
        user = User.objects.get(id=id)
        user.first_name = fname
        user.last_name = lname
        user.gender = gender
        user.phone = phone
        
        if request.user.is_superuser:
            role = request.POST['role']
            superuser, staff = False, False
            if role == '2':
                staff = True
            elif role == '3':
                superuser = True
                staff = True
            user.is_superuser = superuser
            user.is_staff = staff

        try:
            photo = request.FILES['photo']
            user.image = photo
        except:
            pass
        user.save()
        messages.success(request, "profile updated successfully")
        return redirect(request.get_full_path())

@staff_member_required(login_url = '/error/')
def delete_user(request):
    user = request.user
    if request.method == 'GET':
        id = request.GET['id']
        udata = User.objects.get(id=id)
        name = udata.username

        if not user.is_superuser:
            if udata.created_by == user.email:
                pass
            else:
                return redirect('error')
        try:
            udata.delete()
            messages.success(request, "User ({}) deleted successfully".format(name))
            return redirect('get-user')
        except:
            messages.error(request, "Something wents wrong while deleting user ({}).".format(name))
            return redirect('get-user')

def view_profile(request):
    user = request.user
    if request.method == 'GET':
        var = {
            'is_photo': False if user.image == '' else True,
        }
        return render(request, 'authentication/view_profile.html',var)
    elif request.method == 'POST':
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        is_change = request.POST.get('is_change',False)
        user = User.objects.get(email=email)
        user.first_name = fname
        user.last_name = lname
        try:
            photo = request.FILES['photo']
            # print(photo)
            user.image = photo
        except:
            pass
        if is_change:
            pass1 = request.POST['password1']
            pass2 = request.POST['password2']
            if pass1 == pass2:
                user.session_key = ''
                user.session_key = ''
                user.set_password(pass1)
                user.save()
                print(user.session_key)
                messages.success(request, "profile updated successfully")
                return redirect('view-profile')
            else:
                messages.error(request,"password not match.")
                return redirect('view-profile')
        else:
            user.save()
            messages.success(request, "profile updated successfully")
            return redirect('view-profile')

@staff_member_required(login_url = '/error/')
def approve_user(request):
    if request.method == 'GET':
        id = request.GET['id']
        user_data = User.objects.get(id=id)
        user_data.is_active = True
        user_data.save()

        messages.success(request,"User {} is approved by you.".format(user_data.email))
        return redirect('index')

@staff_member_required(login_url = '/error/')
def decline_user(request):
    if request.method == 'GET':
        id = request.GET['id']
        try:
            user_data = User.objects.get(id=id)
            user_data.delete()
        except:
            messages.error(request,"Something wents wrong. Please Try again.")
            return redirect('index')

        messages.success(request,"User {} is rejected by you.".format(user_data.email))
        return redirect('index')

##### State
@staff_member_required(login_url = '/error/')
def get_states(request):
    user = request.user
    if request.method == 'GET':
        state_data = state.objects.all()
        page = request.GET.get('page', 1)
        paginator = Paginator(state_data,10)
        try:
            statelist = paginator.page(page)
        except PageNotAnInteger:
            statelist = paginator.page(1)
        except EmptyPage:
            statelist = paginator.page(paginator.num_pages)
        var = {
            'statelist':statelist,
            'is_photo': False if user.image == '' else True,
            'nbar': 'states',
        }
        return render(request, 'state/get_states.html',var)

@staff_member_required(login_url = '/error/')
def add_state(request):
    user = request.user
    if request.method == 'GET':
        var = {
            'is_photo': False if user.image == '' else True,
            'nbar': 'states',
        }
        return render(request, 'state/add_state.html',var)
    elif request.method == 'POST':
        state_name = request.POST['state_name']
        
        if state.objects.filter(name=state_name).exists():
            messages.error(request, "State with name {} already registered.".format(state_name))
            return redirect(request.get_full_path())
        else:
            state_data = state.objects.create(name=state_name).save()
            messages.success(request, "State added successfully")
            return redirect('get-states')

@staff_member_required(login_url = '/error/')
def update_state(request):
    user = request.user
    if request.method == 'GET':
        id = request.GET['id']
        var = {
            'state_data':state.objects.get(id=id),
            'is_photo': False if user.image == '' else True,
            'nbar': 'states',
        }
        return render(request, 'state/update_state.html',var)
    elif request.method == 'POST':
        state_name = request.POST['state_name']
        id = request.POST['id']

        try:
            state_data = state.objects.get(id=id)
            state_data.name = state_name
            state_data.save()
            messages.success(request, "State with name {} updated successfully.".format(state_name))
            return redirect(request.get_full_path())
        except:
            messages.error(request, "Something wents wrong while updating state {}".format(state_name))
            return redirect(request.get_full_path())

@staff_member_required(login_url = '/error/')
def delete_state(request):
    user = request.user
    if request.method == 'GET':
        id = request.GET['id']
        sdata = state.objects.get(id=id)
        name = sdata.name
        try:
            sdata.delete()
            messages.success(request, "State with name {} deleted successfully".format(name))
            return redirect('get-states')
        except:
            messages.error(request, "Something wents wrong while deleting state {}.".format(name))
            return redirect('get-states')

#################### Settings Section ####################

def settings(request):
    if request.user.is_superuser:
        user = request.user
        if request.method == 'GET':

            tls_style, ssl_style, fs_style,edata = '', '', '', ''
            main_style = ''
            try:
                edata = email_configuration.objects.get(id=1)
                if edata.use_tls == True:
                    tls_style = "checked"
                if edata.use_ssl == True:
                    ssl_style = "checked"
                if edata.fail_silently == True:
                    fs_style = "checked"
            except:
                pass
            try:
                app_setting_data = app_settings.objects.get(id=1)
                if app_setting_data.is_under_maintenance == True:
                    main_style = "checked"
            except:
                app_setting_data = ''

            var = {
                'is_photo': False if user.image == '' else True,
                'nbar': 'setting',
                'edata':edata,
                'tls_style':tls_style,
                'ssl_style':ssl_style,
                'fs_style': fs_style,
                'app_setting_data': app_setting_data,
                'main_style': main_style,
            }
            return render(request, 'authentication/settings.html',var)
    else:
        return redirect('error')

def update_email_configuration(request):
    if request.user.is_superuser:
        user = request.user
        if request.method == 'POST':
            ehost = request.POST['ehost']
            eport = request.POST['eport']
            efrom = request.POST['efrom']
            eusername = request.POST['eusername']
            epassword = request.POST['epassword']
            use_tls = request.POST.get('tls',False)
            use_ssl = request.POST.get('ssl',False)
            fail_silently = request.POST.get('fail_silently',False)
            timeout = request.POST['etimeout'] if request.POST['etimeout'] != '' else 0.0

            print(ehost,eport,efrom,eusername,epassword,use_tls,use_ssl,fail_silently,timeout)

            try:
                edata = email_configuration.objects.get(id=1)
            except:
                if email_configuration.objects.all().count() < 1:
                    edata = email_configuration.objects.create(email_host=ehost,email_port=eport,email_from=efrom,email_username=eusername,
                            email_password=epassword,use_tls=use_tls,use_ssl=use_ssl,fail_silently=fail_silently,timeout=timeout)
                    edata.save()
                    messages.success(request, 'Email Configuration created successfully.')
                    return redirect('settings')
                else:
                    messages.error(request, 'Found Multiple Entry of Email Table in Database.')
                    return redirect('settings')

            edata.email_host = ehost
            edata.email_port = eport
            edata.email_from = efrom
            edata.email_username = eusername
            edata.email_password = epassword
            edata.use_tls = use_tls
            edata.use_ssl = use_ssl
            edata.fail_silently = fail_silently
            edata.timeout = timeout
            edata.save()
            messages.success(request, 'Email Configuration updated successfully.')
            return redirect('settings')
    else:
        return redirect('error')

def set_maintenance(request):
    if request.method == 'POST':
        maintenance = request.POST.get('is_live', False)

        if app_settings.objects.all().count() == 0:
            try:
                app_setting_data = app_settings.objects.create(is_under_maintenance=maintenance).save()
            except:
                messages.error(request, "Something wents wrong. {} {}".format(sys.exc_info()))
                return redirect('settings')
        elif app_settings.objects.all().count() == 1:
            try:
                app_setting_data = app_settings.objects.get(id=1)
                app_setting_data.is_under_maintenance=maintenance
                app_setting_data.save()
            except:
                messages.error(request, "Something wents wrong. {} {}".format(sys.exc_info()))
                return redirect('settings')
        else:
            pass
        # print(maintenance)
        if maintenance == 'True':
            messages.success(request, "Application is now in maintenance. (Only ADMINs can access the portal)")
        else:
            messages.success(request, "Application is now Live to users")
        return redirect('settings')

def logout_all_server_users(request):
    if request.method == 'GET':
        user_data = User.objects.filter(is_superuser=False)
        try:
            for i in user_data:
                session_key = i.session_key
                try:
                    session_data = Session.objects.get(session_key=session_key)
                    session_data.delete()
                    #print("Deleted Key")
                except:
                    pass
                i.session_key = ''
                i.save()
        except:
            messages.error(request, "Something wents wrong. {}".format(sys.exc_info()))
            return redirect('settings')
        messages.success(request, "Successfully logged out all users and staff members.")
        return redirect('settings')

def clear_storage(request):
    if request.method == 'POST':
        unnecessary = request.POST.get('unnecessary', '')

        to_date = datetime.today() - timedelta(days = 1 )
        if unnecessary == '3':
            from_date = datetime.today() - timedelta(days = 4)
        elif unnecessary == '7':
            from_date = datetime.today() - timedelta(days = 8)
        elif unnecessary == '14':
            from_date = datetime.today() - timedelta(days = 15)
        elif unnecessary == '21':
            from_date = datetime.today() - timedelta(days = 21)
        else:
            pass
        
        try:
            count = 0
            temp_data = document_unnecessary.objects.filter(created_at__range=[from_date,to_date])
            for temp in temp_data:
                path = temp.document_path
                try:
                    os.remove(path)
                    count +=1
                except:
                    pass
        except:
            messages.error(request,"Something wents wrong. {}".format(sys.exc_info()))
            return redirect('settings')

        messages.success(request, "Successfully cleaned {} unnecessary data from server".format(count))
        return redirect('settings')
        # print("From - ",from_date)
        # print("To - ",to_date)


#################### Application Section ##################

def get_random_password(first_name):
    # choose from [0-9], [A-Z], and [a-z]
    letters = string.ascii_uppercase + string.digits + string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(6))
    psw = '{}@{}'.format(first_name,result_str)
    return psw

#################### Limit Section ##################

@staff_member_required(login_url = '/error/')
def get_limit(request):
    if request.user.is_superuser:
        user = request.user
        if request.method == 'GET':
            limit_data = document_limit.objects.all()

            page = request.GET.get('page', 1)
            paginator = Paginator(limit_data,15)
            try:
                limitlist = paginator.page(page)
            except PageNotAnInteger:
                limitlist = paginator.page(1)
            except EmptyPage:
                limitlist = paginator.page(paginator.num_pages)

            var = {
                'limitlist': limitlist,
                'is_photo': False if user.image == '' else True,
                'nbar': 'limit',
            }
            return render(request, 'limit/get_limit.html',var)
    else:
        return redirect('error')

@staff_member_required(login_url = '/error/')
def update_limit(request):
    if request.user.is_superuser:
        user = request.user
        if request.method == 'GET':
            id = request.GET['id']
            var = {
                'limit_data': document_limit.objects.get(id=id),
                'is_photo': False if user.image == '' else True,
                'nbar': 'limit',
            }
            return render(request, 'limit/update_limit.html',var)
        elif request.method == 'POST':
            int_limit = request.POST['int_limit']
            id = request.POST['id']

            try:
                limit_data = document_limit.objects.get(id=id)
                limit_data.limit = int_limit
                limit_data.remaining_limit = int_limit
                limit_data.save()
                messages.success(request, "Daily limit updated for user {}".format(limit_data.distributer.email))
                return redirect(request.get_full_path())
            except:
                messages.error(request, "Something wents wrong while updating limit for user {}".format(limit_data.distributer.email))
                return redirect(request.get_full_path())
    else:
        return redirect('error')

@staff_member_required(login_url = '/error/')
def view_download_docs(request):
    if request.user.is_superuser:
        user = request.user
        id = request.GET['id']
        limit_data = document_limit.objects.get(id=id)
        dis_data = User.objects.get(id=limit_data.distributer_id)
        user_download_data = document_shared.objects.filter(distributer_id=limit_data.distributer_id,is_downloaded=False)

        page = request.GET.get('page', 1)
        paginator = Paginator(user_download_data,10)
        try:
            downloadlist = paginator.page(page)
        except PageNotAnInteger:
            downloadlist = paginator.page(1)
        except EmptyPage:
            downloadlist = paginator.page(paginator.num_pages)

        var = {
            'downloadlist': downloadlist,
            'name': dis_data.username,
            'is_photo': False if user.image == '' else True,
            'nbar': 'limit',
        }
        return render(request, 'limit/download_list.html',var)


import mysql.connector
from mysql.connector import Error
from .onetime_share import one_time_share
from .onetime_preview import one_time_preview

def do_connection():
    #try:
    connection = mysql.connector.connect(host='127.0.0.1',
                database='ayushman_dataentry',
                user='root',
                password='root')
    return connection

    #except Error as e:
        #print("Error while connecting to MySQL", e)
        # return "Error while connecting to MySQL {}".format(e)

def get_dataentry_doc(request):
    user = request.user
    if request.method == 'GET':
        # record = connect_mysql_database()
        connection = do_connection()
        if connection.is_connected():
            cursor = connection.cursor()
            mysql_select_query = """SELECT * from account_user_card"""
            cursor.execute(mysql_select_query)
            records = cursor.fetchall()

            # print(len(records))
            # print(records)

            # templist = []
            # for r in records:
            #     temp = list(r)
            #     templist.append(temp)
            # # print(templist)

            templist = []
            for r in records:
                temp = list(r)[0]
                templist.append(temp)
            #print(templist)
            
        record = templist
        page = request.GET.get('page', 1)
        paginator = Paginator(record,50)
        try:
            pdfList = paginator.page(page)
        except PageNotAnInteger:
            pdfList = paginator.page(1)
        except EmptyPage:
            pdfList = paginator.page(paginator.num_pages)
        var = {
            'pdfList': pdfList,
            'is_photo': False if user.image == '' else True,
            'nbar': 'dataentry',
        }
        return render(request, 'dataentry/dataentry.html',var)

def share_dataentry_doc_preview(request):
    if request.method == 'POST':
        result = request.POST
        # print("_-->",result)

        result = list(result)
        result = result[1:]
        length = len(result)
        print(result)

        preview_list = []
        id_list = []
        
        for i in result:
            # print(i)
            id = i.split("doc")[1]
            # print(id)
            connection = do_connection()
            if connection.is_connected():
                cursor = connection.cursor()

                sql_command = 'SELECT * FROM account_user_card WHERE id = {}'.format(id)

                cursor.execute(sql_command)
                records = cursor.fetchall()

            cardData = records[0]
            id_list.append(id)
            name = cardData[2]
            yob = cardData[3]
            gender = cardData[4]
            state = cardData[5]
            image = cardData[6]
            # is_text = cardData.is_text
            extra_text = cardData[7]
            # print("--{}--".format(extra_text))
            is_text = True if extra_text != None else False
            is_background = True
            serial_number = cardData[1]
            # print(serial_number,name,yob,gender,state,image,extra_text)
            # x = 1/0
            path = one_time_preview(name,yob,gender,state,image,is_background,is_text,extra_text,serial_number)
            # print('-->', path)

            preview_list.append(path)
        
        # print(preview_list)
        print(id_list)

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
        return render(request, 'share/share_multiple_document_dataentry.html',var)
