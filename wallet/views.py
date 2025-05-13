from django.shortcuts import render

from port.models import Chapters_Society_and_Affinity_Groups, Panels
from .models import Wallet, WalletEntry, WalletEntryFile

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
        # entry_categories = request.POST.get('entry_categories')
        entry_files = request.FILES.getlist('entry_files')

        sc_ag = Chapters_Society_and_Affinity_Groups.objects.get(primary=1)

        wallet_entry = WalletEntry.objects.create(entry_date_time=entry_date_time,
                                   amount=entry_amount,
                                   name=name,
                                   contact=contact,
                                   remarks=entry_remark,
                                   sc_ag=sc_ag,
                                   tenure=Panels.objects.get(panel_of=sc_ag, current=True))
        
        for file in entry_files:
            WalletEntryFile.objects.create(wallet_entry=wallet_entry, document=file)
    
    wallet_balance = Wallet.objects.get(sc_ag=Chapters_Society_and_Affinity_Groups.objects.get(primary=1).pk).balance

    context = {
        'wallet_balance': wallet_balance,
    }

    return render(request, "add_cash.html", context)