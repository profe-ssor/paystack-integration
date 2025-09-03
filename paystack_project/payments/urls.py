# payments/urls.py
from django.urls import path
from . import views
from . import auth_views

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
    
    # Authentication endpoints
    path('auth/register/', auth_views.UserRegistrationView.as_view(), name='user_register'),
    path('auth/login/', auth_views.UserLoginView.as_view(), name='user_login'),
    path('auth/profile/', auth_views.UserProfileView.as_view(), name='user_profile'),
    path('auth/logout/', auth_views.logout, name='user_logout'),
    path('auth/refresh/', auth_views.refresh_token, name='refresh_token'),
]


