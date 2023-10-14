import datetime

from django.test import TestCase

from safelocks.models import SafeLock
from transactions.models import Transaction
from users.models import CustomUser


class SafelockModelTest(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.user_data = {   'phone_number':'2348026043569', 
                            'password':'password123',
                            'email':'miracle@savests.com',
                            'first_name':'Miracle',
                            'last_name':'Alex'}
        cls.user = CustomUser.objects.create_user(**cls.user_data)
        cls.account = cls.user.account_set.first()
        
        # load data and create safelock
        cls.safe_data = {'account': cls.account,
                    'name': 'invest',
                    'amount': 200,
                    'interest': 20.0,
                    'target_goal': 1000000,
                    'category': SafeLock.Investment,
                    'maturity_date': datetime.date.today() + datetime.timedelta(days=100)
                    }
        cls.safelock = SafeLock.objects.create(**cls.safe_data)

    def test_safelock_creation(self):
        '''Assert that safelock was created, after filling in an account
        and other details.
        '''
       
        self.assertIsNotNone(self.safelock.account)
        self.assertEqual(self.safelock.name, self.safe_data['name'])
        self.assertEqual(self.safelock.interest, self.safe_data['interest'])
        self.assertEqual(self.safelock.amount, self.safe_data['amount'])
        self.assertIsNotNone(self.safelock.maturity_date)


    def test_activate(self):
        '''Assert that activate() works'''

        # activate and refresh
        self.safelock.activate()
        self.safelock.refresh_from_db()

        # assert it is activated
        self.assertTrue(self.safelock.is_active)


    def test_create_deposit(self):
        '''Assert that create_deposit() works as expected'''

        # create deposit
        self.safelock.create_deposit(None, self.safe_data['amount'])

        # get the trans and assert deposit was created
        trans = Transaction.objects.get(account=self.account)
        
        self.assertEqual(trans.amount, self.safe_data['amount'])
        self.assertEqual(trans.data['type_of_deposit'], 'TermDeposit')
        self.assertTrue(trans.status)