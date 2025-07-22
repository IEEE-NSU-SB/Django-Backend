from django.shortcuts import render, redirect
from django.db import DatabaseError, IntegrityError, InternalError
from django.http import HttpResponseServerError, HttpResponseBadRequest, HttpResponse,JsonResponse
from port.renderData import PortData
from recruitment.models import recruitment_session, recruited_members,nsu_departments,nsu_school,nsu_majors
import users
from users.models import MemberSkillSets, Members
from . import renderData
from django.contrib.auth.decorators import login_required
from . forms import StudentForm
from django.contrib import messages
import datetime
from django.core.exceptions import ObjectDoesNotExist
import xlwt,csv
from django.db.utils import IntegrityError
from membership_development_team.renderData import MDT_DATA
from membership_development_team import email_sending
from system_administration.render_access import Access_Render
from users.renderData import LoggedinUser,member_login_permission
import logging
from system_administration.system_error_handling import ErrorHandling
from datetime import datetime
import traceback
from central_branch import views as cv
from django.views import View
from django.http import JsonResponse

# Create your views here.
logger=logging.getLogger(__name__)

@login_required
@member_login_permission
def recruitment_home(request):
    '''Loads all the recruitment sessions present in the database
        this can also register a recruitment session upon data entry
        this passes all the datas into the template file    
    '''
    try:
        sc_ag=PortData.get_all_sc_ag(request=request)
        current_user=LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
        user_data=current_user.getUserData() #getting user data as dictionary file

        #Checking user access
        user=request.user
        has_access=(MDT_DATA.recruitment_session_view_access_control(user.username) or Access_Render.system_administrator_superuser_access(user.username) or Access_Render.system_administrator_staffuser_access(user.username) or Access_Render.eb_access(user.username))
        if has_access:
            numberOfSessions = renderData.Recruitment.loadSession()
            
            if request.method == "POST":
                session_name = request.POST["recruitment_session"]
                session_time=datetime.now()
                try:
                    add_session = recruitment_session(session=session_name,session_time=session_time)
                    add_session.save()
                except DatabaseError:
                    return DatabaseError
            
            context={
                'all_sc_ag':sc_ag,
                'sessions':numberOfSessions,
                "user_data":user_data
            }

            return render(request, 'recruitment_homepage.html', context)
        else:
            return render(request,'access_denied2.html', {'all_sc_ag':sc_ag,'user_data':user_data,})
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return cv.custom_500(request)


@login_required
@member_login_permission
def recruitee(request, pk):
    '''This function is responsible for getting all the members registered in a particular
    recruitment session. Loads all the datas and show them
    '''
    try:
        sc_ag=PortData.get_all_sc_ag(request=request)
        #check the users view access
        user=request.user
        current_user=LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
        user_data=current_user.getUserData() #getting user data as dictionary file

        has_access=(MDT_DATA.recruitment_session_view_access_control(user.username) or Access_Render.system_administrator_superuser_access(user.username) or Access_Render.system_administrator_staffuser_access(user.username) or Access_Render.eb_access(user.username))
        if(has_access):
            
            if request.method == 'POST':
                if 'save_details' in request.POST:
                    recruitment_end_datetime = request.POST.get('recruitment_end_datetime')
                    recruitment_event_link = request.POST.get('recruitment_event_link')
                    is_active = request.POST.get('is_active')

                    if renderData.Recruitment.update_session_details(pk, recruitment_end_datetime, recruitment_event_link, is_active):
                        messages.success(request, 'Session details updated successfully!')
                    else:
                        messages.warning(request, 'Something went wrong!')

                    return redirect('recruitment:recruitee', pk)
        
            getSession = renderData.Recruitment.getSession(session_id=pk)
            getMemberCount = renderData.Recruitment.getTotalNumberOfMembers(int(pk))
            getRecruitedMembers = renderData.Recruitment.getRecruitedMembers(
                session_id=pk)

            get_total_count_of_ieee_payment_completed=renderData.Recruitment.getTotalCountofIEEE_payment_complete(session_id=pk) 
            get_total_count_of_ieee_payment_incomplete=renderData.Recruitment.getTotalCountofIEEE_payment_incomplete(session_id=pk) 
            context = {
                'pk':pk,
                'memberCount': getMemberCount,
                'session': getSession,
                'members': getRecruitedMembers,
                'ieee_payment_complete':get_total_count_of_ieee_payment_completed,
                'ieee_payment_incomplete':get_total_count_of_ieee_payment_incomplete,
                'user_data':user_data,
                'all_sc_ag':sc_ag,
            }
            return render(request, 'session_recruitees.html', context=context)
        else:
            return render(request,'access_denied.html', {'user_data':user_data, 'all_sc_ag':sc_ag})
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return cv.custom_500(request)

@login_required
@member_login_permission
def getPaymentStats(request):

    try:

        if request.method=="GET":
            session_id=request.GET.get('session_id')
            get_total_count_of_ieee_payment_completed=renderData.Recruitment.getTotalCountofIEEE_payment_complete(session_id=session_id) 
            get_total_count_of_ieee_payment_incomplete=renderData.Recruitment.getTotalCountofIEEE_payment_incomplete(session_id=session_id) 
            context={
                "labels":["Complete Payments","Incomplete Payments"],
                "values":[get_total_count_of_ieee_payment_completed,get_total_count_of_ieee_payment_incomplete]
            }
            return JsonResponse(context)   
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return cv.custom_500(request) 


@login_required
@member_login_permission
def recruitee_details(request,session_id,nsu_id):  
    """Preloads all the data of the recruitees who are registered in the particular session, here we can edit and save the data of the recruitee"""
    
    try:

        current_user=LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
        user_data=current_user.getUserData() #getting user data as dictionary file
        sc_ag=PortData.get_all_sc_ag(request=request)

        #Checking user access
        user=request.user
        has_access=(MDT_DATA.recruited_member_details_view_access(user.username) or Access_Render.system_administrator_superuser_access(user.username) or Access_Render.system_administrator_staffuser_access(user.username) or Access_Render.eb_access(user.username))
        if has_access:    
            data = renderData.Recruitment.getRecruitedMemberDetails(nsu_id=nsu_id,session_id=session_id)
            # this parses the date in -DD-MM-YY Format for html
            # this dob does not change any internal data, it is used just to convert the string type from database to load in to html
            if(data==False):
                return redirect('recruitment:recruitee', session_id)
            
            else:    
                dob = datetime.strptime(str(
                    data.date_of_birth), "%Y-%m-%d").strftime("%Y-%m-%d")
                address=data.home_address
                
                checkIfMemberIsRegistered=Members.objects.filter(nsu_id=nsu_id).exists()
                # load all skill types
                all_skills=users.renderData.load_all_skill_types(request)
                
                # Getting the next member for next button
                current_member=recruited_members.objects.get(pk=data.pk)
                if(recruited_members.objects.filter(pk__gt=current_member.pk,session_id=session_id).exists()):
                    has_next_member=True
                    next_member=recruited_members.objects.filter(recruitment_time__gt=current_member.recruitment_time,session_id=session_id).order_by('recruitment_time').first()
                    if(next_member is not None):
                        next_member_nsu_id=next_member.nsu_id
                        has_next_member=True
                    else:
                        next_member_nsu_id=None
                        has_next_member=False
                else:
                    next_member_nsu_id=None
                    has_next_member=False
                    
                # Passing data to the template
                session=data.session_id
                context = {
                    'user_data':user_data,
                    'session': data.session_id,
                    'data': data,
                    'dob': dob,
                    'address':address,
                    'memberExists':checkIfMemberIsRegistered,
                    'has_next_member':has_next_member,
                    'next_member_nsu_id':next_member_nsu_id,
                    'all_sc_ag':sc_ag,
                    'all_skills':all_skills
                }

                if request.method == "POST":
                    
                    
                    # # this is used to update the recruited member details
                    # # Upon entering IEEE id this registers members to the main database of members
                    if request.POST.get('save_edit'):
                        
                        # checks the marked check-boxes
                        cash_payment_status = False
                        if request.POST.get('cash_payment_status'):
                            cash_payment_status = True
                        ieee_payment_status = False
                        if request.POST.get('ieee_payment_status'):
                            ieee_payment_status = True
                        skill_set_list = request.POST.getlist("skill_sets")
                        try:
                            blood_group = request.POST['blood_group']
                        except:
                            blood_group = "None"

                        # Collecting all infos
                        info_dict = {
                            'first_name': request.POST['first_name'],
                            'middle_name': request.POST['middle_name'],
                            'last_name': request.POST['last_name'],
                            'contact_no': request.POST['contact_no'],
                            'emergency_contact_no':request.POST['emergency_contact_no'],
                            'date_of_birth': request.POST['date_of_birth'],
                            'email_personal': request.POST['email_personal'],
                            'email_nsu':request.POST['email_nsu'],
                            'facebook_url': request.POST['facebook_url'],
                            'facebook_username':request.POST['facebook_username'],
                            'home_address': request.POST['home_address'],
                            'gender':request.POST['gender'],
                            'school':request.POST['school'],
                            'department':request.POST['department'],
                            'major': request.POST['major'], 'graduating_year': request.POST['graduating_year'],
                            'ieee_id': request.POST['ieee_id'],
                            'recruited_by': request.POST['recruited_by'],
                            'cash_payment_status': cash_payment_status,
                            'ieee_payment_status': ieee_payment_status,
                            'skill_set_list':skill_set_list,
                            'comment':request.POST['comment'],
                            'blood_group':blood_group
                        }
                        

                        # Getting returned values and handling the exceptions
                        updateRecruiteeDetails = renderData.Recruitment.updateRecruiteeDetails(nsu_id=nsu_id, values=info_dict)

                        if (updateRecruiteeDetails == "no_ieee_id"):
                            messages.error(
                                request, "Please Enter IEEE ID if you have completed payment")
                            return redirect('recruitment:recruitee_details', session_id,nsu_id)
                        elif (updateRecruiteeDetails == IntegrityError):
                            messages.error(
                                request, "There is already a member registered with this IEEE ID")
                            return redirect('recruitment:recruitee_details',session_id, nsu_id)
                        elif (updateRecruiteeDetails == InternalError):
                            messages.error(request, "A Server Error Occured!")
                            return redirect('recruitment:recruitee_details',session_id ,nsu_id)
                        elif (updateRecruiteeDetails):
                            messages.success(request, "Information Updated")
                            return redirect('recruitment:recruitee_details', session_id,nsu_id)
                        else:
                            messages.error(
                                request, "Something went wrong. Please Try again")
                            return redirect('recruitment:recruitee_details', session_id,nsu_id)

                    ##Resending recruitment mail
                    if request.POST.get('resend_email'):
                        name=request.POST['first_name']
                        recruited_member_email=request.POST['email_personal']
                        recruitment_session_name=recruitment_session.objects.get(id=session_id)
                        
                        # updating unique code
                        unique_code=renderData.Recruitment.generateUniqueCode(nsu_id=nsu_id,session=session_id,request=request)
                        recruited_member=recruited_members.objects.get(nsu_id=nsu_id)
                        recruited_member.unique_code=unique_code
                        recruited_member.save()  # Saving the member to the database
                        
                        email_sending_status=email_sending.send_email_to_recruitees_upon_recruitment(
                            name=name,nsu_id=nsu_id,recruited_member_email=recruited_member_email,recruitment_session=recruitment_session_name,unique_code=unique_code
                        )
                        if(email_sending_status):
                            messages.success(request,f"Email was successfully sent to {recruited_member_email}.")
                        else:
                            messages.error(request,f"Could not send email to {recruited_member_email}.")
                    
                    
                    
                    # ##### DELETING RECRUITEES#######
                    if request.POST.get('delete_member'):
                        
                        # if(renderData.Recruitment.deleteMember(nsu_id=nsu_id)=="both_database"):
                        #     messages.info(request,f"Member Deleted Successfully from recruitment process and also from INSB Database with the id {nsu_id}")
                        if (renderData.Recruitment.deleteMember(nsu_id=nsu_id,session_id=data.session_id) == ObjectDoesNotExist):
                            messages.success(
                                request, f"The member with the id {nsu_id} was deleted!")
                            return redirect('recruitment:recruitee', session)
                        elif (renderData.Recruitment.deleteMember(nsu_id=nsu_id,session_id=data.session_id)):
                            
                            return redirect('recruitment:recruitee', session)
                        else:
                            messages.info(request, f"Something went wrong! Try again!")
                            return redirect('recruitment:recruitee', session)
                        
                        

                    # ##### REGISTERING MEMBER IN INSB DATABASE####
                    if request.POST.get("register_member"):
                        
                        getMember = recruited_members.objects.filter(nsu_id=nsu_id)
                        #print(type(getMember[0]['recruitment_time']))
                        # Registering member to the main database
                        try:
                            name = getMember[0].first_name + " "
                            if getMember[0].middle_name:
                                name += getMember[0].middle_name + " "
                            name += getMember[0].last_name
                            newMember = Members(
                                ieee_id=getMember[0].ieee_id,
                                name=name,
                                nsu_id=getMember[0].nsu_id,
                                email_personal=getMember[0].email_personal,
                                email_nsu=getMember[0].email_nsu,
                                school = getMember[0].school,
                                department = getMember[0].department,
                                major=getMember[0].major,
                                contact_no=getMember[0].contact_no,
                                home_address=getMember[0].home_address,
                                date_of_birth=getMember[0].date_of_birth,
                                gender=getMember[0].gender,
                                facebook_url=getMember[0].facebook_url,
                                session=recruitment_session.objects.get(id=getMember[0].session_id),
                                blood_group=getMember[0].blood_group
                            )
                            newMember.save()

                            #After registering the member, register the member's skills
                            member_skill_sets = MemberSkillSets.objects.create(member=newMember)
                            member_skill_sets.skills.add(*getMember[0].skills.all())
                            member_skill_sets.save()

                            messages.success(request, "Member Updated in INSB Database")
                            return redirect('recruitment:recruitee_details',session_id, nsu_id)
                        except IntegrityError:
                            messages.error(
                                "The member is already registered in IEEE NSU SB Database or you have not entered IEEE ID of the member!")
                            return redirect('recruitment:recruitee_details',session_id, nsu_id)
                        except:
                            messages.info(
                                request, "Something went wrong! Please Try again!")
                            return redirect('recruitment:recruitee_details',session_id, nsu_id)
                return render(request,'recruited_member_details.html',context)
        else:
            return render(request,'access_denied.html', {'user_data':user_data, 'all_sc_ag':sc_ag})
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return cv.custom_500(request)

@login_required
@member_login_permission
def recruit_member(request, session_id):

    try:

        sc_ag=PortData.get_all_sc_ag(request=request)
        current_user=LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
        user_data=current_user.getUserData() #getting user data as dictionary file
        
        #Checking user access
        user=request.user
        has_access=(MDT_DATA.recruited_member_details_view_access(user.username) or Access_Render.system_administrator_superuser_access(user.username) or Access_Render.system_administrator_staffuser_access(user.username) or Access_Render.eb_access(user.username))
        if has_access:
            Session = renderData.Recruitment.getSessionid(
                session_id=session_id)
            form = StudentForm
            # load all skill types
            all_skills=users.renderData.load_all_skill_types(request)
            all_schools = nsu_school.objects.all()
            all_departments = nsu_departments.objects.all()
            all_majors = nsu_majors.objects.all()

            context = {
                'user_data':user_data,
                'all_sc_ag':sc_ag,
                'form': form,
                'session_name': Session.session,
                'session_id': Session.id,
                'all_skills':all_skills,
                'all_schools':all_schools,
                'all_departments':all_departments,
                'all_majors':all_majors,
            }

            # this method is for the POST from the recruitment form

            if request.method == "POST":
                
            
                    cash_payment_status = False
                    if request.POST.get("cash_payment_status"):
                        cash_payment_status = True
                    ieee_payment_status = False
                    if request.POST.get("ieee_payment_status"):
                        ieee_payment_status = True
                    skill_set_list = request.POST.getlist("skill_sets")

                    time = datetime.now()
                    # getting all data from form and registering user upon validation
                    if(recruited_members.objects.filter(nsu_id=request.POST['nsu_id'],session_id=Session.id).exists()):
                        messages.info(request,f"Member with NSU ID: {request.POST['nsu_id']} is already registered in the database under this same recruitment session!")
                        return redirect('recruitment:recruit_member',Session.id)
                    else:
                        try:
                            try:
                                blood_group = request.POST['blood_group']
                            except:
                                blood_group = "None"
                            recruited_member = recruited_members(
                                nsu_id=request.POST['nsu_id'],
                                first_name=request.POST['first_name'],
                                middle_name=request.POST['middle_name'],
                                last_name=request.POST['last_name'],
                                contact_no=request.POST['contact_no'],
                                emergency_contact_no=request.POST['emergency_contact_no'],
                                date_of_birth=request.POST['date_of_birth'],
                                email_personal=request.POST['email_personal'],
                                email_nsu=request.POST['email_nsu'],
                                gender=request.POST['gender'],
                                facebook_url=request.POST['facebook_url'],
                                facebook_username=request.POST['facebook_username'],
                                home_address=request.POST['home_address'],
                                school = request.POST.get('school'),
                                department = request.POST.get('department'),
                                major=request.POST.get('major'),
                                graduating_year=request.POST['graduating_year'],
                                session_id=Session.id,
                                recruitment_time=time,
                                recruited_by=request.POST['recruited_by'],
                                cash_payment_status=cash_payment_status,
                                ieee_payment_status=ieee_payment_status,
                                blood_group=blood_group
                            )
                            unique_code=renderData.Recruitment.generateUniqueCode(nsu_id=recruited_member.nsu_id,session=recruited_member.session_id,request=request)
                            recruited_member.unique_code=unique_code
                            recruited_member.save()  # Saving the member to the database

                            #Check if any skills were selected
                            if len(skill_set_list) > 0:
                                if skill_set_list[0] != 'null':
                                    #If yes then add them
                                    recruited_member.skills.add(*skill_set_list)
                                    recruited_member.save()  # Saving the member to the database
                            
                            #send an email now to the recruited member
                            email_status=email_sending.send_email_to_recruitees_upon_recruitment(
                                recruited_member.first_name,recruited_member.nsu_id,recruited_member.email_personal,Session.session,unique_code)

                            if(email_status)==False:
                                messages.warning(request,"The system could not send email to the recruited member due to some errors! Please contact the system administrator")
                            elif(email_status):
                                messages.success(request,"A new member was recruited! E-mail was sent to the recruited member!")
                                
                            return redirect('recruitment:recruitee', session_id)

                        except IntegrityError:  # Checking if same id exist and handling the exception
                            messages.info(
                                request, f"Member with NSU ID: {request.POST['nsu_id']} is already registered in the database! It is prohibited to recruit another member with same NSU ID under one recruitment session.")
                            return render(request, "recruitment_form.html", context=context)

                        except Exception as e:  # Handling all errors
                            messages.warning(request, "Something went Wrong! Please try again")
                            return render(request, "recruitment_form.html", context=context)
                        
                        

            else:
                return render(request, "recruitment_form.html", context=context)
        else:
            return render(request,'access_denied2.html', {'all_sc_ag':sc_ag,'user_data':user_data,})
        
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return cv.custom_500(request)


@login_required
@member_login_permission
def generateExcelSheet(request, session_id):
    '''This method generates the excel files for different sessions'''

    try:

        #Checking user access
        user=request.user
        has_access=(MDT_DATA.recruited_member_details_view_access(user.username) or Access_Render.system_administrator_superuser_access(user.username) or Access_Render.system_administrator_staffuser_access(user.username) or Access_Render.eb_access(user.username))
        if has_access:
            date=datetime.now()
            # getting the session to find members recruited in that particular session
            getSession = renderData.Recruitment.getSessionid(session_id=session_id)
            response = HttpResponse(
                content_type='application/ms-excel')  # eclaring content type for the excel files
            response['Content-Disposition'] = f'attachment; filename=Recruitment Session - {getSession.session}---' +\
                str(date.strftime('%m/%d/%Y')) + \
                '.xls'  # making files downloadable with name of session and timestamp
            # adding encoding to the workbook
            workBook = xlwt.Workbook(encoding='utf-8')
            # opening an worksheet to work with the columns
            workSheet = workBook.add_sheet(f'Recruitment-{getSession.session}')

            # generating the first row
            row_num = 0
            font_style = xlwt.XFStyle()
            font_style.font.bold = True

            # Defining columns that will stay in the first row
            columns = ['NSU ID', 'First Name', 'Middle Name', 'Last Name', 'Email (personal)', 'Email (NSU)','Blood Group', 'Contact No', 'IEEE ID', 'Gender', 'Date Of Birth','Facebook Username', 'Facebook Url',
                    'Address', 'School', 'Department', 'Major', 'Graduating Year', 'Recruitment Time', 'Recruited By', 'Cash Payment Status', 'IEEE Payment Status']

            # Defining first column
            for column in range(len(columns)):
                workSheet.write(row_num, column, columns[column], font_style)

            # reverting font style to default
            font_style = xlwt.XFStyle()

            # getting all the values of members as rows with same session
            rows = recruited_members.objects.filter(session_id=session_id).order_by('recruitment_time').values_list('nsu_id',
                                                                                                        'first_name', 'middle_name', 'last_name',
                                                                                                        'email_personal','email_nsu', 'blood_group',
                                                                                                        'contact_no',
                                                                                                        'ieee_id',
                                                                                                        'gender',
                                                                                                        'date_of_birth',
                                                                                                        'facebook_username',
                                                                                                        'facebook_url',
                                                                                                        'home_address',
                                                                                                        'school','department',
                                                                                                        'major', 'graduating_year',
                                                                                                        'recruitment_time',
                                                                                                        'recruited_by',
                                                                                                        'cash_payment_status',
                                                                                                        'ieee_payment_status'
                                                                                                        )

            for row in rows:

                row_num += 1
                for col_num in range(len(row)):
                    workSheet.write(row_num, col_num, str(row[col_num]), font_style)
            workBook.save(response)
            return (response)
        else:
            return render(request,'access_denied2.html')
        
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return cv.custom_500(request)
    
class DepartmentAjax(View):
    
    def get(self,request):
        
        school_name = request.GET.get('school_name')
        try:
            departments = nsu_departments.objects.filter(department_of = nsu_school.objects.get(school_initial = school_name))
        except:
            departments = []
        department_names = []
        for dept in departments:
            department_names.append(dept.department_initial)
        return JsonResponse(data = {
            'school_name':school_name,
            'departments':department_names,
        })
    
class MajorAjax(View):
    
    def get(self,request):
        department_name = request.GET.get('department_name')
        try:
            majors = nsu_majors.objects.filter(major_of = nsu_departments.objects.get(department_initial = department_name))
        except:
            majors = []
        major_names = []
        for maj in majors:
            major_names.append(maj.major_initial)
        return JsonResponse(data = {
            'department_name':department_name,
            'majors':major_names,
        })