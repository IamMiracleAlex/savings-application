from unittest.mock import patch

from rest_framework.test import APITestCase

from users.models import CustomUser
from transactions.models import Transaction
from utils.choices import Transaction as TransactionOptions
from deposits.models import FundSource


from transactions.helpers import (paystack_deposit, paystack_withdraw, ravepay_bills,
                                create_deposit)



class TransactionHelpersTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user_data = {'phone_number':'08026043569',
                    'password':'password123',
                    'email': 'miracle@savests.com'}
        cls.user = CustomUser.objects.create_user(**cls.user_data)
        cls.wallet_account = cls.user.account_set.first()
        cls.trans_data = {
                      'amount': 200,
                      'account': cls.wallet_account,
                      'data': {}
                    } 
        cls.success_response = { # define return values for success
                'status': True,
                'message':  'deposit successful',
                'data':  {'status': 'success'}
            }
        cls.failure_response = { # define return values for failures
                'status': False,
                'message':  'deposit failed',
                'data':  {'status': 'failure'}
            }  

        cls.fs = FundSource.objects.create(
                            user=cls.user, last4='4444',
                            bank_name='American', card_type='visa', 
                            exp_month='09', exp_year='2024',
                            is_active=True)    

    def test_paystack_deposit(self):
    
        ''' Assert that the paystack deposit function works for transactions '''

        # set up a transaction and fund source
        self.trans_data['type_of_transaction'] = TransactionOptions.Deposit
        self.trans_data['data'] = {'fund_source_id': self.fs.id,
                                'type_of_deposit': 'QuickSave'}

        transaction = Transaction.objects.create(**self.trans_data)


        '''CASE 1: 
            - When PaystackService.charge_card() is successful
        '''

        with patch('transactions.helpers.PaystackService.charge_card') as pcc:
           
            pcc.return_value = self.success_response # define return values
            message, _ = paystack_deposit(transaction.id)    

        # assertions
        self.assertEqual(message, self.success_response['message'])


        '''CASE 2: 
            - When PaystackService.charge_card() failed
        '''

        with patch('transactions.helpers.PaystackService.charge_card') as pcc:
           
            pcc.return_value = self.failure_response # define return values
            message, _ = paystack_deposit(transaction.id)    

        # assertions
        self.assertEqual(message, self.failure_response['message'])


    def test_paystack_withdraw(self):

        ''' Assert that the paystack withdraw function works for transactions '''

        # set up a transaction
        self.trans_data['type_of_transaction'] = TransactionOptions.Withdraw
        transaction = Transaction.objects.create(**self.trans_data)


        '''CASE 1: 
            - When PaystackService.transfer() is successful
        '''

        with patch('transactions.helpers.PaystackService.transfer') as pw:
            
            pw.return_value = self.success_response # define return values
            message, _ = paystack_withdraw(transaction.id)    

        # assertions
        self.assertEqual(message, self.success_response['message'])


        '''CASE 2: 
            - When PaystackService.transfer() failed
        '''

        with patch('transactions.helpers.PaystackService.transfer') as pw:
           
            pw.return_value = self.failure_response # define return values
            message, _ = paystack_withdraw(transaction.id)    

        # assertions
        self.assertEqual(message, self.failure_response['message'])



    def test_ravepay_bills(self):
        ''' Assert that the ravepay bills function works for transactions '''

        # set up a transaction
        self.trans_data['type_of_transaction'] = TransactionOptions.Payment
        self.trans_data['data']['type_of_biller'] = 'Airtime'
        self.trans_data['data']['name_of_biller'] = 'AIRTEL'
        transaction = Transaction.objects.create(**self.trans_data)


        '''CASE 1: 
            - When RavepayService.trans_bill_payments() is successful
        '''

        with patch('transactions.helpers.RavepayService.trans_bill_payments') as rpb:

            # remove and replace status, as ravpay and paystack have diff keys    
            self.success_response['data']['Status'] = self.success_response['data'].pop('status')

            rpb.return_value = self.success_response # define return values
            message, _ = ravepay_bills(transaction.id)    

        # assertions
        self.assertEqual(message, self.success_response['message'])


        '''CASE 2: 
            - When RavepayService.trans_bill_payments() failed
        '''

        with patch('transactions.helpers.RavepayService.trans_bill_payments') as rpb:

            # remove and replace status, as ravpay and paystack have diff keys    
            self.failure_response['data']['Status'] = self.failure_response['data'].pop('status')

            rpb.return_value = self.failure_response # define return values
            message, _ = ravepay_bills(transaction.id)    

        # assertions
        self.assertEqual(message, self.failure_response['message'])


    def test_create_deposit(self):
        ''' Assert that the create deposit function works for transactions '''

        '''CASE 1: 
            - When PaystackService.charge_card() is successful
        '''

        with patch('transactions.helpers.PaystackService.charge_card') as pcc:

            pcc.return_value = self.success_response # define return values
            message, _ = create_deposit(account=self.wallet_account,
                                        amount=200, 
                                        fundsource=self.fs)    

        # assertions
        self.assertEqual(message, self.success_response['message'])


        '''CASE 2: 
            - When PaystackService.charge_card() failed
        '''

        with patch('transactions.helpers.PaystackService.charge_card') as pcc:

            # add more required response data
            self.failure_response['data']['gateway_response'] = 'it just failed'

            pcc.return_value = self.failure_response # define return values
            message, _ = create_deposit(account=self.wallet_account,
                                        amount=200, 
                                        fundsource=self.fs)    

        # assertions
        self.assertEqual(message, self.failure_response['message'])
