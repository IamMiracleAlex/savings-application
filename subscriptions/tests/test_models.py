import datetime

from django.test import TestCase

from subscriptions.models import Subscription
from deposits.models import FundSource
from transactions.models import Transaction
from users.models import CustomUser


class SubscriptionModelTest(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.user_data = {   'phone_number':'2348026043569', 
                            'password':'password123',
                            'email':'miracle@savests.com',
                            'first_name':'Miracle',
                            'last_name':'Alex'}
        cls.user = CustomUser.objects.create_user(**cls.user_data)
        cls.account = cls.user.account_set.first()

        # create a fs instance
        cls.fs = FundSource.objects.create(user=cls.user, last4='4444',
                            bank_name='American', card_type='visa', 
                            exp_month='09', exp_year='2024',
                            is_active=True) 
        
        # load sub and create subscription
        today = datetime.date.today()
        cls.sub_data = {'account': cls.account,
                    'interval': Subscription.WEEKLY,
                    'amount': 200,
                    'next_paydate': today + datetime.timedelta(days=30),
                    'previous_paydate': today - datetime.timedelta(days=31),
                    'start_date': today,
                    'fund_source': cls.fs
                    }
        cls.sub = Subscription.objects.create(**cls.sub_data)

    def test_subscription_creation(self):
        '''Assert that subscription was created, after filling in an account
        and other details.
        '''
       
        self.assertIsNotNone(self.sub.account)
        self.assertEqual(self.sub.start_date, self.sub_data['start_date'])
        self.assertEqual(self.sub.interval, 
                         self.sub_data['interval'])
        self.assertEqual(self.sub.amount, self.sub_data['amount'])
        self.assertIsNotNone(self.sub.next_paydate)
        self.assertIsNotNone(self.sub.previous_paydate)


    def test_user(self):
        '''Assert user() function works'''

        # assert that user() generates the accurate user
        self.assertEqual(self.user, self.sub.user())


    def test_auth(self):
        '''Assert auth() works'''

        # assert that auth() generates the fs code
        self.assertEqual(self.fs.auth_code, self.sub.auth())

    def test_enable(self):
        '''Assert that enable() works'''

        # enable and refresh
        self.sub.enable()
        self.sub.refresh_from_db()

        # assert it is enabled
        self.assertTrue(self.sub.is_active)

    def test_disable(self):
        '''Assert that disable() works'''

        # disable and refresh
        self.sub.disable()
        self.sub.refresh_from_db()

        # assert it is disabled
        self.assertFalse(self.sub.is_active)

    def set_next_paydate(self):
        '''Assert that next_paydate() works'''
        
        # call the function
        self.sub.set_next_paydate()
        self.sub.refresh_from_db()

        # assert that the next_paydate was set
        self.assertNotEqual(self.sub_data['next_paydate'], self.sub.next_paydate)

    def test_create_deposit(self):
        '''Assert that create_deposit() works as expected'''

        # create deposit
        self.sub.create_deposit()

        # get the trans and assert deposit was created
        trans = Transaction.objects.get(account=self.account)
        self.assertEqual(trans.amount, self.sub_data['amount'])
        self.assertEqual(trans.data['fund_source_id'], self.fs.id)
        self.assertEqual(trans.data['subscription_id'], self.sub.id)
        self.assertEqual(trans.data['type_of_deposit'], 'AutoSave')
       