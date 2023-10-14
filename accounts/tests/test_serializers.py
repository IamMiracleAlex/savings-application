from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APITestCase

from users.models import CustomUser
from accounts.models import Account



class AccountSerializerTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.data = {'phone_number':'08026043569', 'password':'password123',
                'email': 'email@gmail.com', 'first_name':'Miracle', 'last_name':'Alex'}
        cls.user = CustomUser.objects.create_user(**cls.data)
        cls.url = reverse('accounts:accounts')

    def test_account_serializer(self):
        '''assert that the account serializer returns the required data'''

        acc_data = {'balance':200.00, 'interest':30.00,
                'last_interest_withdrawal_day': timezone.now() }
        self.client.force_authenticate(self.user)

        accounts = Account.objects.filter(user=self.user)
        accounts.update(**acc_data)

        resp = self.client.get(self.url)

        # get wallet acc returned data, you can get for others
        expected = resp.data['data']['WALLET']

        self.assertIsNotNone(expected['balance'])
        self.assertIsNotNone(expected['interest'])
        self.assertFalse(expected['interest_active'])
        self.assertIsNotNone(expected['created_at'])
        self.assertIsNotNone(expected['updated_at'])
