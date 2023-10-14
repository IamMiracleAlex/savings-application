from django.test import TestCase
from django.utils import timezone

from transactions.models import (Transaction, notify_firebase_failed,
                                notify_firebase_failed, notify_transaction_success,
                                notify_firebase_success,
                                pusher_update )
from utils.choices import Transaction as TransactionOptions
from users.models import CustomUser
from accounts.models import Account


class TransactionModelTest(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.user_data = { 'phone_number':'2348026043569', 
                            'password':'password123',
                            'email':'example@gmail.com',
                            'first_name':'Miracle',
                            'last_name':'Alex'}
        cls.user = CustomUser.objects.create_user(**cls.user_data)
        accounts = Account.objects.filter(user=cls.user)
        data = {'balance':500, 'interest':30,
                'last_interest_withdrawal_day': timezone.now() }
        accounts.update(**data)
        cls.account = Account.objects.filter(user=cls.user).first()
 

    def test_transaction_creation(self):
        '''assert that transaction was created, after filling in an account and other default details.
        Assert that fields have correct values and reference was generated.
        However, to create a transaction, we need a user and an account.'''

        trans_data = {'account':self.account,
                    'type_of_transaction':TransactionOptions.Deposit,
                    'status':TransactionOptions.SUBMITTED,
                    'amount': 200,
                    'balance_after_transaction': 200,
                    'fee': 100,
                    'memo': 'deposit',
                    }
        transaction = Transaction.objects.create(**trans_data)

        self.assertIsNotNone(transaction.reference)
        self.assertEqual(transaction.account, trans_data['account'])
        self.assertEqual(transaction.type_of_transaction, 
                            trans_data['type_of_transaction'])
        self.assertEqual(transaction.amount, trans_data['amount'])
        self.assertEqual(transaction.balance_after_transaction,
                            trans_data['balance_after_transaction'])
        self.assertEqual(transaction.memo, trans_data['memo'])
        self.assertEqual(transaction.fee, trans_data['fee'])
        self.assertIsNotNone(transaction.created_at)
        self.assertIsNotNone(transaction.updated_at)

    def test_minimum_validator(self):
        '''Though the 'minimun validator' works in the admin, it does not work in the console.
        Assert that the minimum validator works using the objects manager.
        
        N/B: Because this test passes, the minimum validator does not work using the 
        object manager, except we use the full_clean() method before save''' 

        trans_data = {'account':self.account,
                    'type_of_transaction':TransactionOptions.Deposit,
                    'status':TransactionOptions.SUBMITTED,
                    'amount': -200,
                    'balance_after_transaction': -200,
                    'fee': 100,
                    'memo': 'deposit',
                    }
        transaction = Transaction.objects.create(**trans_data)


        self.assertEqual(transaction.amount, trans_data['amount'])
        self.assertEqual(transaction.balance_after_transaction,
                            trans_data['balance_after_transaction'])

    def test_reject(self):
        '''assert that the reject() method works on the transaction model
        and that transaction status is changed'''

        # status of 'SUBMITTED' 

        trans_data = {'account':self.account,
                    'type_of_transaction':TransactionOptions.Withdraw,
                    'status':TransactionOptions.SUBMITTED,
                    'reference': 'qwerty',
                    'amount': 200,
                    'balance_after_transaction': 200,
                    'fee': 100,
                    'memo': 'deposit',
                    }
        transaction = Transaction.objects.create(**trans_data)
        transaction.reject() # call the method on trans

        # status of 'FAILED'

        self.assertEqual(transaction.status, TransactionOptions.FAILED)
       

    def test_process(self):
        '''assert that process() method works on the transaction model
        and that transaction status is changed. The balance after transaction is 
        equal to the account balance'''

        # type of trans is deposit

        trans_data = {'account':self.account,
                    'type_of_transaction':TransactionOptions.Deposit,
                    'reference': 'qwerty',
                    'amount': 200,
                    'balance_after_transaction': 200,
                    'fee': 100,
                    'memo': 'deposit',
                    }
        transaction = Transaction.objects.create(**trans_data)
        transaction.process() #method call

        self.assertEqual(transaction.status, TransactionOptions.PROCESSING)
        self.assertEqual(transaction.balance_after_transaction, self.account.balance)

    def test_succeed(self):
        '''assert that succeed() method works on the transaction model
        and that transaction status is changed. The balance after transaction is 
        equal to the account balance'''

        # type of trans is 'Deposit', status is at initial stage

        trans_data = {'account':self.account,
                    'type_of_transaction':TransactionOptions.Deposit,
                    'amount': 200,
                    'balance_after_transaction': 200,
                    'fee': 100,
                    'memo': 'deposit',
                    'data': {'type_of_deposit':TransactionOptions.TermDeposit}
                    }
        transaction = Transaction.objects.create(**trans_data)
        transaction.succeed()  # call the method on trans

        # status change, and balance reflected

        self.assertEqual(transaction.status, TransactionOptions.SUCCESS)
        self.assertEqual(transaction.balance_after_transaction, self.account.balance)

        '''Assert that the succeed method works for interests and transfers and adds the 
        transaction amount to the destination account balance on this transactions.'''

        # change old user data for new user

        new_user_data = self.user_data.copy()
        new_user_data['phone_number'] = '07069179050'
        new_user_data['email'] = 'example@yahoo.com'
        new_user = CustomUser.objects.create_user(**new_user_data)

        # get new user acc, and create new user trans
        new_account = Account.objects.filter(user=new_user).first()
        trans_data['type_of_transaction'] = TransactionOptions.Transfer  
        trans_data['dest_account'] = new_account 
        new_trans = Transaction.objects.create(**trans_data)

        # call method and refresh data
        new_trans.succeed() 

        new_account.refresh_from_db()

        self.assertEqual(transaction.status, TransactionOptions.SUCCESS)
        self.assertEqual(transaction.data['dest_account_balance_after_transaction'], new_account.balance)




class NotifyTransactionsTest(TestCase):

     
    def setUp(self):
        self.user = CustomUser.objects.create_user(phone_number='2348026043569', 
                            password='password123', email='collinsalex50@gmail.com',
                            first_name='Miracle', last_name='Alex')
        accounts = Account.objects.filter(user=self.user)
        data = {'balance':500, 'interest':30,
                'last_interest_withdrawal_day': timezone.now() }
        accounts.update(**data)
        self.account = Account.objects.filter(user=self.user).first()



    def notify_transaction_failures(self):
        '''assert that the notify_transaction_failed() method and notify_firebase_failed() works'''

        trans_data = {'account':self.account,
                'type_of_transaction':TransactionOptions.Withdraw,
                'status':TransactionOptions.SUBMITTED,
                'reference': 'qwerty',
                'amount': 200,
                'balance_after_transaction': 200,
                'fee': 100,
                'memo': 'deposit',
                }
        transaction = Transaction.objects.create(**trans_data)
        transaction.reject()
        resp = notify_firebase_failed(transaction)
        firebase = notify_firebase_failed(transaction)

        self.assertTrue(resp)
        self.assertTrue(firebase)


    def notify_transaction_successful(self):
        '''assert that the notify_transaction_success() method and notify_firebase_success() works'''

        trans_data = {'account':self.account,
                    'type_of_transaction':TransactionOptions.Deposit,
                    'amount': 200,
                    'balance_after_transaction': 200,
                    'fee': 100,
                    'memo': 'deposit',
                    'data': {'type_of_deposit':TransactionOptions.TermDeposit}
                    }
        transaction = Transaction.objects.create(**trans_data)
        transaction.succeed()
        resp = notify_transaction_success(transaction)
        firebase = notify_firebase_success(transaction)

        self.assertTrue(resp)
        self.assertTrue(firebase)


    def test_pusher_update(self):
        '''assert that the pusher_update() function works'''

        trans_data = {'account':self.account,
                    'type_of_transaction':TransactionOptions.Deposit,
                    'amount': 200,
                    'balance_after_transaction': 200,
                    'fee': 100,
                    'memo': 'deposit',
                    'data': {'type_of_deposit':TransactionOptions.TermDeposit}
                    }
        transaction = Transaction.objects.create(**trans_data)
        transaction.succeed()
        pusher = pusher_update(transaction)

        self.assertTrue(pusher)
