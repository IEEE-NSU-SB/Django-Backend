from collections import defaultdict
import json
import mimetypes
from django.http import JsonResponse
from django.utils.timezone import localtime
from django.shortcuts import redirect, render
from django.views import View

from central_events.models import Events
from finance_and_corporate_team.models import BudgetSheet
from insb_port import settings
from port.models import Chapters_Society_and_Affinity_Groups, Panels
from port.renderData import PortData
from users import renderData
from wallet.renderData import WalletManager
from .models import Wallet, WalletEntry, WalletEntryCategory, WalletEntryFile, WalletEventStatus
from users.renderData import LoggedinUser,member_login_permission
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Case, When, F, Value, DecimalField, Min, Max, Subquery, OuterRef

# Create your views here.      

@login_required
@member_login_permission
def entries(request, event_id):

    sc_ag=PortData.get_all_sc_ag(request=request)
    current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
    user_data=current_user.getUserData() #getting user data as dictionary file

    event_name = Events.objects.filter(id=event_id).values_list('event_name', flat=True).first()
    categories = WalletEntryCategory.objects.all()
    entries = WalletEntry.objects.filter(entry_event=event_id).order_by('entry_date_time')
    wallet_event_status, created = WalletEventStatus.objects.get_or_create(wallet_event_id=event_id)
    budget_data = BudgetSheet.objects.filter(event=event_id)
    if len(budget_data) > 0:
        budget_data = budget_data[0]
    else:
        budget_data = None

    total_entries = len(entries)

    wallet_entries = defaultdict(list)
    cash_in_total = 0
    cash_out_total = 0
    names = []

    for entry in entries:
        entry_date = localtime(entry.entry_date_time).date()
        file_count = WalletEntryFile.objects.filter(wallet_entry=entry).count()
        wallet_entries[entry_date].append([entry, file_count])

        if entry.entry_type == 'CASH_IN':
            cash_in_total += entry.amount
        elif entry.entry_type == 'CASH_OUT':
            cash_out_total += entry.amount

        if entry.name and entry.name != '':
            name = entry.name.replace(" ", "").lower()
            if name != '':
                names.append(name)

    net_balance = cash_in_total - cash_out_total
    budget_amount_available = None
    if budget_data:
        budget_amount_available = budget_data.total_cost - float(net_balance)

    wallet_entries = dict(wallet_entries)

    context = {
        'all_sc_ag':sc_ag,
        'user_data':user_data,
        'event_id': event_id,
        'event_name': event_name,
        'wallet_entries': wallet_entries,
        'total_entries': total_entries,
        'cash_in_total': cash_in_total,
        'cash_out_total': cash_out_total,
        'net_balance': net_balance,
        'categories': categories,
        'wallet_event_status': wallet_event_status,
        'names': names,
        'budget_data': budget_data,
        'budget_amount_available': budget_amount_available,
    }

    return render(request, "entries.html", context)

@login_required
@member_login_permission
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

        if event_id:
            return redirect('central_branch:wallet:entries_event', event_id)
        else:
            return redirect('central_branch:wallet:wallet_homepage')
    
    wallet_balance = Wallet.objects.get(sc_ag=Chapters_Society_and_Affinity_Groups.objects.filter(primary=1).values('id')[0]['id']).balance
    categories = WalletEntryCategory.objects.all()

    context = {
        'wallet_balance': wallet_balance,
        'categories': categories,
        'event_id': event_id,
    }

    return render(request, "cash_in.html", context)

@login_required
@member_login_permission
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

        if event_id:
            return redirect('central_branch:wallet:entries_event', event_id)
        else:
            return redirect('central_branch:wallet:wallet_homepage')
    
    wallet_balance = Wallet.objects.get(sc_ag=Chapters_Society_and_Affinity_Groups.objects.filter(primary=1).values('id')[0]['id']).balance
    categories = WalletEntryCategory.objects.all()

    context = {
        'wallet_balance': wallet_balance,
        'categories': categories,
        'event_id': event_id,
    }

    return render(request, "cash_out.html" , context)

@login_required
@member_login_permission
def cash_edit(request, entry_id):

    categories = WalletEntryCategory.objects.all()

    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        entry_date_time = request.POST.get('entry_date_time')
        # entry_amount = request.POST.get('entry_amount')
        name = request.POST.get('name')
        contact = request.POST.get('contact')
        entry_remark = request.POST.get('entry_remark')
        # entry_categories = request.POST.get('entry_categories')
        payment_mode = request.POST.get('payment_mode')
        # entry_files = request.FILES.getlist('entry_files')

        WalletManager.update_wallet_entry(entry_id, entry_date_time, None, name, contact, entry_remark, payment_mode, None, None)

        if event_id:
            return redirect('central_branch:wallet:entries_event', event_id)
        else:
            return redirect('central_branch:wallet:wallet_homepage')
        
    entry = WalletEntry.objects.get(id=entry_id)
    files = WalletEntryFile.objects.filter(wallet_entry=entry)

    for file in files:
        variable, _ = mimetypes.guess_type(file.document.name)
        variable = variable.split('/')
        file.mimetype = [variable[0], variable[1].upper()]

    context = {
        'entry': entry,
        'files': files,
        'media_url':settings.MEDIA_URL,
        'categories': categories,
    }

    return render(request, "cash_edit.html", context)

@login_required
@member_login_permission
def wallet_homepage(request):

    sc_ag=PortData.get_all_sc_ag(request=request)
    current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
    user_data=current_user.getUserData() #getting user data as dictionary file
    
    events = Events.objects.all().values('id', 'event_name')

    wallet_entries_event = None
    wallet_entries = None
    view = 'event_view'
    if request.GET.get('view') and request.GET.get('view') != '':
            view = request.GET.get('view')

    if view == 'event_view':
        wallet_entries_event = (
            WalletEntry.objects
            .filter(entry_event__isnull=False)
            .values(
                'entry_event',
                'entry_event__event_name',
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
                status = Subquery(WalletEventStatus.objects.filter(wallet_event=OuterRef('entry_event')).values('status'))
            )
        )
    elif view == 'non_event_view':
        wallet_entries = (WalletEntry.objects
                .filter(entry_event__isnull=True)
                .values('id', 'creation_date_time', 'update_date_time', 'entry_type', 'amount', 'remarks')
        )

    context = {
        'all_sc_ag':sc_ag,
        'user_data':user_data,
        'events': events,
        'wallet_entries_event':wallet_entries_event,
        'wallet_entries': wallet_entries,
        'view': view,
    }

    return render(request, "wallet_homepage.html", context)

class WalletEventStatusUpdateAjax(View):
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            event_id = data['event_id']
            checked = data['completed']

            wallet_event_status, created = WalletEventStatus.objects.get_or_create(wallet_event_id=event_id)
            if checked == True:
                wallet_event_status.status = 'COMPLETED'
            else:
                wallet_event_status.status = 'ONGOING'
            
            wallet_event_status.save()

            return JsonResponse({'message':'success'})
        except:
            return JsonResponse({'message':'error'})