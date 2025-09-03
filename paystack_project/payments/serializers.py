# payments/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Transaction, PaymentConfiguration

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined')
        read_only_fields = ('id', 'date_joined')

class TransactionSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ('id', 'reference', 'paystack_reference', 'authorization_code', 
                           'gateway_response', 'channel', 'created_at', 'updated_at', 'paid_at')

class PaymentInitializationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField(max_length=3)
    payment_method = serializers.CharField(max_length=20)
    customer_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    customer_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    customer_country = serializers.CharField(max_length=2, required=False, default='NG')
    mobile_money_provider = serializers.CharField(max_length=50, required=False, allow_blank=True)
    mobile_money_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    bank_code = serializers.CharField(max_length=10, required=False, allow_blank=True)
    callback_url = serializers.URLField(required=False)
    metadata = serializers.JSONField(required=False, default=dict)

class PaymentConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentConfiguration
        fields = '__all__'