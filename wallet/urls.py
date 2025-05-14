from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [   
    path('', views.wallet_homepage, name='wallet_homepage'),
    path('entries', views.entries, name='entries'),
    path('cash_in/', views.cash_in, name='cash_in'),
    path('cash_out/', views.cash_out, name='cash_out'),
    path('cash_edit/', views.cash_edit, name='cash_edit'),
]
