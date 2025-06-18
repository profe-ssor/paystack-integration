# test_api.py
import requests
import json

BASE_URL = 'http://127.0.0.1:8000/api/payments'

def test_initialize_payment():
    """Test payment initialization"""
    data = {
        'email': 'test@example.com',
        'amount': 1000.00,
        'currency': 'NGN',
        'payment_method': 'card',
        'customer_name': 'John Doe',
        'customer_phone': '+2348123456789',
        'customer_country': 'NG'
    }
    
    response = requests.post(f'{BASE_URL}/initialize/', json=data)
    print("Initialize Payment Response:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 201:
        return response.json()['data']['reference']
    return None

def test_verify_payment(reference):
    """Test payment verification"""
    if not reference:
        print("No reference to verify")
        return
    
    response = requests.get(f'{BASE_URL}/verify/{reference}/')
    print(f"\nVerify Payment Response for {reference}:")
    print(json.dumps(response.json(), indent=2))

def test_get_transactions():
    """Test getting transactions"""
    response = requests.get(f'{BASE_URL}/transactions/')
    print("\nTransactions List:")
    print(json.dumps(response.json(), indent=2))

def test_get_config():
    """Test getting payment configuration"""
    response = requests.get(f'{BASE_URL}/config/')
    print("\nPayment Configuration:")
    print(json.dumps(response.json(), indent=2))

def test_get_banks():
    """Test getting banks list"""
    response = requests.get(f'{BASE_URL}/banks/nigeria/')
    print("\nBanks List:")
    print(json.dumps(response.json(), indent=2))

if __name__ == '__main__':
    print("Testing Paystack API...")
    
    # Test initialization
    reference = test_initialize_payment()
    
    # Test verification
    test_verify_payment(reference)
    
    # Test other endpoints
    test_get_transactions()
    test_get_config()
    test_get_banks()