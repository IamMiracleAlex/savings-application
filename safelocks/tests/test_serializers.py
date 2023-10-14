import datetime

from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework import status, serializers

from users.models import CustomUser
from accounts.models import Account
from safelocks.models import SafeLock
from subscriptions.models import Subscription



class SafeLockSerializerTest(APITestCase):

    def setUp(self):
        self.user_data = {'phone_number': '08026043569',
                        'password': 'password123',
                        'email': 'email@gmail.com'}
        self.user = CustomUser.objects.create_user(**self.user_data)
        self.account = self.user.account_set.get(type_of_account=Account.DEPOSIT)
    
        # load data and create safelock
        self.safe_data = {
                    'name': 'invest',
                    'amount': 1000,
                    'target_goal': 1000000,
                    'category': 'car',
                    'reference': 'reference' ,
                    'transfer_from': 'wallet' ,
                    'maturity_date': datetime.date.today() + datetime.timedelta(days=100),
                    }
        self.create_url = reverse('safelocks:safelocks')

    def test_maturity_date(self):
        '''Assert that we CAN'T use a maturity date less than 30 days'''

        # Set a maturity date less than 30
        self.safe_data['maturity_date'] = datetime.date.today()

        self.client.force_authenticate(self.user)
        resp = self.client.post(self.create_url, data=self.safe_data)

        # assert error was raised, and was because of days lower than 30
        self.assertRaises(serializers.ValidationError)
        self.assertEqual(resp.status_code,  status.HTTP_400_BAD_REQUEST)
        self.assertIn('date must exceed at least 30 days in the future', 
                            resp.data['message']['maturity_date'][0])


    def test_amount(self):
        '''Assert that we CAN'T use an amount less than 1000'''

        # set a low amount
        self.safe_data['amount'] = 800

        self.client.force_authenticate(self.user)
        resp = self.client.post(self.create_url, data=self.safe_data)

        # assert that error was raised, and was because of low amount
        self.assertRaises(serializers.ValidationError)
        self.assertEqual(resp.status_code,  status.HTTP_400_BAD_REQUEST)
        self.assertEqual('Minimum Term Deposit of 1000 Naira', 
                            resp.data['message']['amount'][0])

    def test_validate(self):
        '''test that validate method works'''

        '''CASE 1
         - Assert we CAN'T create a safelock with low balance,
          when we request from a wallet account.
         - We'll make this request with a zero balance in our account.
        '''
        # update data
        self.safe_data['amount'] = 10000
        self.safe_data['maturity_date'] = datetime.date.today() + datetime.timedelta(days=100)

        self.client.force_authenticate(self.user)
        resp = self.client.post(self.create_url, data=self.safe_data)

        # assert that error was raised, and was because of low balance
        self.assertRaises(serializers.ValidationError)
        self.assertEqual(resp.status_code,  status.HTTP_400_BAD_REQUEST)
        self.assertEqual('Insufficient Balance', 
                            resp.data['message']['non_field_errors'][0])


        '''CASE 2
         - Assert we CAN'T create a safelock without a default fund source,
          when we request from a card
         - We'll make this request without a default fund source
        '''                    

        self.safe_data['transfer_from'] = 'card'
        resp = self.client.post(self.create_url, data=self.safe_data)
        
        # assert that error was raised, and was because there's no card
        self.assertRaises(serializers.ValidationError)
        self.assertEqual(resp.status_code,  status.HTTP_400_BAD_REQUEST)
        self.assertIn('add a card', 
                            resp.data['message']['non_field_errors'][0])


    def test_retrieve_safelocks(self):
        '''Assert that safelocks are retrieved successfully'''   
                    
        retrieve_url = reverse('safelocks:safelocks')

        self.safe_data['category'] = SafeLock.Car
        self.safe_data['is_active'] = True
        self.safe_data['account'] = self.account

        del self.safe_data['reference']
        del self.safe_data['transfer_from']
        SafeLock.objects.create(**self.safe_data)

        self.client.force_authenticate(self.user)
        resp = self.client.get(retrieve_url)

        self.assertEqual(resp.status_code,  status.HTTP_200_OK)
        self.assertEqual(resp.data['message'],  'Success')
        self.assertEqual(resp.data['data'][0]['name'],  self.safe_data['name'])
