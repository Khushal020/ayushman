# Generated by Django 3.0.8 on 2021-05-23 16:31

import account.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0013_auto_20210519_1525'),
    ]

    operations = [
        migrations.CreateModel(
            name='card_data',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('serial_number', models.CharField(max_length=12)),
                ('name', models.CharField(blank=True, max_length=50, null=True)),
                ('yob', models.CharField(blank=True, max_length=10, null=True)),
                ('gender', models.CharField(blank=True, max_length=10, null=True)),
                ('state', models.CharField(blank=True, max_length=30, null=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to=account.models.save_user_image)),
                ('is_text', models.BooleanField(default=False)),
                ('extra_text', models.CharField(blank=True, max_length=100, null=True)),
                ('is_background', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.DeleteModel(
            name='user_card',
        ),
        migrations.RemoveField(
            model_name='document_shared',
            name='document_number',
        ),
        migrations.RemoveField(
            model_name='document_shared',
            name='document_path',
        ),
        migrations.AddField(
            model_name='document_shared',
            name='document',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='account.card_data'),
        ),
    ]
