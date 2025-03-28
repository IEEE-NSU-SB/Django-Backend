from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from central_events.models import Events
from finance_and_corporate_team.models import BudgetSheet
from system_administration.render_access import Access_Render
from users.models import Members
from central_branch.renderData import Branch
from port.models import Chapters_Society_and_Affinity_Groups, Roles_and_Position
from django.contrib import messages
from .renderData import FinanceAndCorporateTeam
from system_administration.models import FCT_Data_Access
from port.renderData import PortData
from users import renderData
from users.renderData import PanelMembersData,member_login_permission
import traceback
from datetime import datetime
import logging
from system_administration.system_error_handling import ErrorHandling
from central_branch import views as cv
from .genPDF import BudgetPDF

logger=logging.getLogger(__name__)
# Create your views here.
@login_required
@member_login_permission
def team_homepage(request):

    try:

        sc_ag=PortData.get_all_sc_ag(request=request)
        current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
        user_data=current_user.getUserData() #getting user data as dictionary file
        
        # get team members
        get_members=FinanceAndCorporateTeam.load_team_members_with_positions()
        
        context={
                'user_data':user_data,
                'all_sc_ag':sc_ag,
                'co_ordinators':get_members[0],
                'incharges':get_members[1],
                'core_volunteers':get_members[2],
                'team_volunteers':get_members[3],
            }
        return render(request,"finance_and_corporate_team/team_homepage.html",context=context)
    
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return cv.custom_500(request)

@login_required
@member_login_permission
def manage_team(request):

    try:

        sc_ag=PortData.get_all_sc_ag(request=request)
        current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
        user_data=current_user.getUserData() #getting user data as dictionary file
        '''This function loads the manage team page for finance and corporate team and is accessable
        by the co-ordinatior only, unless the co-ordinators gives access to others as well'''
        user = request.user
        has_access=(Access_Render.team_co_ordinator_access(team_id=FinanceAndCorporateTeam.get_team_id(),username=user.username) or Access_Render.system_administrator_superuser_access(user.username) or Access_Render.system_administrator_staffuser_access(user.username) or Access_Render.eb_access(user.username)
        or FinanceAndCorporateTeam.fct_manage_team_access(user.username))

        if has_access:
            data_access = FinanceAndCorporateTeam.load_manage_team_access()
            team_members = FinanceAndCorporateTeam.load_team_members()
            #load all position for insb members
            position=PortData.get_all_volunteer_position_with_sc_ag_id(request=request,sc_ag_primary=1)
            #load all insb members
            all_insb_members=Members.objects.all()

            if request.method == "POST":
                if (request.POST.get('add_member_to_team')):
                    #get selected members
                    members_to_add=request.POST.getlist('member_select1')
                    #get position
                    position=request.POST.get('position')
                    for member in members_to_add:
                        FinanceAndCorporateTeam.add_member_to_team(member,position)
                    messages.success(request,"Added new Member to Team!")
                    return redirect('finance_and_corporate_team:manage_team')
                
                if (request.POST.get('remove_member')):
                    '''To remove member from team table'''
                    try:
                        load_current_panel=Branch.load_current_panel()
                        PanelMembersData.remove_member_from_panel(ieee_id=request.POST['remove_ieee_id'],panel_id=load_current_panel.pk,request=request)
                        try:
                            FCT_Data_Access.objects.filter(ieee_id=request.POST['remove_ieee_id']).delete()
                        except FCT_Data_Access.DoesNotExist:
                            return redirect('finance_and_corporate_team:manage_team')
                        return redirect('finance_and_corporate_team:manage_team')
                    except:
                        pass

                if request.POST.get('access_update'):
                    manage_team_access = False
                    if(request.POST.get('manage_team_access')):
                        manage_team_access=True
                    ieee_id=request.POST['access_ieee_id']
                    if (FinanceAndCorporateTeam.fct_manage_team_access_modifications(manage_team_access,ieee_id)):
                        permission_updated_for=Members.objects.get(ieee_id=ieee_id)
                        messages.info(request,f"Permission Details Was Updated for {permission_updated_for.name}")
                    else:
                        messages.info(request,f"Something Went Wrong! Please Contact System Administrator about this issue")

                if request.POST.get('access_remove'):
                    '''To remove record from data access table'''
                    
                    ieeeId=request.POST['access_ieee_id']
                    if(FinanceAndCorporateTeam.remove_member_from_manage_team_access(ieee_id=ieeeId)):
                        messages.info(request,"Removed member from Managing Team")
                        return redirect('finance_and_corporate_team:manage_team')
                    else:
                        messages.info(request,"Something went wrong!")

                if request.POST.get('update_data_access_member'):
                    
                    new_data_access_member_list=request.POST.getlist('member_select')
                    
                    if(len(new_data_access_member_list)>0):
                        for ieeeID in new_data_access_member_list:
                            if(FinanceAndCorporateTeam.add_member_to_manage_team_access(ieeeID)=="exists"):
                                messages.info(request,f"The member with IEEE Id: {ieeeID} already exists in the Data Access Table")
                            elif(FinanceAndCorporateTeam.add_member_to_manage_team_access(ieeeID)==False):
                                messages.info(request,"Something Went wrong! Please try again")
                            elif(FinanceAndCorporateTeam.add_member_to_manage_team_access(ieeeID)==True):
                                messages.info(request,f"Member with {ieeeID} was added to the team table!")
                                return redirect('finance_and_corporate_team:manage_team')

            context={
                'data_access':data_access,
                'members':team_members,
                'insb_members':all_insb_members,
                'positions':position,
                'user_data':user_data,
                'all_sc_ag':sc_ag,
            }

            return render(request,"finance_and_corporate_team/manage_team.html",context=context)
        else:
            return render(request,"finance_and_corporate_team/access_denied.html", {'all_sc_ag':sc_ag ,'user_data':user_data,})
        
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return cv.custom_500(request)
    

def budgetHomePage(request):
    try:
        sc_ag=PortData.get_all_sc_ag(request=request)
        current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
        user_data=current_user.getUserData() #getting user data as dictionary file
        context={
                'user_data':user_data,
                'all_sc_ag':sc_ag,
            }
        return render(request,"finance_and_corporate_team/budgetHomePage.html",context=context)
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return cv.custom_500(request)
    
@login_required
@member_login_permission
def event_page(request):

    try:

        sc_ag=PortData.get_all_sc_ag(request=request)
        current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
        user_data=current_user.getUserData() #getting user data as dictionary file
        '''Only events organised by INSB would be shown on the event page of Graphics Team
        So, only those events are being retrieved from database'''
        insb_organised_events = Branch.load_insb_organised_events()
    
        context = {
            'all_sc_ag':sc_ag,
            'events_of_insb_only':insb_organised_events,
            'user_data':user_data,
        }


        return render(request,"Events/finance_and_corporate_team_events.html",context)
    
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return cv.custom_500(request)
    
@login_required
@member_login_permission
def create_budget(request, event_id=None):

    if request.method == "POST":
        cst_item = request.POST.getlist('cst_item')
        cst_quantity = request.POST.getlist('cst_quantity')
        cst_upc_bdt = request.POST.getlist('cst_upc_bdt')
        cst_total = request.POST.getlist('cst_total')

        total_cost = 0
        for cost in cst_total:
            total_cost += float(cost)

        rev_item = request.POST.getlist('rev_item')
        rev_quantity = request.POST.getlist('rev_quantity')
        rev_upc_bdt = request.POST.getlist('rev_upc_bdt')
        rev_total = request.POST.getlist('rev_total')

        total_revenue = 0
        for revenue in rev_total:
            total_revenue += float(revenue)

        # cost_data = [
        #     ["ITEM", "QUANTITY", "PRICE PER UNIT (BDT)", "TOTAL PRICE (BDT)"],
        # ]
        cost_data =  {}
        for i in range(len(cst_item)):
            cost_data.update({i : [cst_item[i], cst_quantity[i], cst_upc_bdt[i], cst_total[i]]})

        # revenue_data = [
        #     ["Revenue Type", "Quantity", "Revenue / Unit (BDT)", "Revenue Generated (BDT)"]
        # ]
        revenue_data = {}
        for i in range(len(rev_item)):
            revenue_data.update({i : [rev_item[i], rev_quantity[i], rev_upc_bdt[i], rev_total[i]]})

        event = Events.objects.get(id=event_id)
        BudgetSheet.objects.create(name=f'Budget Of {event.event_name}',
                                   sheet_of=Chapters_Society_and_Affinity_Groups.objects.get(primary=1),
                                   event=event,
                                   costBreakdownData=cost_data,
                                   revenueBreakdownData=revenue_data,
                                   total_cost=total_cost,
                                   total_revenue=total_revenue
                                   )

    if event_id:
        if BudgetSheet.objects.filter(event=event_id).count() > 0:
            budget_sheet = BudgetSheet.objects.get(event=event_id)
            return redirect('finance_and_corporate_team:edit_budget', budget_sheet.pk)
        
        elif Events.objects.filter(id=event_id).count() == 0:
            return redirect('finance_and_corporate_team:event_page')
    else:
        pass
        
        
        # event = Events.objects.get(id=event_id)
        # budget_sheet = BudgetSheet.objects.create(name=f'Budget Of {event.event_name}', sheet_of=Chapters_Society_and_Affinity_Groups.objects.get(primary=1), event=event)
            
    sc_ag=PortData.get_all_sc_ag(request=request)
    current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
    user_data=current_user.getUserData() #getting user data as dictionary file

    context = {
        'all_sc_ag':sc_ag,
        'user_data':user_data,
    }

    return render(request,"finance_and_corporate_team/budgetPage.html", context)


@login_required
@member_login_permission
def edit_budget(request, sheet_id):

    sc_ag=PortData.get_all_sc_ag(request=request)
    current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
    user_data=current_user.getUserData() #getting user data as dictionary file

    budget_sheet = BudgetSheet.objects.get(id=sheet_id)

    context = {
        'all_sc_ag':sc_ag,
        'user_data':user_data,
        'budget_sheet':budget_sheet
    }

    return render(request,"finance_and_corporate_team/budgetPage.html", context)
    
def budgetPage(request):
    try:
        
        if request.method == "POST":
            cst_item = request.POST.getlist('cst_item')
            cst_quantity = request.POST.getlist('cst_quantity')
            cst_upc_bdt = request.POST.getlist('cst_upc_bdt')
            cst_total = request.POST.getlist('cst_total')

            total_cost = 0
            for cost in cst_total:
                total_cost += float(cost)

            rev_item = request.POST.getlist('rev_item')
            rev_quantity = request.POST.getlist('rev_quantity')
            rev_upc_bdt = request.POST.getlist('rev_upc_bdt')
            rev_total = request.POST.getlist('rev_total')

            total_revenue = 0
            for revenue in rev_total:
                total_revenue += float(revenue)

            cost_data = [
                ["ITEM", "QUANTITY", "PRICE PER UNIT (BDT)", "TOTAL PRICE (BDT)"],
            ]

            for i in range(len(cst_item)):
                cost_data.append([cst_item[i], cst_quantity[i], cst_upc_bdt[i], cst_total[i]])

            revenue_data = [
                ["Revenue Type", "Quantity", "Revenue / Unit (BDT)", "Revenue Generated (BDT)"]
            ]

            for i in range(len(rev_item)):
                revenue_data.append([rev_item[i], rev_quantity[i], rev_upc_bdt[i], rev_total[i]])

            BudgetPDF.create_pdf('test.pdf', cost_data, revenue_data)

        sc_ag=PortData.get_all_sc_ag(request=request)
        current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
        user_data=current_user.getUserData() #getting user data as dictionary file
        context={
                'user_data':user_data,
                'all_sc_ag':sc_ag,
            }
        return render(request,"finance_and_corporate_team/budgetPage.html",context=context)
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return cv.custom_500(request)








