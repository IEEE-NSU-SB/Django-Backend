from datetime import timedelta
import random
import secrets
import string
import uuid
from django.db import models
from django.urls import reverse
from django.utils import timezone
from central_events.models import Events
from django_resized import ResizedImageField
from PIL import Image, ExifTags
from io import BytesIO
from django.core.files import File
from django.contrib.auth.hashers import make_password, check_password

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
    
class Certificate_Public_URL(models.Model):

    certificate = models.OneToOneField(Certificate, null=False, blank=False, on_delete=models.CASCADE)
    url_key = models.CharField(null=False, blank=False, max_length=40, unique=True)
    is_active = models.BooleanField(null=False, blank=False, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Generate a secure 40-char key if not already set
        if not self.url_key:
            alphabet = string.ascii_letters + string.digits
            self.url_key = ''.join(secrets.choice(alphabet) for _ in range(20))
        super().save(*args, **kwargs)

    def get_public_url(self, request=None):
        path = reverse('port:certificate_base', kwargs={'key' : self.url_key})
        
        if request:
            return request.build_absolute_uri(path)
        return path

    class Meta:
        verbose_name = 'Certificate Public URL'

    def __str__(self):
        return str(self.pk)
    
class Certificate_Receiver_Download_Request(models.Model):

    certificate = models.ForeignKey(Certificate, null=False, blank=False, on_delete=models.CASCADE)
    certificate_receiver = models.ForeignKey(Certificate_Receivers, blank=False, null=False, on_delete=models.CASCADE)
    requested_at = models.DateTimeField(auto_now_add=True)

    # OTP fields
    otp_code = models.CharField(max_length=128)
    otp_expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    # Security
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=5)

    #unique request ID
    request_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def is_expired(self):
        return timezone.now() > self.otp_expires_at

    def can_attempt(self):
        return self.attempts < self.max_attempts
    
    def set_otp(self, length=6, validity_minutes=5):
        """Generate and hash OTP, set expiration"""
        otp_raw = f"{random.randint(0, 10**length - 1):0{length}}"
        self.otp_code = make_password(otp_raw)
        self.otp_expires_at = timezone.now() + timedelta(minutes=validity_minutes)
        self.is_used = False
        self.attempts = 0
        self.save()
        return otp_raw

    def verify_otp(self, raw_otp):
        """
        Verify OTP:
        - Not expired
        - Not used
        - Within max attempts
        """
        if  self.is_used:
            return False, "OTP already used"

        if self.is_expired():
            return False, "OTP expired"

        if not self.can_attempt():
            return False, "Maximum attempts reached"

        self.attempts += 1

        if check_password(raw_otp, self.otp_code):
            self.is_used = True
            self.save()
            return True, "OTP verified successfully"
        else:
            self.save()
            return False, "Incorrect OTP"
    
    class Meta:
        verbose_name = 'Certificate Receiver Download Request'

    def __str__(self):
        return str(self.pk)
    
# class Certificate_Receiver_Download_URL(models.Model):

#     download_request = models.OneToOneField(Certificate_Receiver_Download_Request, null=False, blank=False)
#     url_key = models.CharField(null=False, blank=False, max_length=40, unique=True)
#     is_active = models.BooleanField(null=False, blank=False, default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     expires_at = models.DateTimeField(null=False, blank=False)

#     def save(self, *args, **kwargs):
#         # Generate a secure 40-char key if not already set
#         if not self.url_key:
#             alphabet = string.ascii_letters + string.digits
#             self.url_key = ''.join(secrets.choice(alphabet) for _ in range(40))

#         # Set default expiry if not already set (e.g., 1 day)
#         if not self.expires_at:
#             self.expires_at = timezone.now() + timedelta(days=1)

#         super().save(*args, **kwargs)

#     def is_expired(self):
#         """Check if the URL has expired"""
#         return timezone.now() > self.expires_at

#     def get_download_url(self):
#         """Return full URL"""
#         return f"https://example.com/download/{self.url_key}/"

#     class Meta:
#         verbose_name = 'Certificate Public URL'

#     def __str__(self):
#         return str(self.pk)
