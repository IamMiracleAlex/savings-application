from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from accounts.models import Account
from users.models import CustomUser


class AccountModelTest(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(phone_number='2348026043569', 
                            password='password123', email='example@gmail.com',
                            first_name='Miracle', last_name='Alex')
                            

    def test_account_creation(self):
        '''assert that account was created when a user was created, and 
        accounts fields when updated return correct values correctly'''

        accounts = Account.objects.filter(user=self.user)

        # accounts created?
        self.assertIsNotNone(accounts)

        data = {'balance':200, 'interest':30,
                'last_interest_withdrawal_day': timezone.now() }
        accounts.update(**data)
        accounts = Account.objects.filter(user=self.user).first()

        # updated accts has correct values
        self.assertEqual(accounts.balance, data['balance'])
        self.assertEqual(accounts.interest, data['interest'])
        self.assertIsNotNone(accounts.last_interest_withdrawal_day)
        self.assertFalse(accounts.interest_active)
        self.assertIsNotNone(accounts.created_at)
        self.assertIsNotNone(accounts.updated_at)
        self.assertIsNotNone(accounts.public_id)

    def test_minimum_validator(self):
        '''Though the 'minimun validator' works in the admin, it does not work in the console.
        Assert that the minimum validator works using the objects manager.
        
        Because this test passes, the minimum validator does not work using the object manager''' 

        accounts = Account.objects.filter(user=self.user)

        data = {'balance': Decimal(-300.00), 'interest':-30,
                'last_interest_withdrawal_day': timezone.now() }
        accounts.update(**data)
        account = Account.objects.filter(user=self.user).first()

        self.assertEqual(account.balance, data['balance'])
        self.assertEqual(account.interest, data['interest'])
        
    def test_chicken_change_deposit(self):
        '''Assert that the chicken_change_deposit() works and confirm that 
        the amount is added to the account'''   


        accounts = Account.objects.filter(user=self.user)

        data = {'balance': 300.00, 'interest':30,
                'last_interest_withdrawal_day': timezone.now() }
        accounts.update(**data)
        account = Account.objects.filter(user=self.user).first()

        # call chicken change deposit()
        amount = 500
        account.chicken_change_deposit(self.user, amount)

        expected = data['balance'] + amount
        self.assertEqual(account.balance, expected)