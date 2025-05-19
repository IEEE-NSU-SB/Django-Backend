from collections import defaultdict
from django.utils.timezone import localtime
from django.shortcuts import render

from central_events.models import Events
from port.models import Chapters_Society_and_Affinity_Groups, Panels
from wallet.renderData import WalletManager
from .models import Wallet, WalletEntry, WalletEntryCategory, WalletEntryFile
from django.db.models import Sum, Case, When, F, Value, DecimalField, Min, Max

# Create your views here.      

def entries(request, event_id=None):

    event_name = Events.objects.filter(id=event_id).values_list('event_name', flat=True).first()
    categories = WalletEntryCategory.objects.all()
    entries = WalletEntry.objects.filter(entry_event=event_id).order_by('entry_date_time')

    total_entries = len(entries)

    wallet_entries = defaultdict(list)
    cash_in_total = 0
    cash_out_total = 0

    for entry in entries:
        entry_date = localtime(entry.entry_date_time).date()
        file_count = WalletEntryFile.objects.filter(wallet_entry=entry).count()
        wallet_entries[entry_date].append([entry, file_count])
        if entry.entry_type == 'CASH_IN':
            cash_in_total += entry.amount
        elif entry.entry_type == 'CASH_OUT':
            cash_out_total += entry.amount

    net_balance = cash_in_total - cash_out_total

    wallet_entries = dict(wallet_entries)

    context = {
        'event_id': event_id,
        'event_name': event_name,
        'wallet_entries': wallet_entries,
        'total_entries': total_entries,
        'cash_in_total': cash_in_total,
        'cash_out_total': cash_out_total,
        'net_balance': net_balance,
        'categories': categories,
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

def cash_edit(request, entry_id):
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