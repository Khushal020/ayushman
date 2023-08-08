from .models import *
from django.shortcuts import render, redirect

from rest_framework import status


class UserCheckerMiddleware:
    def __init__(self, get_response):
        # print("Called __init___")
        self.get_response = get_response

    
    def __call__(self, request):
        response = self.get_response(request)
		
        # return render(request, 'error/500_maintenance.html')
        # print("-->",request.get_full_path())

        if request.user.is_authenticated:
            pass
        elif request.get_full_path() == '/password/forgot/':
            pass
        elif request.get_full_path() == '/123':
            pass
        elif request.get_full_path() == '/mainfun':
            pass
        elif request.get_full_path() == '/logout_11/':
            pass
        elif request.get_full_path() == '/clear-session':
            pass
        else:
            # pass
            # print("---->",request.get_full_path())
            return render(request, 'authentication/login.html')
        
        return response

