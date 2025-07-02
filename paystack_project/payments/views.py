# payments/views.py
import json
import uuid
import logging
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .models import Transaction, WebhookEvent, PaymentConfiguration
from .serializers import (
    TransactionSerializer, 
    PaymentInitializationSerializer,
    PaymentConfigurationSerializer
)
from .services import paystack_service

logger = logging.getLogger('payments')

class InitializePaymentView(generics.CreateAPIView):
    """Initialize payment with Paystack"""
    permission_classes = [AllowAny]
    serializer_class = PaymentInitializationSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        # Generate unique reference
        reference = f"PAY_{uuid.uuid4().hex[:12].upper()}"
        
        try:
            # Create transaction record
            transaction = Transaction.objects.create(
                reference=reference,
                email=data['email'],
                amount=data['amount'],
                currency=data['currency'],
                payment_method=data['payment_method'],
                customer_name=data.get('customer_name', ''),
                customer_phone=data.get('customer_phone', ''),
                customer_country=data.get('customer_country', 'NG'),
                mobile_money_provider=data.get('mobile_money_provider', ''),
                mobile_money_number=data.get('mobile_money_number', ''),
                bank_code=data.get('bank_code', ''),
                metadata=data.get('metadata', {})
            )
            
            # Prepare Paystack payload
            paystack_data = {
                'reference': transaction.reference,
                'email': transaction.email,
                'amount_in_kobo': transaction.amount_in_kobo,
                'currency': transaction.currency,
                'payment_method': transaction.payment_method,
                'customer_name': transaction.customer_name,
                'customer_phone': transaction.customer_phone,
                'mobile_money_provider': transaction.mobile_money_provider,
                'mobile_money_number': transaction.mobile_money_number,
                'bank_code': transaction.bank_code,
                'callback_url': data.get('callback_url', f"{request.build_absolute_uri('/api/payments/callback/')}"),
                'metadata': {
                    'transaction_id': str(transaction.id),
                    'payment_method': transaction.payment_method,
                    'customer_name': transaction.customer_name,
                    'customer_phone': transaction.customer_phone,
                    **transaction.metadata
                }
            }
            
            # Initialize with Paystack
            paystack_response = paystack_service.initialize_payment(paystack_data)
            
            if paystack_response.get('status'):
                response_data = paystack_response['data']
                return Response({
                    'status': 'success',
                    'message': 'Payment initialized successfully',
                    'data': {
                        'authorization_url': response_data.get('authorization_url'),
                        'access_code': response_data.get('access_code'),
                        'reference': transaction.reference,
                        'transaction_id': str(transaction.id)
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                # Delete transaction if initialization failed
                transaction.delete()
                return Response({
                    'status': 'error',
                    'message': paystack_response.get('message', 'Payment initialization failed')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Payment initialization error: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Payment initialization failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyPaymentView(generics.RetrieveAPIView):
    """Verify payment status with Paystack"""
    permission_classes = [AllowAny]
    
    def get(self, request, reference):
        try:
            transaction = Transaction.objects.get(reference=reference)
        except Transaction.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Transaction not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Verify with Paystack
            paystack_response = paystack_service.verify_payment(reference)
            
            if paystack_response.get('status'):
                paystack_data = paystack_response['data']
                
                # Update transaction
                transaction.status = paystack_data['status']
                transaction.paystack_reference = paystack_data['reference']
                transaction.channel = paystack_data.get('channel', '')
                transaction.gateway_response = paystack_data.get('gateway_response', '')
                
                if paystack_data.get('authorization'):
                    transaction.authorization_code = paystack_data['authorization'].get('authorization_code', '')
                
                if paystack_data['status'] == 'success':
                    transaction.paid_at = timezone.now()
                
                transaction.save()
                
                # Serialize transaction data
                serializer = TransactionSerializer(transaction)
                
                return Response({
                    'status': 'success',
                    'message': 'Payment verification successful',
                    'data': {
                        **serializer.data,
                        'paystack_status': paystack_data['status'],
                        'paystack_reference': paystack_data['reference'],
                        'amount_paid': paystack_data.get('amount', 0) / 100,  # Convert from kobo
                        'channel': paystack_data.get('channel'),
                        'fees': paystack_data.get('fees', 0) / 100,
                        'customer': paystack_data.get('customer', {}),
                        'authorization': paystack_data.get('authorization', {})
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 'error',
                    'message': paystack_response.get('message', 'Verification failed')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Payment verification error: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Payment verification failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(generics.CreateAPIView):
    """Handle Paystack webhooks"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Get signature from headers
        signature = request.headers.get('X-Paystack-Signature')
        if not signature:
            logger.warning("Webhook received without signature")
            return Response({
                'status': 'error',
                'message': 'Missing signature'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify signature
        payload = request.body
        if not paystack_service.verify_webhook_signature(payload, signature):
            logger.warning("Invalid webhook signature")
            return Response({
                'status': 'error',
                'message': 'Invalid signature'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            event_data = json.loads(payload)
            event_type = event_data.get('event')
            data = event_data.get('data', {})
            
            # Store webhook event
            webhook_event, created = WebhookEvent.objects.get_or_create(
                paystack_event_id=data.get('id', ''),
                defaults={
                    'event_type': event_type,
                    'reference': data.get('reference', ''),
                    'status': data.get('status', ''),
                    'raw_data': event_data
                }
            )
            
            if created:
                logger.info(f"Processing webhook event: {event_type} for reference: {data.get('reference')}")
                self.process_webhook_event(webhook_event)
            else:
                logger.info(f"Webhook event already processed: {event_type}")
            
            return Response({
                'status': 'success',
                'message': 'Webhook processed successfully'
            }, status=status.HTTP_200_OK)
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook payload")
            return Response({
                'status': 'error',
                'message': 'Invalid JSON payload'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Webhook processing failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def process_webhook_event(self, webhook_event):
        """Process different types of webhook events"""
        try:
            event_data = webhook_event.raw_data['data']
            reference = webhook_event.reference
            
            # Find transaction
            try:
                transaction = Transaction.objects.get(reference=reference)
            except Transaction.DoesNotExist:
                logger.warning(f"Transaction not found for reference: {reference}")
                webhook_event.mark_processed()
                return
            
            if webhook_event.event_type == 'charge.success':
                transaction.status = 'success'
                transaction.paid_at = timezone.now()
                transaction.channel = event_data.get('channel', '')
                transaction.gateway_response = event_data.get('gateway_response', '')
                
                if event_data.get('authorization'):
                    transaction.authorization_code = event_data['authorization'].get('authorization_code', '')
                
                transaction.save()
                logger.info(f"Transaction {reference} marked as successful")
                
            elif webhook_event.event_type == 'charge.failed':
                transaction.status = 'failed'
                transaction.gateway_response = event_data.get('gateway_response', '')
                transaction.save()
                logger.info(f"Transaction {reference} marked as failed")
                
            webhook_event.mark_processed()
            
        except Exception as e:
            logger.error(f"Error processing webhook event: {str(e)}")

class TransactionListView(generics.ListAPIView):
    """List all transactions with filtering"""
    permission_classes = [AllowAny]
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.all()
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by currency
        currency_filter = self.request.query_params.get('currency')
        if currency_filter:
            queryset = queryset.filter(currency=currency_filter)
        
        # Filter by payment method
        method_filter = self.request.query_params.get('payment_method')
        if method_filter:
            queryset = queryset.filter(payment_method=method_filter)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class TransactionDetailView(generics.RetrieveAPIView):
    """Get transaction details"""
    permission_classes = [AllowAny]
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.all()
    lookup_field = 'reference'
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({
                'status': 'success',
                'data': serializer.data
            })
        except Transaction.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Transaction not found'
            }, status=status.HTTP_404_NOT_FOUND)

class PaymentConfigurationView(generics.ListAPIView):
    """Get payment configuration for countries"""
    permission_classes = [AllowAny]
    serializer_class = PaymentConfigurationSerializer
    queryset = PaymentConfiguration.objects.filter(is_active=True)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        })

class BankListView(generics.ListAPIView):
    """Get list of banks for a country"""
    permission_classes = [AllowAny]
    
    def get(self, request, country='nigeria'):
        try:
            response = paystack_service.list_banks(country)
            if response.get('status'):
                return Response({
                    'status': 'success',
                    'data': response['data']
                })
            else:
                return Response({
                    'status': 'error',
                    'message': 'Failed to fetch banks'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error fetching banks: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to fetch banks'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def payment_callback(request):
    """Handle payment callback from Paystack"""
    reference = request.GET.get('reference')
    if not reference:
        return Response({
            'status': 'error',
            'message': 'Missing reference parameter'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        transaction = Transaction.objects.get(reference=reference)
        
        # Verify payment
        paystack_response = paystack_service.verify_payment(reference)
        
        if paystack_response.get('status'):
            paystack_data = paystack_response['data']
            
            # Update transaction
            transaction.status = paystack_data['status']
            transaction.paystack_reference = paystack_data['reference']
            transaction.channel = paystack_data.get('channel', '')
            transaction.gateway_response = paystack_data.get('gateway_response', '')
            
            if paystack_data.get('authorization'):
                transaction.authorization_code = paystack_data['authorization'].get('authorization_code', '')
            
            if paystack_data['status'] == 'success':
                transaction.paid_at = timezone.now()
            
            transaction.save()
            
            return Response({
                'status': 'success',
                'message': 'Payment processed successfully',
                'data': {
                    'reference': reference,
                    'status': transaction.status,
                    'amount': str(transaction.amount),
                    'currency': transaction.currency
                }
            })
        else:
            return Response({
                'status': 'error',
                'message': 'Payment verification failed'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Transaction.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Transaction not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Callback processing error: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Callback processing failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_stats(request):
    """Get dashboard statistics"""
    try:
        total_transactions = Transaction.objects.count()
        successful_transactions = Transaction.objects.filter(status='success').count()
        pending_transactions = Transaction.objects.filter(status='pending').count()
        failed_transactions = Transaction.objects.filter(status='failed').count()
        
        # Calculate success rate
        success_rate = (successful_transactions / total_transactions * 100) if total_transactions > 0 else 0
        
        # Get currency breakdown
        currency_stats = {}
        for currency, name in Transaction.CURRENCY_CHOICES:
            count = Transaction.objects.filter(currency=currency).count()
            if count > 0:
                currency_stats[currency] = {
                    'name': name,
                    'count': count,
                    'successful': Transaction.objects.filter(currency=currency, status='success').count()
                }
        
        # Get payment method breakdown
        method_stats = {}
        for method, name in Transaction.PAYMENT_METHOD_CHOICES:
            count = Transaction.objects.filter(payment_method=method).count()
            if count > 0:
                method_stats[method] = {
                    'name': name,
                    'count': count,
                    'successful': Transaction.objects.filter(payment_method=method, status='success').count()
                }
        
        return Response({
            'status': 'success',
            'data': {
                'total_transactions': total_transactions,
                'successful_transactions': successful_transactions,
                'pending_transactions': pending_transactions,
                'failed_transactions': failed_transactions,
                'success_rate': round(success_rate, 2),
                'currency_breakdown': currency_stats,
                'payment_method_breakdown': method_stats
            }
        })
    except Exception as e:
        logger.error(f"Dashboard stats error: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Failed to fetch dashboard stats'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)