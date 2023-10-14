import datetime
from unittest.mock import patch
from unittest import skip

from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework import status

from users.models import CustomUser
from accounts.models import Account
from subscriptions.models import Subscription
from deposits.models import FundSource
from safelocks.models import SafeLock
from safelocks.views import activate_safelock_deposit, create_transfer


class ListCreateSafeLocksTest(APITestCase):

    def setUp(self):
        self.user_data = {'phone_number': '08026043569',
                        'password': 'password123',
                        'email': 'miracle@savests.com'}
        self.user = CustomUser.objects.create_user(**self.user_data)
        self.user.account_set.update(balance=2000)
        self.account = self.user.account_set.get(type_of_account=Account.DEPOSIT)

         # load data and create safelock
        self.safe_data = {
                    'name': 'invest',
                    'amount': 1000,
                    'target_goal': 1000000,
                    'category': 'Car',
                    'reference': 'reference' ,
                    'transfer_from': 'wallet' ,
                    'maturity_date': datetime.date.today() + datetime.timedelta(days=100),
                    }
        self.url = reverse('safelocks:safelocks')
    

    def test_post(self):
        '''Assert that the post method creates a safelock successfully'''
       
        self.client.force_authenticate(self.user)
        resp = self.client.post(self.url, data=self.safe_data)

        # assert that safelock was created succesful, 
        self.assertEqual(resp.status_code,  status.HTTP_200_OK)
        self.assertIn('Deposit created successfully', resp.data['message'])
        self.assertEqual(self.safe_data['name'], resp.data['data']['name'])


    def test_get(self):
        '''Assert that the get method gets safelocks successfully'''
                    
        self.safe_data['category'] = SafeLock.Car
        self.safe_data['is_active'] = True
        self.safe_data['account'] = self.account

        # remove unwanted data and create safelock
        del self.safe_data['reference']
        del self.safe_data['transfer_from']
        SafeLock.objects.create(**self.safe_data)

        self.client.force_authenticate(self.user)
        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code,  status.HTTP_200_OK)
        self.assertEqual(resp.data['message'],  'Success')
        self.assertEqual(resp.data['data'][0]['name'],  self.safe_data['name'])


class UpdateSafelocksTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user_data = {'phone_number': '08026043569',
                        'password': 'password123',
                        'email': 'miracle@savests.com'}
        cls.user = CustomUser.objects.create_user(**cls.user_data)
        cls.user.account_set.update(balance=2000)
        cls.account = cls.user.account_set.get(type_of_account=Account.DEPOSIT)

        cls.safe_data = {
                    'name': 'invest',
                    'amount': 1000,
                    'target_goal': 1000000,
                    'category': SafeLock.Car,
                    'account': cls.account ,
                    'is_active': True ,
                    'maturity_date': datetime.date.today() + datetime.timedelta(days=100),
                    }

        cls.url = reverse('safelocks:safelock')


    def test_put(self):
        '''Assert that the put method works'''

        # create a safelock
        safelock = SafeLock.objects.create(**self.safe_data)

        # data for updating safelock
        update_data = {
                    'name': 'home',
                    'amount': 1000,
                    'target_goal': 1000000,
                    'id': safelock.id,
                    'reference': 'reference' ,
                    'transfer_from': 'wallet' ,
        }

        self.client.force_authenticate(self.user)
        resp = self.client.put(self.url, data=update_data)

        # assert that request was succesful, and data was updated
        self.assertEqual(resp.status_code,  status.HTTP_200_OK)
        self.assertEqual(resp.data['message'],
                            'Term Deposit updated successfully')
        self.assertEqual(resp.data['data']['amount'], safelock.amount + update_data['amount'])                    

   


class SafeLocksFunctions(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user_data = {'phone_number': '08026043569',
                        'password': 'password123',
                        'email': 'miracle@savests.com'}
        cls.user = CustomUser.objects.create_user(**cls.user_data)
        cls.account = cls.user.account_set.get(type_of_account=Account.DEPOSIT)

        fs = FundSource.objects.create(user=cls.user, last4='4444',
                            bank_name='American', card_type='visa', 
                            exp_month='09', exp_year='2024',
                            is_active=True) 
     
        cls.user.default_deposit_fund_source = fs
        cls.user.save()

        # load safelock data
        cls.safe_data = {'account': cls.account,
                    'name': 'invest',
                    'amount': 200,
                    'interest': 20.0,
                    'target_goal': 1000000,
                    'category': SafeLock.Investment,
                    'maturity_date': datetime.date.today() + datetime.timedelta(days=100),
                    }

    def test_create_transfer(self):
        '''Assert that the create transfer method works'''

        # create safelock
        safelock = SafeLock.objects.create(**self.safe_data)

        ct = create_transfer(safelock, 'reference', 1000)
        self.assertEqual(ct, True) # return value on success


    def test_activate_safelock_deposit(self):
        '''Assert that activate_safelock_deposit works'''

        success_response = { # define return values for success
                'status': True,
                'message':  'deposit successful',
                'data':  {'status': 'success'}
            }
        failure_response = { # define return values for failures
                'status': False,
                'message':  'deposit failed',
                'data':  {'status': 'failure',
                        'gateway_response': 'invalid card'
                }
            } 
        safelock = SafeLock.objects.create(**self.safe_data)


        '''case 1, when paystack endpoint returns a succesful transaction''' 

        with patch('safelocks.views.PaystackService.charge_card') as pcc:
            
            pcc.return_value = success_response # define return values
            resp, deposit = activate_safelock_deposit(safelock.id, 'reference', 1000)    

        # assertions
        self.assertEqual(resp, success_response['message'])


        '''case 2, when paystack endpoint fails''' 

        with patch('safelocks.views.PaystackService.charge_card') as pcc:
            
            pcc.return_value = failure_response # define return values
            resp, deposit = activate_safelock_deposit(safelock.id, 'reference', 1000)    
       
        # assertions
        self.assertEqual(resp, failure_response['message'])