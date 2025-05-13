from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [   
    path('', views.wallet_homepage, name='wallet_homepage'),
    path('add_cash/', views.add_cash, name='add_cash'),
    path('cash_out/', views.cash_out, name='cash_out'),
    path('edit_cash/', views.edit_cash, name='edit_cash')
]
