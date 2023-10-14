from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework import status

from users.models import CustomUser
from deposits.models.fund_source import FundSource
from accounts.models import Account
from subscriptions.models import Subscription
from safelocks.models import SafeLock
from kyc_profiles.models import KYCProfile



class UserSerializerTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.data = {'phone_number':'08026043569', 'password':'password123',
                'email': 'email@gmail.com', 'first_name':'Miracle', 'last_name':'Alex'}
        cls.user = CustomUser.objects.create_user(**cls.data)
        cls.url = reverse('users:users')

    def test_get_fundsources(self):
        '''assert that the fundsource data is returned by the serializer as required'''

        fund_data = {'user':self.user,'last4':'4444','bank_name':'Providus','card_type':'visa',
                                'auth_code':'code', 'exp_month':'07','exp_year':'2020', 'is_active':True }
        self.client.force_authenticate(self.user)
        FundSource.objects.create(**fund_data) # create fundsource obj
        resp = self.client.get(self.url) # call endpoint
        expected = resp.data['data']['fund_sources'][0]

        # check returned data match given data
        self.assertEqual(fund_data['last4'], expected['last4'])
        self.assertEqual(fund_data['bank_name'], expected['bank_name'])
        self.assertEqual(fund_data['card_type'], expected['card_type'])
        self.assertEqual(fund_data['exp_month'], expected['exp_month'])
        self.assertEqual(fund_data['exp_year'], expected['exp_year'])

    def test_get_transactions(self):
        '''assert that get transactions return the required data'''

        self.client.force_authenticate(self.user)
        resp = self.client.get(self.url)
        expected = resp.data['data']['transactions']

        self.assertFalse(expected) # trans data is empty

    def test_get_subscriptions(self):
        '''assert that the serializer returns subscriptions as required'''

        self.client.force_authenticate(self.user)

        # subscriptions require a direct acct.
        direct_account = Account.objects.get(user=self.user, type_of_account=Account.DIRECT)
        sub_data = {'account':direct_account,
                    'amount':300, 'interval':Subscription.DAILY,
                    'start_date':'2020-07-30'}
        Subscription.objects.create(**sub_data)
        resp = self.client.get(self.url)
        expected = resp.data['data']['subscription']

        # returned sub data matches parsed
        self.assertEqual(expected['amount'], sub_data['amount'])
        self.assertEqual(expected['interval'], 'Daily')
        self.assertEqual(expected['start_date'], sub_data['start_date'])
        self.assertIsNotNone(expected['created_at'])
        self.assertTrue(expected['account']['interest_active'])

    def test_get_safelocks(self):
        '''assert that the serializers return safelocks as required'''

        self.client.force_authenticate(self.user)

        # deposits accounts for safelocks
        deposit_account = Account.objects.get(user=self.user, type_of_account=Account.DEPOSIT)
        safe_data = {'name':'Business', 'account':deposit_account,
                    'amount':3000, 'maturity_date':'2020-07-30',
                    'category':SafeLock.Business, 'is_active':True}
        SafeLock.objects.create(**safe_data)
        resp = self.client.get(self.url)
        expected = resp.data['data']['safelocks'][0]

        # returned safelocks data matches parsed
        self.assertEqual(expected['amount'], safe_data['amount'])
        self.assertEqual(expected['name'], safe_data['name'])
        self.assertEqual(expected['maturity_date'], safe_data['maturity_date'])
        self.assertIsNotNone(expected['created_at'])

    def test_get_accounts(self):
        '''assert that all user accounts are returned'''

        self.client.force_authenticate(self.user)
        resp = self.client.get(self.url)
        expected = resp.data['data']['accounts']

        # assert that user accounts are returned
        self.assertIsNotNone(expected)

    def test_get_referrals(self):
        '''assert that the created referrlas are returned by the serializers'''

        refer_code = self.user.refer_code
        new_user_data = {'phone_number':'07069179050', 'password':'password123',
                         'refer_code': refer_code }
        # create a new user with a referal code, so there's a referral               
        new_user = self.client.post(reverse('users:register'), new_user_data, format='json')

        self.assertEqual(new_user.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(self.user)
        resp = self.client.get(self.url)
        expected = resp.data['data']['referrals']

        self.assertTrue(expected) # assert that there is a referral

    def test_get_kyc_profile(self):

        self.client.force_authenticate(self.user)
        kyc_data = {'bvn':'1234567890',
                    'name':'Miracle Alex', 'phone_number':'08026043569',
                    'dob':'2020-07-30'}

        # get and update kyc profile            
        kyc_profile = KYCProfile.objects.filter(user=self.user)
        kyc_profile.update(**kyc_data)            
        resp = self.client.get(self.url)
        expected = resp.data['data']['kyc_profile']

        # assert that data returned is same as parsed
        self.assertEqual(expected['bvn'], kyc_data['bvn'])
        self.assertEqual(expected['phone_number'], kyc_data['phone_number'])
        self.assertEqual(expected['dob'], kyc_data['dob'])
        self.assertEqual(expected['name'], kyc_data['name'])
        self.assertIsNotNone(expected['created_at'])

    def test_get_default_deposit_fund_source(self):
        '''assert that all user default deposit fund sources are returned'''

        self.client.force_authenticate(self.user)
        resp = self.client.get(self.url)
        expected = resp.data['data']['default_deposit_fund_source']

        self.assertIsNone(expected)  

    def test_get_default_withdraw_beneficiary(self):
        '''assert that all user default withdraw beneficiary are returned'''

        self.client.force_authenticate(self.user)
        resp = self.client.get(self.url)
        expected = resp.data['data']['default_withdraw_beneficiary']

        self.assertIsNone(expected)  