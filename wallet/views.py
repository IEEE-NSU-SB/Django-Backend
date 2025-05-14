from django.shortcuts import render

from port.models import Chapters_Society_and_Affinity_Groups, Panels
from wallet.renderData import WalletManager
from .models import Wallet, WalletEntry, WalletEntryCategory, WalletEntryFile
from django.db.models import Sum, Case, When, F, Value, DecimalField, Min, Max

# Create your views here.      

def entries(request, event_id=None):

    context = {
        'event_id': event_id,
    }

    return render(request, "entries.html", context)

def cash_in(request, event_id=None):

    if request.method == 'POST':
        entry_date_time = request.POST.get('entry_date_time')
        entry_amount = request.POST.get('entry_amount')
        name = request.POST.get('name')
        contact = request.POST.get('contact')
        entry_remark = request.POST.get('entry_remark')
        entry_categories = request.POST.get('entry_categories')
        payment_mode = request.POST.get('payment_mode')
        entry_files = request.FILES.getlist('entry_files')

        WalletManager.add_wallet_entry(1, 'CASH_IN', entry_date_time, entry_amount, name, contact, entry_remark, payment_mode, entry_categories, entry_files, event_id)
    
    wallet_balance = Wallet.objects.get(sc_ag=Chapters_Society_and_Affinity_Groups.objects.get(primary=1).pk).balance
    categories = WalletEntryCategory.objects.all()

    context = {
        'wallet_balance': wallet_balance,
        'categories': categories,
    }

    return render(request, "cash_in.html", context)

def cash_out(request, event_id=None):

    if request.method == 'POST':
        entry_date_time = request.POST.get('entry_date_time')
        entry_amount = request.POST.get('entry_amount')
        name = request.POST.get('name')
        contact = request.POST.get('contact')
        entry_remark = request.POST.get('entry_remark')
        entry_categories = request.POST.get('entry_categories')
        payment_mode = request.POST.get('payment_mode')
        entry_files = request.FILES.getlist('entry_files')

        WalletManager.add_wallet_entry(1, 'CASH_OUT', entry_date_time, entry_amount, name, contact, entry_remark, payment_mode, entry_categories, entry_files, event_id)
    
    wallet_balance = Wallet.objects.get(sc_ag=Chapters_Society_and_Affinity_Groups.objects.get(primary=1).pk).balance
    categories = WalletEntryCategory.objects.all()

    context = {
        'wallet_balance': wallet_balance,
        'categories': categories,
    }

    return render(request, "cash_out.html" , context)

def cash_edit(request):
    return render(request, "cash_edit.html")

def wallet_homepage(request):

    wallet_entries_event = (
        WalletEntry.objects
        .filter(entry_event__isnull=False)
        .values(
            'entry_event',
            'entry_event__event_name',
            #'status',
        )
        .annotate(
            total_amount=Sum(
                Case(
                    When(entry_type='CASH_IN', then=F('amount')),
                    When(entry_type='CASH_OUT', then=-F('amount')),
                    default=Value(0),
                    output_field=DecimalField()
                )
            ),
            creation_date_time=Min('creation_date_time'),
            last_update_date_time=Max('update_date_time'),
        )
    )

    context = {
        'wallet_entries_event':wallet_entries_event
    }

    return render(request, "wallet_homepage.html", context)