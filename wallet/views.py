from django.shortcuts import render

from port.models import Chapters_Society_and_Affinity_Groups
from .models import Wallet

# Create your views here.      

def wallet_homepage(request):
    return render(request, "wallet_page.html")

def add_cash(request):

    if request.method == 'POST':
        entry_date_time = request.POST.get('entry_date_time')
        entry_amount = request.POST.get('entry_amount')
        name = request.POST.get('name')
        contact = request.POST.get('contact')
        entry_remark = request.POST.get('entry_remark')
        entry_categories = request.POST.get('entry_categories')
    
    wallet_balance = Wallet.objects.get(sc_ag=Chapters_Society_and_Affinity_Groups.objects.get(primary=1).pk).balance

    context = {
        'wallet_balance': wallet_balance,
    }

    return render(request, "add_cash.html", context)