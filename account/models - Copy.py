from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# Overriding the Default Django Auth User and adding One More Field
class User(AbstractUser):
    phone = models.CharField(max_length=15,blank=True,null=True)
    gender = models.CharField(max_length=10,blank=True,null=True)
    image = models.ImageField(upload_to='user_profile',blank=True,null=True)
    created_by = models.CharField(max_length=255,blank=True,null=True)
    session_key = models.CharField(max_length=255,blank=True,null=True)

    def __str__(self):
        return self.email

def save_user_barcode(instance, filename):
    return 'user_barcode/{}.png'.format(instance.unique_id)

def save_user_qrcode(instance, filename):
    return 'user_qrcode/{}.png'.format(instance.unique_id)

class user_card(models.Model):
    unique_id = models.CharField(max_length=10)
    name = models.CharField(max_length=50,blank=True,null=True)
    yob = models.CharField(max_length=10,blank=True,null=True)
    gender = models.CharField(max_length=10,blank=True,null=True)
    state = models.CharField(max_length=30,blank=True,null=True)
    # barcode = models.ImageField(upload_to=save_user_barcode,blank=True,null=True)
    # qrcode = models.ImageField(upload_to=save_user_qrcode,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return unique_id

class document_shared(models.Model):
    distributer = models.ForeignKey(User, on_delete=models.CASCADE)
    document_type = models.CharField(max_length=10,default="OLD")
    document_number = models.CharField(max_length=10,blank=True,null=True)
    # document_number = models.IntegerField(default=1)
    document_path = models.CharField(max_length=255,blank=True,null=True)
    is_downloaded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class email_configuration(models.Model):
    email_host = models.CharField(max_length=256,blank=True,null=True)
    email_port = models.IntegerField(blank=True,null=True)
    email_from = models.CharField(max_length=256,blank=True,null=True)
    email_username = models.CharField(max_length=256,blank=True,null=True)
    email_password = models.CharField(max_length=256,blank=True,null=True)
    use_tls = models.BooleanField(blank=True,null=True)
    use_ssl = models.BooleanField(blank=True,null=True)
    fail_silently = models.BooleanField(blank=True,null=True)
    timeout = models.FloatField(blank=True,null=True)

    def __str__(self):
        return self.email_username

class state(models.Model):
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class document_limit(models.Model):
    distributer = models.ForeignKey(User, on_delete=models.CASCADE)
    limit = models.IntegerField(default=20)
    remaining_limit = models.IntegerField(default=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.distributer.username

@receiver(post_save, sender=User)
def create_user_limit(sender, instance, created, **kwargs):
    if created and not instance.is_superuser:
        # print(type(instance))
        document_limit.objects.create(distributer=instance)

# @receiver(post_save, sender=User)
# def save_user_limit(sender, instance, **kwargs):
#     instance.document_limit.save()