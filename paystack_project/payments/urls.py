# payments/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Index endpoint
    path('', views.index, name='index'),
    path('index/', views.index, name='index_alt'),
    
    # Payment endpoints
    path('initialize/', views.InitializePaymentView.as_view(), name='initialize_payment'),
    path('verify/<str:reference>/', views.VerifyPaymentView.as_view(), name='verify_payment'),
    path('callback/', views.payment_callback, name='payment_callback'),
    path('webhook/', views.WebhookView.as_view(), name='webhook'),
    
    # Transaction endpoints
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/<str:reference>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    
    # Configuration endpoints
    path('config/', views.PaymentConfigurationView.as_view(), name='payment_config'),
    path('banks/', views.BankListView.as_view(), name='bank_list'),
    path('banks/<str:country>/', views.BankListView.as_view(), name='bank_list_country'),
    
    # Dashboard
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
]


