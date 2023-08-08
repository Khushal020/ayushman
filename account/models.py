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

def save_user_image(instance, filename):
    return 'card_user_photo/{}.png'.format(instance.serial_number)

class card_data(models.Model):
    serial_number = models.CharField(max_length=255)
    name = models.CharField(max_length=50,blank=True,null=True)
    yob = models.CharField(max_length=10,blank=True,null=True)
    gender = models.CharField(max_length=10,blank=True,null=True)
    state = models.CharField(max_length=30,blank=True,null=True)
    image = models.ImageField(upload_to=save_user_image,blank=True,null=True)
    is_text = models.BooleanField(default=False)
    extra_text = models.CharField(max_length=100,blank=True,null=True)
    is_background = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.serial_number

class document_shared(models.Model):
    distributer = models.ForeignKey(User, on_delete=models.CASCADE)
    document_type = models.CharField(max_length=10,default="OLD")
    document = models.ForeignKey(card_data, on_delete=models.CASCADE, blank=True,null=True)
    is_downloaded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class document_shared_temp(models.Model):
    distributer = models.ForeignKey(User, on_delete=models.CASCADE)
    document_type = models.CharField(max_length=10,default="OLD")
    document_path = models.CharField(max_length=255,blank=True,null=True)
    # document = models.ForeignKey(card_data, on_delete=models.CASCADE, blank=True,null=True)
    is_downloaded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class document_unnecessary(models.Model):
    document_path = models.CharField(max_length=255,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)

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

class app_settings(models.Model):
    is_under_maintenance = models.BooleanField(default=False)

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