from django.shortcuts import render

# Create your views here.      

def wallet_homepage(request):
    return render(request, "wallet_page.html")

def add_cash(request):
    return render(request, "add_cash.html")

def cash_out(request):
    return render(request, "cash_out.html") 


def edit_cash(request):
    return render(request, "edit_cash.html") 