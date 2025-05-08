from django.shortcuts import render

# Create your views here.      

def wallet_homepage(request):
    return render(request, "wallet_page.html")

def add_cash(request):
    return render(request, "add_cash.html")