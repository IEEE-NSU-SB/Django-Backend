from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [   
    path('', views.wallet_homepage, name='wallet_homepage'),
    path('entries', views.entries, name='entries'),
    path('entries/<int:event_id>/', views.entries, name='entries_event'),
    path('cash_in/', views.cash_in, name='cash_in'),
    path('cash_in/<int:event_id>/', views.cash_in, name='cash_in_event'),
    path('cash_out/', views.cash_out, name='cash_out'),
    path('cash_out/<int:event_id>/', views.cash_out, name='cash_out_event'),
    path('cash_edit/', views.cash_edit, name='cash_edit'),
]
