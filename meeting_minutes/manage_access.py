
from datetime import datetime
import logging
import traceback
from central_branch.view_access import Branch_View_Access
from chapters_and_affinity_group.manage_access import SC_Ag_Render_Access
from chapters_and_affinity_group.models import SC_AG_Members
from meeting_minutes.models import MeetingMinutesAccess
from system_administration.system_error_handling import ErrorHandling
from users.models import Members


class MM_Render_Access:

    logger=logging.getLogger(__name__)
    
    def has_meeting_minutes_create_access(request, sc_ag_primary, team_primary=None):
        
        try:
            # get the user and username. Username will work as IEEE ID and Developer username both
            user=request.user
            username=user.username

            get_member = Members.objects.filter(ieee_id=username)
            if sc_ag_primary == 1:
                
                #Check if the member exits
                if(get_member.exists()):
                    if(Branch_View_Access.common_access(username)):
                        return True
                    else:
                        if team_primary != None and get_member[0].team.primary == team_primary:
                            return True
                        elif team_primary == None and get_member[0].position.is_officer:
                            return True
                        else:
                            return False
                else:
                    if(Branch_View_Access.common_access(username)):
                        return True
                    else:
                        return False
            else:
                #Check if the member exits
                if(get_member.exists()):
                    sc_ag_member = SC_AG_Members.objects.filter(sc_ag__primary=sc_ag_primary, member=get_member[0])
                    if sc_ag_member.exists():
                        if(SC_Ag_Render_Access.get_sc_ag_common_access_non_branch(request, sc_ag_primary)):
                            return True
                        else:
                            if sc_ag_member[0].team != None:
                                return True
                            else:
                                return False
                    else:
                        return False
                else:
                    if(SC_Ag_Render_Access.get_sc_ag_common_access_non_branch(request, sc_ag_primary)):
                        return True
                    else:
                        return False

        except Exception as e:
            if sc_ag_primary == 1:
                if(Branch_View_Access.common_access(request.user.username)):
                    return True
                else:
                    MM_Render_Access.logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
                    ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
                    return False
            else:
                if(SC_Ag_Render_Access.get_sc_ag_common_access_non_branch(request, sc_ag_primary)):
                    return True
                else:
                    MM_Render_Access.logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
                    ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
                    return False
                
    def has_meeting_minutes_homepage_access(request, sc_ag_primary, team_primary=None):

        try:
            # get the user and username. Username will work as IEEE ID and Developer username both
            user=request.user
            username=user.username

            get_member = Members.objects.filter(ieee_id=username)
            if sc_ag_primary == 1:
                
                #Check if the member exits
                if(get_member.exists()):
                    if(Branch_View_Access.common_access(username)):
                        return True
                    else:
                        if team_primary != None and (get_member[0].team.primary == team_primary or get_member[0].position.is_officer):
                            return True
                        elif team_primary == None and get_member[0].team != None:
                            return True
                        else:
                            return False
                else:
                    if(Branch_View_Access.common_access(username)):
                        return True
                    else:
                        return False
            else:
                #Check if the member exits
                if(get_member.exists()):
                    sc_ag_member = SC_AG_Members.objects.filter(sc_ag__primary=sc_ag_primary, member=get_member[0])
                    if sc_ag_member.exists():
                        if(SC_Ag_Render_Access.get_sc_ag_common_access_non_branch(request, sc_ag_primary)):
                            return True
                        else:
                            if sc_ag_member[0].team != None:
                                return True
                            else:
                                return False
                    else:
                        return False
                else:
                    if(SC_Ag_Render_Access.get_sc_ag_common_access_non_branch(request, sc_ag_primary)):
                        return True
                    else:
                        return False

        except Exception as e:
            if sc_ag_primary == 1:
                if(Branch_View_Access.common_access(request.user.username)):
                    return True
                else:
                    MM_Render_Access.logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
                    ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
                    return False
            else:
                if(SC_Ag_Render_Access.get_sc_ag_common_access_non_branch(request, sc_ag_primary)):
                    print('gnbdfvdcsx')
                    return True
                else:
                    MM_Render_Access.logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
                    ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
                    return False

    def has_meeting_minutes_access(request, meeting_minutes_id, sc_ag_primary, team_primary=None):
        
        try:
            # get the user and username. Username will work as IEEE ID and Developer username both
            user=request.user
            username=user.username

            get_member = Members.objects.filter(ieee_id=username)
            member_data_access = MeetingMinutesAccess.objects.filter(meeting_minutes=meeting_minutes_id, member=get_member[0])

            if sc_ag_primary == 1:
                
                #Check if the member exits
                if(get_member.exists()):
                    if(Branch_View_Access.common_access(username)):
                        return 'Edit'
                    else:
                        if member_data_access.exists():
                            return member_data_access[0].access_type
                        elif get_member[0].position.is_officer and get_member[0].team.primary == team_primary:
                            return 'Edit'
                        elif (get_member[0].position.is_officer and get_member[0].team.primary != team_primary) or (get_member[0].team.primary == team_primary) or (team_primary == None and get_member[0].team != None):

                            return 'ViewOnly'
                        else:
                            return 'Restricted'
                else:
                    if(Branch_View_Access.common_access(username)):
                        return 'Edit'
                    else:
                        return 'Restricted'
            else:
                #Check if the member exits
                if(get_member.exists()):
                    sc_ag_member = SC_AG_Members.objects.filter(sc_ag__primary=sc_ag_primary, member=get_member[0])
                    if sc_ag_member.exists():
                        if(SC_Ag_Render_Access.get_sc_ag_common_access_non_branch(request, sc_ag_primary)):
                            return 'Edit'
                        else:
                            if member_data_access.exists():
                                return member_data_access[0].access_type
                            elif sc_ag_member[0].position.is_officer and sc_ag_member[0].team.primary == team_primary:
                                return 'Edit'
                            elif (sc_ag_member[0].position.is_officer and sc_ag_member[0].team.primary != team_primary) or sc_ag_member[0].team.primary == team_primary:
                                return 'ViewOnly'
                            else:
                                return 'Restricted'
                    else:
                        return 'Restricted'
                else:
                    if(SC_Ag_Render_Access.get_sc_ag_common_access_non_branch(request, sc_ag_primary)):
                        return 'Edit'
                    else:
                        return 'Restricted'

        except Exception as e:
            if sc_ag_primary == 1:
                if(Branch_View_Access.common_access(request.user.username)):
                    return 'Edit'
                else:
                    MM_Render_Access.logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
                    ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
                    return 'Restricted'
            else:
                if(SC_Ag_Render_Access.get_sc_ag_common_access_non_branch(request, sc_ag_primary)):
                    return 'Edit'
                else:
                    MM_Render_Access.logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
                    ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
                    return 'Restricted'