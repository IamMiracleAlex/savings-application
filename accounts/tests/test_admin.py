from django.test import TestCase
from django.contrib.admin.sites import AdminSite

from users.models import CustomUser
from accounts.models import Account
from accounts import admin





class AccountAdminTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(phone_number='2348026043569', 
                            password='password123', email='example@gmail.com',
                            first_name='Miracle', last_name='Alex')
        cls.account = Account.objects.filter(user=cls.user).first()

        '''Instantiate admin site'''
        
        cls.site = AdminSite() # instantiate admin
        cls.account_admin = admin.AccountAdmin(Account, cls.site) # instantiate acc admin

    def test_get_email(self):
        '''test get_email() method'''

        result = self.account_admin.get_email(self.account)
        self.assertIn(self.user.email, result)

    def test_get_phone_number(self):
        '''get_phone_number() method test'''

        result = self.account_admin.get_phone_number(self.account)
        self.assertEqual(result, self.user.phone_number)

