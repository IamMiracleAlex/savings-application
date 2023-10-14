import datetime

from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework import status, serializers

from users.models import CustomUser
from deposits.models.fund_source import FundSource




class AddCardViewTest(APITestCase):

    def setUp(self):
        self.user_data = {'phone_number': '08026043569',
                        'password': 'password123',
                        'email': 'email@gmail.com'}
        self.user = CustomUser.objects.create_user(**self.user_data)
        
        # load data
        self.add_card_data = {
                    'amount': 100,
                    'reference': 'reference' ,
                    }
        self.url = reverse('paystack_addcard')
        
    
    def test_post(self):
        '''test that post method works'''

        self.client.force_authenticate(self.user)
        resp = self.client.post(self.url, self.add_card_data)
        
        # assertions
        self.assertEqual(resp.status_code,  status.HTTP_200_OK)
        self.assertIn('Card would be added shortly if transaction was successful', 
                            resp.data['message'])



class RetrieveFundSourceViewTest(APITestCase):

    def setUp(self):
        self.user_data = {'phone_number': '08026043569',
                        'password': 'password123',
                        'email': 'email@gmail.com'}
        self.user = CustomUser.objects.create_user(**self.user_data)
        self.url = reverse('fund_sources')
        
    
    def test_get(self):
        '''test that get method works'''

        fs = { 'user': self.user,'last4': '4444',
                'bank_name': 'American', 'card_type': 'visa',
                'exp_month': '09', 'exp_year': '2024',
                'is_active': True }

        FundSource.objects.create(**fs) 
        self.client.force_authenticate(self.user)
        resp = self.client.get(self.url)
        
        # assertions
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['data'][0]['last4'], fs['last4'])
        self.assertEqual(resp.data['data'][0]['bank_name'], fs['bank_name'])
        self.assertEqual(resp.data['data'][0]['card_type'], fs['card_type'])
        self.assertEqual(resp.data['data'][0]['exp_year'], fs['exp_year'])
        

class ChangeDefaultFundSourceTest(APITestCase):

    def setUp(self):
        self.user_data = {'phone_number': '08026043569',
                        'password': 'password123',
                        'email': 'email@gmail.com'}
        self.user = CustomUser.objects.create_user(**self.user_data)
        
        self.url = reverse('default_fund_source')
        
    
    def test_post(self):
        '''test that post method works'''

        ''' CASE 1 -  When fund source DOES NOT exist'''
       
        self.data = {
                    'fund_source_id': 1,
                    }
        self.client.force_authenticate(self.user)
        resp = self.client.post(self.url, self.data)
        
        # assertions
        self.assertEqual('Fund Source does not exist', resp.data['message'])

        ''' CASE 2 -  When fund source exists'''

        fs = { 'user': self.user, 'last4': '4444',
            'bank_name': 'American', 'card_type': 'visa',
            'exp_month': '09', 'exp_year': '2024',
            'is_active': True }
        fund_sc = FundSource.objects.create(**fs) 

        self.data = {
                'fund_source_id': fund_sc.id,
                }
        self.client.force_authenticate(self.user)
        resp = self.client.post(self.url, self.data)
        
        self.assertEqual('Successfully set default fund source', resp.data['message'])


   