# payments/services.py
import requests
import hashlib
import hmac
import json
import logging
from django.conf import settings
from typing import Dict, Any, Optional

logger = logging.getLogger('payments')

class PaystackService:
    BASE_URL = 'https://api.paystack.co'
    
    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.public_key = settings.PAYSTACK_PUBLIC_KEY
        self.webhook_secret = settings.PAYSTACK_WEBHOOK_SECRET
        # Check if we're in test mode (when keys are placeholder values)
        self.test_mode = (
            self.secret_key == 'sk_test_your_paystack_secret_key_here' or
            self.public_key == 'pk_test_your_paystack_public_key_here'
        )
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to Paystack API"""
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=data)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Paystack API request failed: {str(e)}")
            raise Exception(f"Payment service error: {str(e)}")
    
    def initialize_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize payment with Paystack"""
        
        # If in test mode, return mock response
        if self.test_mode:
            logger.info(f"TEST MODE: Initializing payment for reference: {payment_data['reference']}")
            return {
                'status': True,
                'message': 'Payment initialized successfully (TEST MODE)',
                'data': {
                    'authorization_url': f"http://localhost:5176/payment/success?reference={payment_data['reference']}",
                    'access_code': f"TEST_ACCESS_{payment_data['reference']}",
                    'reference': payment_data['reference']
                }
            }
        
        endpoint = '/transaction/initialize'
        
        # Prepare payload
        payload = {
            'reference': payment_data['reference'],
            'email': payment_data['email'],
            'amount': payment_data['amount_in_kobo'],
            'currency': payment_data['currency'],
            'callback_url': payment_data.get('callback_url'),
            'metadata': payment_data.get('metadata', {})
        }
        
        # Add mobile money specific data
        if payment_data.get('payment_method') == 'mobile_money':
            payload['mobile_money'] = {
                'phone': payment_data.get('mobile_money_number'),
                'provider': payment_data.get('mobile_money_provider')
            }
        
        # Add bank transfer specific data
        if payment_data.get('payment_method') == 'bank_transfer':
            payload['bank'] = {
                'code': payment_data.get('bank_code')
            }
        
        # Add customer data
        if payment_data.get('customer_name') or payment_data.get('customer_phone'):
            payload['customer'] = {}
            if payment_data.get('customer_name'):
                payload['customer']['first_name'] = payment_data['customer_name'].split()[0]
                if len(payment_data['customer_name'].split()) > 1:
                    payload['customer']['last_name'] = ' '.join(payment_data['customer_name'].split()[1:])
            if payment_data.get('customer_phone'):
                payload['customer']['phone'] = payment_data['customer_phone']
        
        logger.info(f"Initializing payment for reference: {payment_data['reference']}")
        return self._make_request('POST', endpoint, payload)
    
    def verify_payment(self, reference: str) -> Dict[str, Any]:
        """Verify payment with Paystack"""
        
        # If in test mode, return mock response
        if self.test_mode:
            logger.info(f"TEST MODE: Verifying payment for reference: {reference}")
            return {
                'status': True,
                'message': 'Payment verified successfully (TEST MODE)',
                'data': {
                    'reference': reference,
                    'status': 'success',
                    'amount': 100000,  # 1000 NGN in kobo
                    'currency': 'NGN',
                    'channel': 'test',
                    'gateway_response': 'Successful (TEST MODE)',
                    'customer': {
                        'email': 'test@example.com',
                        'customer_code': 'TEST_CUSTOMER_001'
                    },
                    'authorization': {
                        'authorization_code': f'TEST_AUTH_{reference}',
                        'card_type': 'test',
                        'last4': '0000',
                        'exp_month': '12',
                        'exp_year': '2025',
                        'bank': 'TEST BANK',
                        'country_code': 'NG',
                        'brand': 'test'
                    }
                }
            }
        
        endpoint = f'/transaction/verify/{reference}'
        logger.info(f"Verifying payment for reference: {reference}")
        return self._make_request('GET', endpoint)
    
    def list_banks(self, country: str = 'nigeria') -> Dict[str, Any]:
        """Get list of banks for a country"""
        endpoint = f'/bank?country={country}'
        return self._make_request('GET', endpoint)
    
    def validate_account(self, account_number: str, bank_code: str) -> Dict[str, Any]:
        """Validate bank account"""
        endpoint = '/bank/resolve'
        data = {
            'account_number': account_number,
            'bank_code': bank_code
        }
        return self._make_request('GET', endpoint, data)
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature from Paystack"""
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured")
            return False
        
        expected_signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    def get_supported_countries(self) -> Dict[str, Any]:
        """Get list of supported countries"""
        endpoint = '/country'
        return self._make_request('GET', endpoint)

# Singleton instance
paystack_service = PaystackService()