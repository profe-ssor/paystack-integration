# payments/models.py
from django.db import models
import uuid
from django.utils import timezone

class Transaction(models.Model):
    CURRENCY_CHOICES = [
        ('NGN', 'Nigerian Naira'),
        ('USD', 'US Dollar'),
        ('GHS', 'Ghanaian Cedi'),
        ('ZAR', 'South African Rand'),
        ('KES', 'Kenyan Shilling'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('XOF', 'West African CFA Franc'),
        ('EGP', 'Egyptian Pound'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('abandoned', 'Abandoned'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('ussd', 'USSD'),
        ('qr', 'QR Code'),
        ('eft', 'EFT'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=100, unique=True)
    email = models.EmailField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='NGN')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    
    # Customer Information
    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_country = models.CharField(max_length=2, default='NG')
    
    # Mobile Money Specific
    mobile_money_provider = models.CharField(max_length=50, blank=True)
    mobile_money_number = models.CharField(max_length=20, blank=True)
    
    # Bank Transfer Specific
    bank_code = models.CharField(max_length=10, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    
    # Paystack Response Data
    paystack_reference = models.CharField(max_length=100, blank=True)
    authorization_code = models.CharField(max_length=100, blank=True)
    gateway_response = models.TextField(blank=True)
    channel = models.CharField(max_length=50, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.reference} - {self.amount} {self.currency}"
    
    @property
    def amount_in_kobo(self):
        """Convert amount to kobo/cents for Paystack"""
        return int(float(self.amount) * 100)

class WebhookEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ('charge.success', 'Charge Success'),
        ('charge.failed', 'Charge Failed'),
        ('transfer.success', 'Transfer Success'),
        ('transfer.failed', 'Transfer Failed'),
    ]
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    paystack_event_id = models.CharField(max_length=100, unique=True)
    reference = models.CharField(max_length=100)
    status = models.CharField(max_length=20)
    raw_data = models.JSONField()
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.event_type} - {self.reference}"
    
    def mark_processed(self):
        self.processed = True
        self.processed_at = timezone.now()
        self.save()

class PaymentConfiguration(models.Model):
    """Store payment configuration and supported methods per country"""
    country_code = models.CharField(max_length=2, unique=True)
    country_name = models.CharField(max_length=100)
    currency = models.CharField(max_length=3)
    flag = models.CharField(max_length=10)
    supported_methods = models.JSONField(default=list)
    banks = models.JSONField(default=list)
    mobile_money_providers = models.JSONField(default=list)
    ussd_codes = models.JSONField(default=dict)
    min_amount = models.DecimalField(max_digits=12, decimal_places=2, default=1.00)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, default=1000000.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.country_name} ({self.currency})"