from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from users.models import CustomUser




class ListAccountsViewTest(APITestCase):   

    @classmethod
    def setUpTestData(cls):
        cls.data = { 
            'phone_number': '2348026043569',
            'password': '@password123',
            'email': 'email@example.com'
        }     
        cls.url = reverse('accounts:accounts')
        cls.user = CustomUser.objects.create_user(**cls.data)

    def test_get_list_accounts(self):
        '''assert that list accounts works'''
       
        self.client.force_authenticate(self.user)
        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['message'], 'Success')



class GetAccountViewTest(APITestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.data = { 
            'phone_number': '2348026043569',
            'password': '@password123',
            'email': 'email@example.com'
        }     
        cls.user = CustomUser.objects.create_user(**cls.data)

    def test_get_accounts_wallets(self):
        '''assert that get accounts works for wallets'''
        
        self.client.force_authenticate(self.user)

        # the reverse() args takes in the type of account
        wallet_url = reverse('accounts:account', args=['WALLET'])
        resp = self.client.get(wallet_url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['message'], 'Success')

    def test_get_accounts_deposits(self):
        '''assert that get accounts works for wallets'''
        
        self.client.force_authenticate(self.user)
        deposit_url = reverse('accounts:account', args=['DEPOSIT'])
        resp = self.client.get(deposit_url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['message'], 'Success')

    def test_get_accounts_direct(self):
        '''assert that get accounts works for wallets'''
        
        self.client.force_authenticate(self.user)
        direct_url = reverse('accounts:account', args=['DIRECT'])
        resp = self.client.get(direct_url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['message'], 'Success')
