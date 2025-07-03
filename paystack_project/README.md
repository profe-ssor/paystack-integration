# Paystack Integration Backend

Django backend for Paystack multi-currency payment integration.

## Quick Setup

### 1. Install Dependencies
```bash
# Activate virtual environment
source ../paystack_env/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Paystack API Keys
```bash
# Run the setup script
python3 setup_paystack.py
```

This will:
- Create a `.env` file with your Paystack API keys
- Test the connection to Paystack API
- Set up all necessary environment variables

### 3. Get Paystack API Keys
1. Go to [Paystack Dashboard](https://dashboard.paystack.com/#/settings/developer)
2. Copy your **Public Key** (starts with `pk_test_` or `pk_live_`)
3. Copy your **Secret Key** (starts with `sk_test_` or `sk_live_`)

### 4. Run the Server
```bash
# Start Django development server
python3 manage.py runserver
```

The API will be available at: http://localhost:8000/api/payments/

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `PAYSTACK_PUBLIC_KEY` | Paystack public key | ✅ |
| `PAYSTACK_SECRET_KEY` | Paystack secret key | ✅ |
| `PAYSTACK_WEBHOOK_SECRET` | Webhook secret (optional) | ❌ |
| `SECRET_KEY` | Django secret key | ✅ |
| `DEBUG` | Debug mode | ❌ |
| `DATABASE_URL` | Database URL | ❌ |

## API Endpoints

- `GET /api/payments/` - List all transactions
- `POST /api/payments/initialize/` - Initialize payment
- `GET /api/payments/verify/{reference}/` - Verify payment
- `GET /api/payments/` - Index endpoint

## Troubleshooting

### 401 Unauthorized Error
This means your Paystack API keys are not configured correctly:
1. Check that your `.env` file exists
2. Verify your API keys are correct
3. Make sure you're using the right keys (test vs live)

### 403 Forbidden Error
This usually means your API keys are invalid or expired:
1. Regenerate your API keys in Paystack dashboard
2. Update your `.env` file with new keys

### Connection Issues
1. Check your internet connection
2. Verify Paystack API is accessible
3. Check firewall settings 