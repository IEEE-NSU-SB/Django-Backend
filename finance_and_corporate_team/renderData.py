from central_events.models import Events
from finance_and_corporate_team.models import BudgetSheet, BudgetSheetAccess
from users.models import Members
from port.models import Chapters_Society_and_Affinity_Groups, Teams,Roles_and_Position
from system_administration.models import FCT_Data_Access
from central_branch.renderData import Branch
class FinanceAndCorporateTeam:

    def get_team_id():
        
        '''Gets the team id from the database only for Finance and Corporate Team. Not the right approach'''
        team=Teams.objects.get(primary=11)
        return team.id

    def load_manage_team_access():
        return FCT_Data_Access.objects.all()
    
    def load_team_members():
        
        '''This function loads all the team members for the Finance and Corporate team'''

        team_members=Branch.load_team_members(team_primary=11)
        return team_members
    
    def load_team_members_with_positions():
        team_members=FinanceAndCorporateTeam.load_team_members()
        co_ordinators=[]
        incharges=[]
        core_volunteers=[]
        team_volunteers=[]
        
        for i in team_members:
            if(i.position.is_officer):
                if(i.position.is_co_ordinator):
                    co_ordinators.append(i)
                else:
                    incharges.append(i)
            elif(i.position.is_volunteer):
                if(i.position.is_core_volunteer):
                    core_volunteers.append(i)
                else:
                    team_volunteers.append(i)
        return co_ordinators,incharges,core_volunteers,team_volunteers      
    
    def add_member_to_team(ieee_id,position):
        Branch.add_member_to_team(ieee_id=ieee_id,position=position,team_primary=11)

    def fct_manage_team_access_modifications(manage_team_access, create_budget_access, ieee_id):
        try:
            FCT_Data_Access.objects.filter(ieee_id=ieee_id).update(manage_team_access=manage_team_access, create_budget_access=create_budget_access)
            return True
        except FCT_Data_Access.DoesNotExist:
            return False
        
    def remove_member_from_manage_team_access(ieee_id):
        try:
            FCT_Data_Access.objects.get(ieee_id=ieee_id).delete()
            return True
        except:
            return False
        
    def add_member_to_manage_team_access(ieee_id):
        try:
            if(FCT_Data_Access.objects.filter(ieee_id=ieee_id).exists()):
                return "exists"
            else:
            
                new_access=FCT_Data_Access(
                    ieee_id=Members.objects.get(ieee_id=ieee_id)
                )
                new_access.save()
            return True
        except:
            return False
        
    def create_budget(request, event_id, cst_item, cst_quantity, cst_upc_bdt, cst_total, rev_item, rev_quantity, rev_upc_bdt, rev_total):
        
        try:
            total_cost = 0
            for cost in cst_total:
                if cost:
                    total_cost += float(cost)

            total_revenue = 0
            for revenue in rev_total:
                if revenue:
                    total_revenue += float(revenue)

            cost_data =  {}
            for i in range(len(cst_item)):
                cost_data.update({i : [cst_item[i], cst_quantity[i], cst_upc_bdt[i], cst_total[i]]})

            revenue_data = {}
            for i in range(len(rev_item)):
                revenue_data.update({i : [rev_item[i], rev_quantity[i], rev_upc_bdt[i], rev_total[i]]})

            if event_id:
                event = Events.objects.get(id=event_id)
                budget_sheet = BudgetSheet.objects.create(name=f'Budget of {event.event_name}',
                                        sheet_of=Chapters_Society_and_Affinity_Groups.objects.get(primary=1),
                                        event=event,
                                        costBreakdownData=cost_data,
                                        revenueBreakdownData=revenue_data,
                                        total_cost=total_cost,
                                        total_revenue=total_revenue)           
            else:
                budget_sheet = BudgetSheet.objects.create(name=f'Budget Of XYZ',
                                                        sheet_of=Chapters_Society_and_Affinity_Groups.objects.get(primary=1),
                                                        costBreakdownData=cost_data,
                                                        revenueBreakdownData=revenue_data,
                                                        total_cost=total_cost,
                                                        total_revenue=total_revenue)
                
            username = request.user.username
            member = Members.objects.get(ieee_id=username)

            BudgetSheetAccess.objects.create(sheet=budget_sheet, member=member, access_type='Edit')
                
            return budget_sheet
        
        except:
            return False
        
    def edit_budget(sheet_id, cst_item, cst_quantity, cst_upc_bdt, cst_total, rev_item, rev_quantity, rev_upc_bdt, rev_total):

        try:
            total_cost = 0
            for cost in cst_total:
                if cost:
                    total_cost += float(cost)

            total_revenue = 0
            for revenue in rev_total:
                if revenue:
                    total_revenue += float(revenue)

            cost_data =  {}
            for i in range(len(cst_item)):
                cost_data.update({i : [cst_item[i], cst_quantity[i], cst_upc_bdt[i], cst_total[i]]})

            revenue_data = {}
            for i in range(len(rev_item)):
                revenue_data.update({i : [rev_item[i], rev_quantity[i], rev_upc_bdt[i], rev_total[i]]})

            budget_sheet = BudgetSheet.objects.get(id=sheet_id)
            budget_sheet.costBreakdownData = cost_data
            budget_sheet.revenueBreakdownData = revenue_data
            budget_sheet.total_cost = total_cost
            budget_sheet.total_revenue = total_revenue
            budget_sheet.save()

            return True
        
        except:
            return False
