import datetime

from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework import status, serializers

from users.models import CustomUser
from accounts.models import Account
from subscriptions.models import Subscription



class SubscriptionsSerializerTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user_data = {'phone_number': '08026043569',
                        'password': 'password123',
                        'email': 'email@gmail.com'}
        cls.user = CustomUser.objects.create_user(**cls.user_data)
        cls.account = cls.user.account_set.get(type_of_account=Account.DIRECT)
     
        cls.sub_data = {'name': 'house',
                        'amount': 200,
                        'interval': 'week',
                        'start_date': datetime.date.today()
                }             
        cls.create_url = reverse('subscriptions:subscriptions', 
                        args=['direct']
                        )
    def test_validate(self):
        '''assert the validate method validates subscriptions'''

        '''CASE 1: Assert that we can't make a subscription without a CARD'''
       
        self.client.force_authenticate(self.user)
        resp = self.client.post(self.create_url, data=self.sub_data)

        # assert that error was raised, and was actually due to absence of card
        self.assertRaises(serializers.ValidationError)
        self.assertEqual(resp.status_code,  status.HTTP_400_BAD_REQUEST)
        self.assertIn('Please add a card to proceed', 
                            resp.data['message']['non_field_errors'][0])


        '''CASE 2: Assert that we can't make a subscription when there is an
        an initial subscription'''

        self.sub_data['interval'] = Subscription.WEEKLY
        self.sub_data['account'] = self.account
        Subscription.objects.create(**self.sub_data)

        resp = self.client.post(self.create_url, data=self.sub_data)

        # assert that error was raised, and was because of initial subscription
        self.assertRaises(serializers.ValidationError)
        self.assertEqual(resp.status_code,  status.HTTP_400_BAD_REQUEST)
        self.assertIn('already exists for user', 
                            resp.data['message']['non_field_errors'][0])


    def test_validate_start_date(self):

        '''Assert that we CAN'T use a start date from the past'''

        # set a date from the past
        self.sub_data['start_date'] = datetime.date.today() - datetime.timedelta(days=3)

        self.client.force_authenticate(self.user)
        resp = self.client.post(self.create_url, data=self.sub_data)

        # assert that error was raised, and was because of a past date
        self.assertRaises(serializers.ValidationError)
        self.assertEqual(resp.status_code,  status.HTTP_400_BAD_REQUEST)
        self.assertIn('Date cannot be in the past', 
                            resp.data['message']['start_date'][0])


    def test_update(self):
        '''Assert that serilizers update's data as required'''

        # create a subscription
        self.sub_data['interval'] = Subscription.WEEKLY
        self.sub_data['account'] = self.account
        subscription = Subscription.objects.create(**self.sub_data)

        # prepare url, payload, and make request
        update_url = reverse('subscriptions:subscription', 
                        args=['direct']
                        )
        self.sub_data['interval'] = 'Monthly'
        self.sub_data['id'] = subscription.id

        self.client.force_authenticate(self.user)
        resp = self.client.put(update_url, data=self.sub_data)

        # assert that request was succesful, and data was updated
        self.assertEqual(resp.status_code,  status.HTTP_200_OK)
        self.assertEqual(resp.data['message'],
                            'Direct debit has beeen successfully updated')
        self.assertEqual(resp.data['data']['interval'], self.sub_data['interval'])                    


    def test_returned_data(self):
        '''Assert that subscription data are returned accurately'''

        # create a subscription
        self.sub_data['interval'] = Subscription.WEEKLY
        self.sub_data['account'] = self.account
        Subscription.objects.create(**self.sub_data)

        # prepare url, and make request
        get_sub_url = reverse('subscriptions:subscription', 
                        args=['direct']
                        )
        self.client.force_authenticate(self.user)
        resp = self.client.get(get_sub_url)

        # assert that request was succesful, and data was returned
        self.assertEqual(resp.status_code,  status.HTTP_200_OK)
        self.assertEqual(resp.data['message'], 'Success')
        self.assertEqual(resp.data['data'][0]['name'], self.sub_data['name'])  
