from collections import defaultdict
import json
import mimetypes
from django.http import JsonResponse
from django.utils.timezone import localtime
from django.shortcuts import redirect, render
from django.views import View

from central_branch.renderData import Branch
from central_events.models import Events
from chapters_and_affinity_group.get_sc_ag_info import SC_AG_Info
from finance_and_corporate_team.models import BudgetSheet
from insb_port import settings
from port.models import Chapters_Society_and_Affinity_Groups, Panels
from port.renderData import PortData
from users import renderData
from wallet.renderData import WalletManager
from .models import Wallet, WalletEntry, WalletEntryCategory, WalletEntryFile, WalletEventStatus
from users.renderData import LoggedinUser,member_login_permission
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Case, When, F, Value, DecimalField, Min, Max, Subquery, OuterRef, IntegerField
from django.db.models.functions import TruncDate

# Create your views here.      

@login_required
@member_login_permission
def entries(request, event_id, primary=None):

    sc_ag=PortData.get_all_sc_ag(request=request)
    current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
    user_data=current_user.getUserData() #getting user data as dictionary file
    get_sc_ag_info=None

    if WalletManager.has_access(request, primary, event_id=event_id):

        if primary == None:
            primary = 1
        else:
            get_sc_ag_info=SC_AG_Info.get_sc_ag_details(request,primary)

        event_name = Events.objects.filter(id=event_id).order_by('-start_date','-event_date').values_list('event_name', flat=True).first()
        categories = WalletEntryCategory.objects.all()
        entries = WalletEntry.objects.filter(entry_event=event_id).order_by('entry_date_time')
        wallet_event_status, created = WalletEventStatus.objects.get_or_create(wallet_event_id=event_id)
        wallet_balance = Wallet.objects.get(sc_ag=Chapters_Society_and_Affinity_Groups.objects.filter(primary=primary).values('id')[0]['id']).balance
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
        budget_surplus_deficit = None
        if budget_data:
            budget_surplus_deficit = budget_data.total_revenue - budget_data.total_cost

        wallet_entries = dict(wallet_entries)

        context = {
            'all_sc_ag':sc_ag,
            'sc_ag_info':get_sc_ag_info,
            'user_data':user_data,
            'primary': primary,
            'event_id': event_id,
            'event_name': event_name,
            'wallet_entries': wallet_entries,
            'wallet_balance': wallet_balance,
            'total_entries': total_entries,
            'cash_in_total': cash_in_total,
            'cash_out_total': cash_out_total,
            'net_balance': net_balance,
            'categories': categories,
            'wallet_event_status': wallet_event_status,
            'names': names,
            'budget_data': budget_data,
            'budget_surplus_deficit': budget_surplus_deficit,
        }

        return render(request, "entries.html", context)
    else:
        return render(request,'access_denied.html', {'all_sc_ag':sc_ag,'user_data':user_data,'sc_ag_info':get_sc_ag_info})

@login_required
@member_login_permission
def cash_in(request, event_id=None, primary=None):

    sc_ag=PortData.get_all_sc_ag(request=request)
    current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
    user_data=current_user.getUserData() #getting user data as dictionary file
    get_sc_ag_info=None

    if WalletManager.has_access(request, primary, event_id=event_id):
        if primary == None:
            primary = 1
        else:
            get_sc_ag_info=SC_AG_Info.get_sc_ag_details(request,primary)

        if request.method == 'POST':
            entry_date_time = request.POST.get('entry_date_time')
            entry_amount = request.POST.get('entry_amount')
            name = request.POST.get('name')
            contact = request.POST.get('contact')
            entry_remark = request.POST.get('entry_remark')
            entry_categories = request.POST.get('entry_categories')
            payment_mode = request.POST.get('payment_mode')
            entry_files = request.FILES.getlist('entry_files')

            WalletManager.add_wallet_entry(primary, 'CASH_IN', entry_date_time, entry_amount, name, contact, entry_remark, payment_mode, entry_categories, entry_files, event_id)

            if event_id:
                if primary == 1:
                    return redirect('central_branch:wallet:entries_event', event_id)
                else:
                    return redirect('chapters_and_affinity_group:wallet:entries_event', primary, event_id)
            else:
                if primary == 1:
                    return redirect('central_branch:wallet:wallet_homepage')
                else:
                    return redirect('chapters_and_affinity_group:wallet:wallet_homepage', primary)
        
        wallet_balance = Wallet.objects.get(sc_ag=Chapters_Society_and_Affinity_Groups.objects.filter(primary=primary).values('id')[0]['id']).balance
        categories = WalletEntryCategory.objects.all()

        context = {
            'all_sc_ag':sc_ag,
            'sc_ag_info':get_sc_ag_info,
            'user_data':user_data,
            'primary': primary,
            'wallet_balance': wallet_balance,
            'categories': categories,
            'event_id': event_id,
        }

        return render(request, "cash_in.html", context)
    else:
        return render(request,'access_denied.html', {'all_sc_ag':sc_ag,'user_data':user_data,'sc_ag_info':get_sc_ag_info})

@login_required
@member_login_permission
def cash_out(request, event_id=None, primary=None):

    sc_ag=PortData.get_all_sc_ag(request=request)
    current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
    user_data=current_user.getUserData() #getting user data as dictionary file
    get_sc_ag_info=None

    if WalletManager.has_access(request, primary, event_id=event_id):
        if primary == None:
            primary = 1
        else:
            get_sc_ag_info=SC_AG_Info.get_sc_ag_details(request,primary)

        if request.method == 'POST':
            entry_date_time = request.POST.get('entry_date_time')
            entry_amount = request.POST.get('entry_amount')
            name = request.POST.get('name')
            contact = request.POST.get('contact')
            entry_remark = request.POST.get('entry_remark')
            entry_categories = request.POST.get('entry_categories')
            payment_mode = request.POST.get('payment_mode')
            entry_files = request.FILES.getlist('entry_files')

            WalletManager.add_wallet_entry(primary, 'CASH_OUT', entry_date_time, entry_amount, name, contact, entry_remark, payment_mode, entry_categories, entry_files, event_id)

            if event_id:
                if primary == 1:
                    return redirect('central_branch:wallet:entries_event', event_id)
                else:
                    return redirect('chapters_and_affinity_group:wallet:entries_event', primary, event_id)
            else:
                if primary == 1:
                    return redirect('central_branch:wallet:wallet_homepage')
                else:
                    return redirect('chapters_and_affinity_group:wallet:wallet_homepage', primary)
        
        wallet_balance = Wallet.objects.get(sc_ag=Chapters_Society_and_Affinity_Groups.objects.filter(primary=primary).values('id')[0]['id']).balance
        categories = WalletEntryCategory.objects.all()

        context = {
            'all_sc_ag':sc_ag,
            'sc_ag_info':get_sc_ag_info,
            'user_data':user_data,
            'primary': primary,
            'wallet_balance': wallet_balance,
            'categories': categories,
            'event_id': event_id,
        }

        return render(request, "cash_out.html" , context)
    else:
        return render(request,'access_denied.html', {'all_sc_ag':sc_ag,'user_data':user_data,'sc_ag_info':get_sc_ag_info})

@login_required
@member_login_permission
def cash_edit(request, entry_id, primary=None):

    sc_ag=PortData.get_all_sc_ag(request=request)
    current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
    user_data=current_user.getUserData() #getting user data as dictionary file
    get_sc_ag_info=None

    if WalletManager.has_access(request, primary, entry_id=entry_id):
        if primary == None:
            primary = 1
        else:
            get_sc_ag_info=SC_AG_Info.get_sc_ag_details(request,primary)

        categories = WalletEntryCategory.objects.all()

        if request.method == 'POST':
            event_id = request.POST.get('event_id')

            if 'update_entry' in request.POST:
                entry_date_time = request.POST.get('entry_date_time')
                entry_amount = request.POST.get('entry_amount')
                name = request.POST.get('name')
                contact = request.POST.get('contact')
                entry_remark = request.POST.get('entry_remark')
                entry_categories = request.POST.get('entry_categories')
                payment_mode = request.POST.get('payment_mode')
                entry_files = request.FILES.getlist('entry_files')

                WalletManager.update_wallet_entry(entry_id, entry_date_time, entry_amount, name, contact, entry_remark, payment_mode, entry_categories, entry_files)

            elif 'delete_entry' in request.POST:
                WalletManager.delete_wallet_entry(entry_id)

            elif 'delete_file' in request.POST:
                file_id = request.POST.get('delete_file')

                WalletManager.delete_entry_file(file_id)

                if primary == 1:
                    return redirect('central_branch:wallet:cash_edit', entry_id)
                else:
                    return redirect('chapters_and_affinity_group:wallet:cash_edit', primary, entry_id)

            if event_id:
                if primary == 1:
                    return redirect('central_branch:wallet:entries_event', event_id)
                else:
                    return redirect('chapters_and_affinity_group:wallet:entries_event', primary, event_id)
            else:
                if primary == 1:
                    return redirect('central_branch:wallet:wallet_homepage')
                else:
                    return redirect('chapters_and_affinity_group:wallet:wallet_homepage', primary)

            
        entry = WalletEntry.objects.get(id=entry_id)
        files = WalletEntryFile.objects.filter(wallet_entry=entry)

        for file in files:
            variable, _ = mimetypes.guess_type(file.document.name)
            variable = variable.split('/')
            file.mimetype = [variable[0], variable[1].upper()]

        context = {
            'all_sc_ag':sc_ag,
            'sc_ag_info':get_sc_ag_info,
            'user_data':user_data,
            'primary': primary,
            'entry': entry,
            'files': files,
            'media_url':settings.MEDIA_URL,
            'categories': categories,
        }

        return render(request, "cash_edit.html", context)
    else:
        return render(request,'access_denied.html', {'all_sc_ag':sc_ag,'user_data':user_data,'sc_ag_info':get_sc_ag_info})

@login_required
@member_login_permission
def wallet_homepage(request, primary=None):

    sc_ag=PortData.get_all_sc_ag(request=request)
    current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
    user_data=current_user.getUserData() #getting user data as dictionary file
    get_sc_ag_info=None

    if WalletManager.has_access(request, primary):
        if primary == None:
            primary = 1
        else:
            get_sc_ag_info=SC_AG_Info.get_sc_ag_details(request,primary)

        if request.method == 'POST':
            if 'delete_entry' in request.POST:
                entry_id = request.POST.get('delete_entry')

                WalletManager.delete_wallet_entry(entry_id)
        
        events = Events.objects.filter(event_organiser__primary=primary).order_by('-start_date','-event_date').values('id', 'event_name')
        tenures = Panels.objects.filter(panel_of__primary=primary).order_by('-year')

        wallet_entries_event = None
        wallet_entries = None
        filter_queries = {}
        filters = {}
        order_by = []

        view = 'event_view'

        if request.GET.get('view') and request.GET.get('view') != '':
            view = request.GET.get('view')

        if view == 'event_view':
            if request.GET.get('tenure') and request.GET.get('tenure') != '':
                filter_tenure = Panels.objects.get(panel_of__primary=primary, year=request.GET.get('tenure'))
                filter_queries.update({'tenure': request.GET.get('tenure')})
            else:
                filter_tenure = Panels.objects.get(panel_of__primary=primary, current=True)

            if request.GET.get('month') and request.GET.get('month') != '':
                filters.update({'entry_date_time__month': request.GET.get('month')})
                filter_queries.update({'month': request.GET.get('month')})

            last_updated = None
            if request.GET.get('last_updated') and request.GET.get('last_updated') != '':
                last_updated = request.GET.get('last_updated')
                if last_updated == 'latest':
                    order_by.append('-update_date')
                elif last_updated == 'oldest':
                    order_by.append('update_date')
                filter_queries.update({'last_updated': last_updated})

            if request.GET.get('net_balance') and request.GET.get('net_balance') != '':
                net_balance = request.GET.get('net_balance')
                if net_balance == 'htol':
                    order_by.append('-total_amount')
                elif net_balance == 'ltoh':
                    order_by.append('total_amount')               
                filter_queries.update({'net_balance': net_balance})

            status_filter = None
            if request.GET.get('status') and request.GET.get('status') != '':
                status_filter = request.GET.get('status').upper()
                filter_queries.update({'status': status_filter})

            status_subquery = WalletEventStatus.objects.filter(
                wallet_event=OuterRef('entry_event')
            ).values('status')[:1]

            # Base queryset
            queryset = WalletEntry.objects.filter(
                entry_event__isnull=False,
                sc_ag__primary=primary,
                tenure=filter_tenure,
                **filters
            )

            if status_filter:
                queryset = queryset.filter(
                    entry_event__in=WalletEventStatus.objects.filter(
                        status=status_filter
                    ).values('wallet_event')
                )

            wallet_entries_event = (
                queryset
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
                    update_date = TruncDate('last_update_date_time'),
                    status=Subquery(status_subquery),
                )
                .order_by(*order_by)
            )
        elif view == 'non_event_view':

            if request.GET.get('tenure') and request.GET.get('tenure') != '':
                filter_tenure = Panels.objects.get(panel_of__primary=primary, year=request.GET.get('tenure'))
                filter_queries.update({'tenure': request.GET.get('tenure')})
            else:
                filter_tenure = Panels.objects.get(panel_of__primary=primary, current=True)

            if request.GET.get('month') and request.GET.get('month') != '':
                filters.update({'entry_date_time__month': request.GET.get('month')})
                filter_queries.update({'month': request.GET.get('month')})

            if request.GET.get('last_updated') and request.GET.get('last_updated') != '':
                last_updated = request.GET.get('last_updated')
                if last_updated == 'latest':
                    order_by.append('-update_date')
                elif last_updated == 'oldest':
                    order_by.append('update_date')
                filter_queries.update({'last_updated': last_updated})

            net_balance = None
            if request.GET.get('net_balance') and request.GET.get('net_balance') != '':
                net_balance = request.GET.get('net_balance')
                filter_queries.update({'net_balance': net_balance})

            # Base queryset
            wallet_entries_queryset = WalletEntry.objects.filter(
                entry_event__isnull=True,
                sc_ag__primary=primary,
                **filters
            )

            # Initialize annotation
            annotations = {}

            if net_balance:
                annotations['priority'] = Case(
                    When(entry_type='CASH_IN', then=Value(0)),
                    When(entry_type='CASH_OUT', then=Value(1)),
                    default=Value(2),
                    output_field=IntegerField()
                )
                annotations['update_date'] = TruncDate('update_date_time')

            ordering = []
            if net_balance == 'ltoh':
                ordering = ['-priority', 'amount']
            elif net_balance == 'htol':
                ordering = ['priority', '-amount']

            # Apply annotations and final query
            wallet_entries = (
                wallet_entries_queryset
                .annotate(**annotations)
                .order_by(*order_by, *ordering)
                .values('id', 'creation_date_time', 'update_date_time', 'entry_type', 'amount', 'remarks')
            )
        
        wallet_balance = Wallet.objects.get(sc_ag=Chapters_Society_and_Affinity_Groups.objects.filter(primary=primary).values('id')[0]['id']).balance

        context = {
            'all_sc_ag':sc_ag,
            'sc_ag_info':get_sc_ag_info,
            'user_data':user_data,
            'primary': primary,
            'events': events,
            'wallet_balance': wallet_balance,
            'wallet_entries_event': wallet_entries_event,
            'wallet_entries': wallet_entries,
            'view': view,
            'tenures': tenures,
            'filter_queries': filter_queries,
        }

        return render(request, "wallet_homepage.html", context)
    else:
        return render(request,'access_denied.html', {'all_sc_ag':sc_ag,'user_data':user_data,'sc_ag_info':get_sc_ag_info})

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