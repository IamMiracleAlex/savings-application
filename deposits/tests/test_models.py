import datetime

from django.test import TestCase

from deposits.models.fund_source import FundSource
from users.models import CustomUser


class FundSourceModelTest(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.user_data = {'phone_number':'2348026043569', 
                        'password':'password123',
                        'email':'miracle@savests.com',
                    }
        cls.user = CustomUser.objects.create_user(**cls.user_data)

        # load source data
        cls.fs_data = {'user': cls.user,
                    'last4': '4444',
                    'bank_name': 'American',
                    'card_type': 'visa',
                    'exp_month': '09',
                    'exp_year': '2024',
                    'is_active': True
                    }
        cls.fs = FundSource.objects.create(**cls.fs_data)

    def test_safelock_creation(self):
        '''Assert that fund source was created, after filling in a user
        and other details.
        '''
       
        self.assertIsNotNone(self.fs.user)
        self.assertEqual(self.fs.last4, self.fs_data['last4'])
        self.assertEqual(self.fs.bank_name, self.fs_data['bank_name'])
        self.assertEqual(self.fs.card_type, self.fs_data['card_type'])
        self.assertEqual(self.fs.exp_year, self.fs_data['exp_year'])
        self.assertEqual(self.fs.is_active, self.fs_data['is_active'])










