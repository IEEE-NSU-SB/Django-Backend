from django.db import models
from central_events.models import Events
from django_resized import ResizedImageField
from PIL import Image, ExifTags
from io import BytesIO
from django.core.files import File

# Create your models here.
#Table for Media Links and Images
class Graphics_Link(models.Model):
    event_id=models.ForeignKey(Events,on_delete=models.CASCADE)
    graphics_link=models.URLField(null=True,blank=True,max_length=300)
class Graphics_Banner_Image(models.Model):
    event_id=models.ForeignKey(Events,on_delete=models.CASCADE)
    selected_image=ResizedImageField(null=True,blank=True,default=None,upload_to='Event_Banner_Image/')

class Graphics_Form_Link(models.Model):
    event_id = models.ForeignKey(Events,on_delete=models.CASCADE)
    graphics_form_link_name = models.CharField(null=True,blank=True,max_length = 200)
    graphics_form_link = models.URLField(null=True,blank=True,max_length=300)
class Graphics_Drive_links(models.Model):

    link_title = models.TextField(null=True,blank=True,default="")
    link = models.URLField(blank=True,null=True,default="www.google_drive_link.com")
    created_at = models.DateTimeField(auto_now_add = True)

    class Meta:

        verbose_name = "Graphics_Drive_link" 
        ordering = ['-created_at']

class Certificate(models.Model):

    event = models.ForeignKey(Events, null=False, blank=False, related_name='certificate_types', on_delete=models.CASCADE)
    title = models.CharField(null=False, blank=False, max_length=50, default='Untitled')

    class Meta:
        verbose_name = 'Certificate Type'

    def __str__(self):
        return f"{self.title} - {self.event.event_name}"
    
class Certificate_Template(models.Model):

    certificate = models.ForeignKey(Certificate, null=True, on_delete=models.SET_NULL)
    svg_template = models.FileField(null=True, blank=True, upload_to='certificates/svg/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Certificate Template'

    def __str__(self):
        return str(self.pk)
    
class Certificate_Receivers(models.Model):

    certificate = models.ForeignKey(Certificate, null=False, blank=False, on_delete=models.CASCADE)
    name = models.CharField(null=False, blank=False, max_length=100, default='Unnamed')
    email = models.CharField(null=False, blank=False, max_length=40)

    class Meta:
        verbose_name = 'Certificate Receivers'

    def __str__(self):
        return f'{self.name} - {self.email}'
