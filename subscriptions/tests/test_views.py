import datetime

from unittest.mock import patch

from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework import status

from users.models import CustomUser
from accounts.models import Account
from subscriptions.models import Subscription
from deposits.models import FundSource
from safelocks.models import SafeLock
from subscriptions.views import activate_subscription


class CreateSubscriptionsTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user_data = {'phone_number': '08026043569',
                        'password': 'password123',
                        'email': 'miracle@savests.com'}
        cls.user = CustomUser.objects.create_user(**cls.user_data)
        cls.account = cls.user.account_set.get(type_of_account=Account.DIRECT)
     
        # subscription data
        cls.sub_data = {'name': 'house',
                        'amount': 200,
                        'interval': 'weekly',
                        'start_date': datetime.date.today()
                }  
        # fund source        
        cls.fs = FundSource.objects.create(user=cls.user, last4='4444',
                            bank_name='American', card_type='visa', 
                            exp_month='09', exp_year='2024',
                            is_active=True) 

        # create a default fs                    
        cls.user.default_deposit_fund_source = cls.fs
        cls.user.save()

    def test_post(self):
        '''Assert that the post method creates a subscription successfully'''

        create_url = reverse('subscriptions:subscriptions', 
                        args=['direct']
                        )
        self.client.force_authenticate(self.user)
        resp = self.client.post(create_url, data=self.sub_data)

        # assert that sub was succesful, 
        self.assertEqual(resp.status_code,  status.HTTP_200_OK)
        self.assertIn('debits has been activated on your account', resp.data['message'])



class RetrieveUpdateSubscriptionsTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user_data = {'phone_number': '08026043569',
                        'password': 'password123',
                        'email': 'miracle@savests.com'}
        cls.user = CustomUser.objects.create_user(**cls.user_data)
        cls.account = cls.user.account_set.get(type_of_account=Account.DIRECT)
     
        # subscription data
        cls.sub_data = {'name': 'house',
                        'amount': 200,
                        'interval': 'weekly',
                        'start_date': datetime.date.today()
                }

        cls.get_put_url = reverse('subscriptions:subscription', 
                        args=['direct']
                        )          

    def test_get(self):
        '''Assert that the get method gets a subscription successfully'''
   
        # create a subscription
        self.sub_data['interval'] = Subscription.WEEKLY
        self.sub_data['account'] = self.account
        Subscription.objects.create(**self.sub_data)

        # make request
        self.client.force_authenticate(self.user)
        resp = self.client.get(self.get_put_url)

        # assert that request was succesful, and data was returned
        self.assertEqual(resp.status_code,  status.HTTP_200_OK)
        self.assertEqual(resp.data['message'], 'Success')
        self.assertEqual(resp.data['data'][0]['name'], self.sub_data['name'])


    def test_put(self):
        '''Assert that the put method works'''

        # create a subscription
        self.sub_data['interval'] = Subscription.WEEKLY
        self.sub_data['account'] = self.account
        subscription = Subscription.objects.create(**self.sub_data)

        # update sub data
        self.sub_data['interval'] = 'Monthly'
        self.sub_data['id'] = subscription.id

        self.client.force_authenticate(self.user)
        resp = self.client.put(self.get_put_url, data=self.sub_data)
       
        # assert that request was succesful, and data was updated
        self.assertEqual(resp.status_code,  status.HTTP_200_OK)
        self.assertEqual(resp.data['message'],
                            'Direct debit has beeen successfully updated')
        self.assertEqual(resp.data['data']['interval'], self.sub_data['interval'])                    


class EnableDisableSubscriptionsTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user_data = {'phone_number': '08026043569',
                        'password': 'password123',
                        'email': 'miracle@savests.com'}
        cls.user = CustomUser.objects.create_user(**cls.user_data)
        cls.account = cls.user.account_set.get(type_of_account=Account.DIRECT)
     
        # subscription data
        cls.sub_data = {'name': 'house',
                        'amount': 200,
                        'interval': Subscription.WEEKLY,
                        'start_date': datetime.date.today(),
                        'account': cls.account,
                        'previous_paydate': datetime.date.today() - datetime.timedelta(days=30)
                }
        cls.sub = Subscription.objects.create(**cls.sub_data)


    def test_enable_subscription(self):
        '''Assert that subscriptions are enabled when this view is called'''

        # enable sub url, payload and request
        enable_sub_url = reverse('subscriptions:enable_subscription', 
                    args=['direct']
                        )   
        data = {'id': self.sub.id }                
        self.client.force_authenticate(self.user)
        resp = self.client.post(enable_sub_url, data=data)
       
        # assert that request was succesful, and subscription was enabled
        self.assertEqual(resp.status_code,  status.HTTP_200_OK)
        self.assertEqual(resp.data['message'],
                            'Your Subscription has been enabled')
        self.assertTrue(resp.data['data']['is_active'])


    def test_disable_subscription(self):
        '''Assert that subscriptions are disabled when this view is called'''

        # disable sub url, payload and request
        disable_sub_url = reverse('subscriptions:disable_subscription', 
                    args=['direct']
                        )   
        data = {'id': self.sub.id }                
        self.client.force_authenticate(self.user)
        resp = self.client.post(disable_sub_url, data=data)
       
        # assert that request was succesful, and subscription was disabled
        self.assertEqual(resp.status_code,  status.HTTP_200_OK)
        self.assertEqual(resp.data['message'],
                            'Your Subscription has been disabled')
        self.assertFalse(resp.data['data']['is_active'])



class ActivateSubscription(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user_data = {'phone_number': '08026043569',
                        'password': 'password123',
                        'email': 'miracle@savests.com'}
        cls.user = CustomUser.objects.create_user(**cls.user_data)
        cls.account = cls.user.account_set.get(type_of_account=Account.DIRECT)

        cls.success_response = { # define return values for success
                'status': True,
                'message':  'deposit successful',
                'data':  {'status': 'success'}
            }
        cls.failure_response = { # define return values for failures
                'status': False,
                'message':  'deposit failed',
                'data':  {'status': 'failure'}
            } 


    def test_activate_subscription(self):

        # subscription data
        fs = FundSource.objects.create(user=self.user, last4='4444',
                            bank_name='American', card_type='visa', 
                            exp_month='09', exp_year='2024',
                            is_active=True) 

        sub_data = {'name': 'house',
                        'amount': 200,
                        'interval': Subscription.WEEKLY,
                        'start_date': datetime.date.today(),
                        'account': self.account,
                        'fund_source': fs
                }
        sub = Subscription.objects.create(**sub_data)
         
        # load data and create safelock
        safe_data = {'account': self.account,
                    'name': 'invest',
                    'amount': 200,
                    'interest': 20.0,
                    'target_goal': 1000000,
                    'category': SafeLock.Investment,
                    'maturity_date': datetime.date.today() + datetime.timedelta(days=100),
                    'subscription': sub
                    }
        SafeLock.objects.create(**safe_data)

        '''case 1, when paystack endpoint works''' #edit this

        with patch('subscriptions.views.PaystackService.charge_card') as pcc:
            
            pcc.return_value = self.success_response # define return values
            resp = activate_subscription(sub.id)    

        # assertions
        self.assertTrue(resp)
