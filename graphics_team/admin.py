from django.contrib import admin
from .models import Certificate_Receiver_Download_Request, Certificate_Receiver_Download_URL, Graphics_Link,Graphics_Banner_Image,Graphics_Form_Link,Graphics_Drive_links,Certificate,Certificate_Receivers,Certificate_Template, Certificate_Public_URL
# Register your models here.
@admin.register(Graphics_Link)
class Graphics_Link(admin.ModelAdmin):
    list_display = ['id','event_id','graphics_link']
@admin.register(Graphics_Banner_Image)
class Graphics_Banner_Image(admin.ModelAdmin):
    list_display=['id','event_id','selected_image']

@admin.register(Graphics_Form_Link)
class Graphics_Form_Link(admin.ModelAdmin):
    list_display=['event_id','graphics_form_link_name','graphics_form_link']

@admin.register(Graphics_Drive_links)
class Graphics_Drive_Link(admin.ModelAdmin):
    list_display = ['link_title','link','created_at']

admin.site.register(Certificate)
admin.site.register(Certificate_Receivers)
admin.site.register(Certificate_Template)
admin.site.register(Certificate_Public_URL)
admin.site.register(Certificate_Receiver_Download_Request)
admin.site.register(Certificate_Receiver_Download_URL)