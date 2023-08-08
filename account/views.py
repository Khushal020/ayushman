from django.shortcuts import render

# Create your views here.
def handler404(request, exception):
    return render(request, 'error/404.html')

def handler403(request, exception):
    return render(request, 'error/403.html')

def handler500(request):
    return render(request, 'error/500.html')

def error(request):
    return render(request, 'error/403.html')