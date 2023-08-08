# Email Configuration modules
from django.core.mail import EmailMessage, EmailMultiAlternatives, get_connection, send_mail
from django.core.mail.backends.smtp import EmailBackend

from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.conf import settings

from .models import *

def user_password_reset(email,psw,username):
    print("Enter in Password Reset Fun")
    user_data = User.objects.get(email=email)
    user_data.set_password(psw)
    user_data.save()
    var = {
        'password':psw,
        'username': user_data.username,
    }

    sub = "Password Reset Successfully"
    to = [email]

    edata = email_configuration.objects.get(id=1)
    print("Before backend configure")
    print(edata.email_host,edata.email_port,edata.email_username,edata.email_password,edata.use_tls,edata.use_ssl,edata.fail_silently)
    backend = EmailBackend(host=edata.email_host,port=edata.email_port,username=edata.email_username,password=edata.email_password,
                    use_tls=edata.use_tls,use_ssl=edata.use_ssl,fail_silently=edata.fail_silently)

    html_body = render_to_string('email/password_reset.html',{'var':var})
    text_body = strip_tags(html_body)
    
    #print("Before static mail")	
    #subject = sub
    #message = text_body
    #email_from = settings.EMAIL_HOST_USER
    #recipient_list = to
    #send_mail( subject, message, email_from, recipient_list )
    print("Before email config")
    email = EmailMultiAlternatives(
        sub,
        text_body,
        edata.email_username,
        to,
        connection=backend
    )
    email.attach_alternative(html_body,"text/html")
    # email.attach_file('Document.pdf')
    print("Before send email")
    email.send()
    return True

def user_password_informer(email,psw,username):
    var = {
        'password':psw,
        'username': username,
        'email': email,
    }

    sub = "Your Login Credential"
    to = [email]

    # print("111111111111111")

    edata = email_configuration.objects.get(id=1)

    backend = EmailBackend(host=edata.email_host,port=edata.email_port,username=edata.email_username,password=edata.email_password,
                    use_tls=edata.use_tls,use_ssl=edata.use_ssl,fail_silently=edata.fail_silently)

    # print("22222222222222222222222")

    html_body = render_to_string('email/password.html',{'var':var})
    text_body = strip_tags(html_body)

    # print("3333")

    email = EmailMultiAlternatives(
        sub,
        text_body,
        edata.email_username,
        to,
        connection=backend
    )
    email.attach_alternative(html_body,"text/html")
    # email.attach_file('Document.pdf')
    # print("4444")
    email.send()
    return True