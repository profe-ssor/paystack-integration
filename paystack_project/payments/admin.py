# payments/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Transaction, WebhookEvent, PaymentConfiguration

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'email', 'amount_display', 'currency', 
        'status', 'payment_method', 'created_at'
    ]
    list_filter = ['status', 'currency', 'payment_method', 'created_at']
    search_fields = ['reference', 'email', 'customer_name', 'customer_phone']
    readonly_fields = [
        'id', 'reference', 'paystack_reference', 'authorization_code',
        'created_at', 'updated_at', 'paid_at'
    ]
    
    fieldsets = (
        ('Transaction Info', {
            'fields': ('id', 'reference', 'paystack_reference', 'status')
        }),
        ('Customer Info', {
            'fields': ('email', 'customer_name', 'customer_phone', 'customer_country')
        }),
        ('Payment Details', {
            'fields': ('amount', 'currency', 'payment_method')
        }),
        ('Mobile Money', {
            'fields': ('mobile_money_provider', 'mobile_money_number'),
            'classes': ('collapse',)
        }),
        ('Bank Transfer', {
            'fields': ('bank_code', 'bank_name'),
            'classes': ('collapse',)
        }),
        ('Paystack Data', {
            'fields': ('authorization_code', 'gateway_response', 'channel'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at')
        })
    )
    
    def amount_display(self, obj):
        currency_symbols = {
            'NGN': '₦', 'USD': '$', 'GHS': '₵', 'ZAR': 'R', 
            'KES': 'KSh', 'EUR': '€', 'GBP': '£'
        }
        symbol = currency_symbols.get(obj.currency, obj.currency)
        return f"{symbol}{obj.amount:,.2f}"
    amount_display.short_description = 'Amount'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()

@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'reference', 'status', 'processed', 'created_at']
    list_filter = ['event_type', 'status', 'processed', 'created_at']
    search_fields = ['reference', 'paystack_event_id']
    readonly_fields = ['paystack_event_id', 'created_at', 'processed_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-created_at')

@admin.register(PaymentConfiguration)
class PaymentConfigurationAdmin(admin.ModelAdmin):
    list_display = ['country_name', 'currency', 'flag_display', 'is_active']
    list_filter = ['currency', 'is_active']
    search_fields = ['country_name', 'country_code']
    
    def flag_display(self, obj):
        return format_html('<span style="font-size: 20px;">{}</span>', obj.flag)
    flag_display.short_description = 'Flag'