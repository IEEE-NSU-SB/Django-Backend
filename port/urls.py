
from django.urls import path,include
from port import views
from graphics_team.views import certificate_otp, certificate_email, certificate_download

app_name='port'

##defining the urls to work with

urlpatterns = [
    #landing_page
    path('',views.homepage, name='homepage'),
    #developed by
    # path('portal/developers',views.developed_by,name='developers'),
    
    path('portal/authorize/', views.authorize, name='authorize'),
    path('portal/oauth2callback/', views.oauth2callback, name='oauth2callback'),
    path('certificates/get/<str:key>/', certificate_email, name="certificate_base"),
    path('certificates/otp/', certificate_otp, name="certificate_otp"),
    path('certificates/download/', certificate_download, name="certificate_download"),
]
