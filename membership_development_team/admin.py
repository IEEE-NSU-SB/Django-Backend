from django.contrib import admin
from . models import Renewal_Sessions,Renewal_requests,Portal_Joining_Requests,Renewal_Form_Info,Birthday_Email_Records
# Register your models here.
@admin.register(Renewal_Sessions)
class Renewal_Sessions(admin.ModelAdmin):
    list_display=['id','session_name','session_time']
@admin.register(Renewal_requests)
class Renewal_Requests(admin.ModelAdmin):
    list_display = ['id', 'session_id_id', 'name']
    readonly_fields = ('view_encrypted_password',)
    exclude = ('_ieee_account_password',)

    def view_encrypted_password(self, obj):
        return "Hidden for security"

    view_encrypted_password.short_description = 'IEEE Account Password'
@admin.register(Portal_Joining_Requests)
class Joining_Requests(admin.ModelAdmin):
    list_display=['ieee_id','name','position','team']
@admin.register(Renewal_Form_Info)
class Renewal_Form_Info(admin.ModelAdmin):
    list_display=['form_id','session']
@admin.register(Birthday_Email_Records)
class Birthday_Email_Records(admin.ModelAdmin):
    list_display = ['confirm_message']
