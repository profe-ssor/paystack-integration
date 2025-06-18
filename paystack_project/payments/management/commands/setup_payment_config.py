from django.core.management.base import BaseCommand
from payments.models import PaymentConfiguration

class Command(BaseCommand):
    help = 'Setup initial payment configuration data'
    
    def handle(self, *args, **options):
        configs = [
            {
                'country_code': 'NG',
                'country_name': 'Nigeria',
                'currency': 'NGN',
                'flag': '🇳🇬',
                'supported_methods': ['card', 'bank_transfer', 'ussd', 'qr'],
                'banks': [
                    {'code': '044', 'name': 'Access Bank'},
                    {'code': '014', 'name': 'Afribank Nigeria Plc'},
                    {'code': '023', 'name': 'Citibank Nigeria'},
                    {'code': '058', 'name': 'Guaranty Trust Bank'},
                    {'code': '030', 'name': 'Heritage Bank'},
                    {'code': '082', 'name': 'Keystone Bank'},
                    {'code': '076', 'name': 'Polaris Bank'},
                    {'code': '101', 'name': 'Providus Bank'},
                    {'code': '221', 'name': 'Stanbic IBTC Bank'},
                    {'code': '068', 'name': 'Standard Chartered Bank'},
                    {'code': '232', 'name': 'Sterling Bank'},
                    {'code': '032', 'name': 'Union Bank of Nigeria'},
                    {'code': '033', 'name': 'United Bank For Africa'},
                    {'code': '215', 'name': 'Unity Bank'},
                    {'code': '035', 'name': 'Wema Bank'},
                    {'code': '057', 'name': 'Zenith Bank'}
                ],
                'ussd_codes': {
                    'access': '*901*amount*account#',
                    'gtb': '*737*amount*account#',
                    'uba': '*919*amount*account#',
                    'zenith': '*966*amount*account#'
                },
                'min_amount': 100.00,
                'max_amount': 5000000.00
            },
            {
                'country_code': 'GH',
                'country_name': 'Ghana',
                'currency': 'GHS',
                'flag': '🇬🇭',
                'supported_methods': ['card', 'mobile_money', 'bank_transfer'],
                'banks': [
                    {'code': 'GCB', 'name': 'Ghana Commercial Bank'},
                    {'code': 'EBG', 'name': 'Ecobank Ghana'},
                    {'code': 'SCB', 'name': 'Standard Chartered Bank Ghana'},
                    {'code': 'CAL', 'name': 'CAL Bank'},
                    {'code': 'ADB', 'name': 'Agricultural Development Bank'}
                ],
                'mobile_money_providers': [
                    {'code': 'mtn', 'name': 'MTN Mobile Money', 'prefix': '024'},
                    {'code': 'vodafone', 'name': 'Vodafone Cash', 'prefix': '020'},
                    {'code': 'airteltigo', 'name': 'AirtelTigo Money', 'prefix': '027'}
                ],
                'min_amount': 1.00,
                'max_amount': 50000.00
            },
            {
                'country_code': 'KE',
                'country_name': 'Kenya',
                'currency': 'KES',
                'flag': '🇰🇪',
                'supported_methods': ['card', 'mobile_money', 'bank_transfer'],
                'banks': [
                    {'code': 'KCB', 'name': 'Kenya Commercial Bank'},
                    {'code': 'EQB', 'name': 'Equity Bank'},
                    {'code': 'CBA', 'name': 'Commercial Bank of Africa'},
                    {'code': 'SCB', 'name': 'Standard Chartered Kenya'}
                ],
                'mobile_money_providers': [
                    {'code': 'mpesa', 'name': 'M-Pesa', 'prefix': '254'},
                    {'code': 'airtel', 'name': 'Airtel Money', 'prefix': '254'}
                ],
                'min_amount': 1.00,
                'max_amount': 100000.00
            },
            {
                'country_code': 'ZA',
                'country_name': 'South Africa',
                'currency': 'ZAR',
                'flag': '🇿🇦',
                'supported_methods': ['card', 'eft', 'mobile_money'],
                'banks': [
                    {'code': 'ABSA', 'name': 'Absa Bank'},
                    {'code': 'FNB', 'name': 'First National Bank'},
                    {'code': 'NED', 'name': 'Nedbank'},
                    {'code': 'STD', 'name': 'Standard Bank'}
                ],
                'mobile_money_providers': [
                    {'code': 'mtn', 'name': 'MTN Mobile Money', 'prefix': '27'}
                ],
                'min_amount': 1.00,
                'max_amount': 10000.00
            }
        ]
        
        created_count = 0
        for config_data in configs:
            config, created = PaymentConfiguration.objects.get_or_create(
                country_code=config_data['country_code'],
                defaults=config_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created config for {config_data["country_name"]}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Config for {config_data["country_name"]} already exists')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} payment configurations')
        )