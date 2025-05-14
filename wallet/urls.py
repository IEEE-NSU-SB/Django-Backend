from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [   
    path('', views.wallet_homepage, name='wallet_homepage'),
    path('entries', views.entries, name='entries'),
    path('cash_in/', views.cash_in, name='cash_in'),
]
