# payments/serializers.py
from rest_framework import serializers
from .models import Transaction, WebhookEvent, PaymentConfiguration

class TransactionSerializer(serializers.ModelSerializer):
    amount_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'reference', 'email', 'amount', 'amount_display', 'currency',
            'status', 'payment_method', 'customer_name', 'customer_phone',
            'customer_country', 'mobile_money_provider', 'mobile_money_number',
            'bank_code', 'bank_name', 'channel', 'gateway_response',
            'created_at', 'updated_at', 'paid_at', 'metadata'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'paid_at']
    
    def get_amount_display(self, obj):
        currency_symbols = {
            'NGN': '₦',
            'USD': '$',
            'GHS': '₵',
            'ZAR': 'R',
            'KES': 'KSh',
            'EUR': '€',
            'GBP': '£',
            'XOF': 'CFA',
            'EGP': 'E£'
        }
        symbol = currency_symbols.get(obj.currency, obj.currency)
        return f"{symbol}{obj.amount:,.2f}"

class PaymentInitializationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.ChoiceField(
        choices=Transaction.CURRENCY_CHOICES,
        default='NGN'
    )
    payment_method = serializers.ChoiceField(
        choices=Transaction.PAYMENT_METHOD_CHOICES,
        default='card'
    )
    customer_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    customer_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    customer_country = serializers.CharField(max_length=2, default='NG')
    mobile_money_provider = serializers.CharField(max_length=50, required=False, allow_blank=True)
    mobile_money_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    bank_code = serializers.CharField(max_length=10, required=False, allow_blank=True)
    callback_url = serializers.URLField(required=False)
    metadata = serializers.JSONField(required=False, default=dict)
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value
    
    def validate(self, data):
        # Validate mobile money requirements
        if data.get('payment_method') == 'mobile_money':
            if not data.get('mobile_money_provider'):
                raise serializers.ValidationError({
                    'mobile_money_provider': 'Mobile money provider is required'
                })
            if not data.get('mobile_money_number'):
                raise serializers.ValidationError({
                    'mobile_money_number': 'Mobile money number is required'
                })
        
        # Validate bank transfer requirements
        if data.get('payment_method') == 'bank_transfer':
            if not data.get('bank_code'):
                raise serializers.ValidationError({
                    'bank_code': 'Bank code is required for bank transfers'
                })
        
        return data

class PaymentConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentConfiguration
        fields = '__all__'

class WebhookEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookEvent
        fields = '__all__'
        read_only_fields = ['created_at', 'processed_at']