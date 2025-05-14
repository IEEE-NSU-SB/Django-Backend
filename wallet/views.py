from django.shortcuts import render

from port.models import Chapters_Society_and_Affinity_Groups, Panels
from wallet.renderData import WalletManager
from .models import Wallet, WalletEntry, WalletEntryCategory, WalletEntryFile

# Create your views here.      

def entries(request):
    return render(request, "entries.html")

def cash_in(request):

    if request.method == 'POST':
        entry_date_time = request.POST.get('entry_date_time')
        entry_amount = request.POST.get('entry_amount')
        name = request.POST.get('name')
        contact = request.POST.get('contact')
        entry_remark = request.POST.get('entry_remark')
        entry_categories = request.POST.get('entry_categories')
        payment_mode = request.POST.get('payment_mode')
        entry_files = request.FILES.getlist('entry_files')

        WalletManager.add_wallet_entry(1, entry_date_time, entry_amount, name, contact, entry_remark, payment_mode, entry_categories, entry_files)
    
    wallet_balance = Wallet.objects.get(sc_ag=Chapters_Society_and_Affinity_Groups.objects.get(primary=1).pk).balance
    categories = WalletEntryCategory.objects.all()

    context = {
        'wallet_balance': wallet_balance,
        'categories': categories,
    }

    return render(request, "cash_in.html", context)

def cash_out(request):
    return render(request, "cash_out.html")

def wallet_homepage(request):
    return render(request, "wallet_homepage.html")