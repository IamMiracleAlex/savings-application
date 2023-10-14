from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APITestCase
from rest_framework import status, serializers

from users.models import CustomUser
from accounts.models import Account
from transactions.models import Transaction
from transactions.serializers import create_deposit
from utils.choices import Transaction as TransactionOptions
from withdraws.models import Beneficiary
from deposits.models import FundSource



class TransactionSerializerTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user_data = {'phone_number':'08026043569',
                    'password':'password123',
                    'email': 'email@gmail.com'}
        cls.user = CustomUser.objects.create_user(**cls.user_data)

    def test_returned_fields(self):
        '''assert that the serializer data is returned by the serializer
         as required'''

        account = self.user.account_set.first()
        url = reverse('transactions:transactions', 
                        args=[account.get_type_of_account_display()]
                        )

        # destination user and account setup            
        dest_user_data = self.user_data.copy()
        dest_user_data['phone_number'] = '07069179050'
        dest_user_data['email'] = '@yahoo.com'

        dest_user = CustomUser.objects.create_user(**dest_user_data)   
        dest_account = Account.objects.filter(user=dest_user).first()

        # create trans in the db                
        trans_data = {'account': account,
                    'type_of_transaction': TransactionOptions.Deposit,
                    'status': TransactionOptions.SUBMITTED,
                    'reference': 'qwerty',
                    'amount': 200,
                    'balance_after_transaction': 200,
                    'fee': 100,
                    'memo': 'deposit',
                    'dest_account': dest_account
                }                        
        Transaction.objects.create(**trans_data)

        # authenticate user and fetch transactions
        self.client.force_authenticate(self.user)
        resp = self.client.get(url)
        
        # assert the url works and data is returned as expected
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['message'], 'Success')
        self.assertEqual(resp.data['data'][0]['reference'], 
                                    trans_data['reference'])
        self.assertEqual(
                        resp.data['data'][0]['balance_after_transaction'],
                        trans_data['balance_after_transaction']
                        )
        self.assertIsNotNone(resp.data['data'][0]['account_id'])


    def test_validate(self):
        '''assert the validate method validates transactions'''

        '''CASE 1: Assert that we can't make a deposit except we have a fundsource 
        ID in the payload'''

        # wallect acct instance, with data for testing
        acc_data = {
            'balance': 10000
        }

        wallet_account = self.user.account_set.update(**acc_data)
        wallet_account = self.user.account_set.first()
        wallet_url = reverse('transactions:transactions', 
                        args=[wallet_account.get_type_of_account_display()]
                        )
        # create payload, without fundsource ID and make a post request
        trans_data = {'account': wallet_account,
                    'type_of_transaction': 'deposit',
                    'amount': 200,
                } 
        self.client.force_authenticate(self.user)
        resp = self.client.post(wallet_url, data=trans_data)

        # assert that error was raised, and that it was actually due to fundsource
        self.assertRaises(serializers.ValidationError)
        self.assertEqual(resp.status_code,  status.HTTP_400_BAD_REQUEST)
        self.assertIn('fund source is invalid', 
                            resp.data['message']['non_field_errors'][0])


        '''CASE 2: Assert that we can't make a transfer except we have a desc
        account ID in the payload'''

        # change type_of_trans to transfer and make request
        trans_data['type_of_transaction'] = 'transfer'
        resp = self.client.post(wallet_url, data=trans_data)

        # error was raised, and was actually due to absence of dest acct ID
        self.assertRaises(serializers.ValidationError)
        self.assertEqual(resp.status_code,  status.HTTP_400_BAD_REQUEST)
        self.assertIn('destination account specified is invalid', 
                            resp.data['message']['non_field_errors'][0])


        '''CASE 3: Assert that we can't withdraw except the user has a valid
        beneficiary'''

        # change type_of_trans to withdraw, add more data and make request
        trans_data['type_of_transaction'] = 'withdraw'
        trans_data['amount'] = 2000
        resp = self.client.post(wallet_url, data=trans_data)

        # error was raised, and was actually due to absence of dest acct ID
        self.assertRaises(serializers.ValidationError)
        self.assertEqual(resp.status_code,  status.HTTP_400_BAD_REQUEST)
        self.assertIn('have not set a valid withdrawal beneficiary', 
                            resp.data['message']['non_field_errors'][0])


        '''
        CASE 4: Assert that withdrawals are forbidden for NON wallet accounts 
        '''

        # change acct to Direct, create a beneficiary, update data and make 
        # full withdrawal request
        direct_account = self.user.account_set.get(type_of_account=Account.DIRECT)
        direct_url = reverse('transactions:transactions', 
                        args=[direct_account.get_type_of_account_display()]
                        )
        ben_data = {
            'user': self.user,
            'type_of_beneficiary': Beneficiary.SavestUser,
            'recipient_name': 'Miracle'
        }
        beneficiary = Beneficiary.objects.create(**ben_data)
        self.user.default_withdraw_beneficiary = beneficiary
        self.user.save()

        trans_data['type_of_transaction'] = 'withdraw'
        trans_data['amount'] = 2000

        resp = self.client.post(direct_url, data=trans_data)

        # error was raised, and was actually due to a wrong acct type
        self.assertRaises(serializers.ValidationError)
        self.assertEqual(resp.status_code,  status.HTTP_400_BAD_REQUEST)
        self.assertEqual('Invalid account transaction', 
                            resp.data['message']['non_field_errors'][0])


        '''
        CASE 5: Assert that payments are forbidden for NON wallet accounts 
        '''

        # Use prev Direct acc, update data to make payment request
        trans_data['type_of_transaction'] = 'payment'
        resp = self.client.post(direct_url, data=trans_data)

        # error was raised, error messages indicates payments are not valid for 
        # this account
        self.assertRaises(serializers.ValidationError)
        self.assertEqual(resp.status_code,  status.HTTP_400_BAD_REQUEST)
        self.assertEqual('Invalid account transaction', 
                            resp.data['message']['non_field_errors'][0])


    def test_validate_amount(self):
        '''Assert that the serializer validate_amount method functions correctly'''
 
        '''CASE 1: Assert that for a WALLET account, we can't make a deposit less 
        than 100'''

        # A wallect acct url
        wallet_account = self.user.account_set.first()
        wallet_url = reverse('transactions:transactions', 
                        args=[wallet_account.get_type_of_account_display()]
                        )                
        trans_data = {
                    'type_of_transaction': 'deposit',
                    'amount': 50,
                } 
        self.client.force_authenticate(self.user)
        resp = self.client.post(wallet_url, data=trans_data)

        # assert validation error is raised, and that error msg indicates deposit
        #  amount is less than 100
        self.assertRaises(serializers.ValidationError)
        self.assertEqual(resp.status_code,  status.HTTP_400_BAD_REQUEST)
        self.assertEqual('Minimum deposit of NGN 100', 
                            resp.data['message']['amount'][0])


        '''
        CASE 2: Assert that we can't make a withdrawal less than 2000
        '''

        trans_data['type_of_transaction'] = 'withdraw'
        trans_data['amount'] = '1999' # amount less than 2000

        resp = self.client.post(wallet_url, data=trans_data)

        # assert validation error is raised, and that error msg indicates withdraw
        # amount is less than 2000
        self.assertRaises(serializers.ValidationError)
        self.assertEqual(resp.status_code,  status.HTTP_400_BAD_REQUEST)
        self.assertEqual('Minimum withdrawal of NGN 2000', 
                            resp.data['message']['amount'][0])


        '''
        CASE 3: Assert that user can't withdraw MORE THAN account balance
        '''

        # currently, user has nothing in the acct balance
        trans_data['amount'] = '2000'

        resp = self.client.post(wallet_url, data=trans_data)

        # assert validation error is raised, and that the error msg indicates user
        # can't withdraw more than acct balance
        self.assertRaises(serializers.ValidationError)
        self.assertEqual(resp.status_code,  status.HTTP_400_BAD_REQUEST)
        self.assertEqual('Insufficient Balance', 
                            resp.data['message']['amount'][0])




class SerializerFunctionsTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user_data = {'phone_number':'08026043569',
                    'password':'password123',
                    'email': 'email@gmail.com'}
        cls.user = CustomUser.objects.create_user(**cls.user_data)


    def test_validate_transfer(self):
    
        '''CASE 1: 
            - Assert that 5% fee is charged for a DIRECT account transfer before 
                withdrawal date.
            - Assert that the type of transaction 'TRANSFER' work.
            - Assert destination account are being credited on transfer.
            - Assert the type of transfer is an internal transfer
        '''

        # add funds to acct, prepare endpoint and payload
        acc_data = {
            'balance': 10000
        }
        self.user.account_set.update(**acc_data)
        wallet_account = self.user.account_set.filter(user=self.user).first()
        direct_url = reverse('transactions:transactions', 
                        args=['direct']
                        )
        # create payload, make transfer from a direct acct to wallet acct
        trans_data = {'type_of_transaction': 'transfer',
                      'amount': 200,
                      'dest_account_id': wallet_account.id
                    } 
        self.client.force_authenticate(self.user)
        resp = self.client.post(direct_url, data=trans_data)
        wallet_account.refresh_from_db() 

        # assert transfer was successful, fee was charged, dest acct was credited, etc
        self.assertEqual(resp.status_code,  status.HTTP_200_OK)
        self.assertEqual(resp.data['data']['fee'], trans_data['amount']*0.05)
        self.assertEqual(resp.data['data']['data']['transfer_type'], 'InternalTransfer')
        self.assertEqual(resp.data['data']['data']['dest_account_balance_after_transaction'],
                                    wallet_account.balance)


        '''CASE 2: 
             Assert that a transfer to the same account is NOT allowed.
             - For this, we'll attempt a transfer from a wallet account to thesame wallet
             account.
        '''

        wallet_url = reverse('transactions:transactions', 
                        args=['wallet']
                        )
        resp = self.client.post(wallet_url, data=trans_data)
        wallet_account.refresh_from_db() 

        # assert trans was declined
        self.assertRaises(serializers.ValidationError)
        self.assertEqual(resp.status_code,  status.HTTP_400_BAD_REQUEST)
        self.assertEqual('Invalid transaction', 
                            resp.data['message']['non_field_errors'][0])


        '''CASE 3: 
             Assert that a transfer with a fee is NOT allowed if sum of the amount
             and fee is greater than the balance.
             - For this, we'll attempt a transfer from a direct account, with exact balance
             in the acct. However, before due date, so a fee is charged.
        '''

        trans_data['amount'] = wallet_account.balance

        # send a request from a direct acct
        self.client.force_authenticate(self.user)
        resp = self.client.post(direct_url, data=trans_data)

        # assert balance was not enough
        self.assertRaises(serializers.ValidationError)
        self.assertEqual(resp.status_code,  status.HTTP_400_BAD_REQUEST)
        self.assertEqual('Insufficient Balance', 
                            resp.data['message']['non_field_errors'][0])


    def test_validate_payment(self):

        '''CASE 1: 
            - Assert that users are BANNED from making payments with unactivated accounts
        '''

        wallet_url = reverse('transactions:transactions', args=['wallet'])
        trans_data = {
                    'type_of_transaction': 'payment',
                    'amount': 200,
                } 
        # Send a payment request        
        self.client.force_authenticate(self.user)
        resp = self.client.post(wallet_url, data=trans_data)

        # assert the right validation error was raised
        self.assertRaises(serializers.ValidationError)
        self.assertEqual(resp.status_code,  status.HTTP_400_BAD_REQUEST)
        self.assertIn('activate your account before you can make payments', 
                            resp.data['message']['non_field_errors'][0])


        ''' CASE 2: 
            - Assert that customer id, name of biller, type of biller, fund source type MUST be present 
            in the payload
        '''

        # activate acct and make trans
        self.user.account_activated = True
        self.user.save()
        resp = self.client.post(wallet_url, data=trans_data)

        # assert the right validation error was raised
        self.assertRaises(serializers.ValidationError)
        self.assertEqual(resp.status_code,  status.HTTP_400_BAD_REQUEST)
        self.assertIn('biller, type of biller, fund source type cannot be null', 
                            resp.data['message']['non_field_errors'][0])

        ''' CASE 3: 
            - Assert that one can't make payments with a low account balance.
            PS: trans amount is 200
        '''

        # update acct balance to 100
        self.user.account_set.update(balance = 100)

        # set up trans payload
        trans_data['customer_id'] = self.user_data['phone_number']
        trans_data['name_of_biller'] = 'AIRTEL'
        trans_data['type_of_biller'] = 'Airtime'
        trans_data['fund_source_type'] = 'Wallet'

        resp = self.client.post(wallet_url, data=trans_data)

        # assert the right validation error was raised
        self.assertRaises(serializers.ValidationError)
        self.assertEqual(resp.status_code,  status.HTTP_400_BAD_REQUEST)
        self.assertEqual('Insufficient Balance', 
                            resp.data['message']['non_field_errors'][0])


        ''' CASE 4: 
            - Assert that one can't make payments when a fundsource is not provided.
        '''

        # update acct balance to 300
        self.user.account_set.update(balance = 300)

        # set up trans payload
        trans_data['fund_source_id'] = 1
        trans_data['fund_source_type'] = 'Card'

        resp = self.client.post(wallet_url, data=trans_data)

        # assert the right validation error was raised
        self.assertRaises(serializers.ValidationError)
        self.assertEqual(resp.status_code,  status.HTTP_400_BAD_REQUEST)
        self.assertEqual('Invalid card selected', 
                            resp.data['message']['non_field_errors'][0])


        ''' CASE 5: 
            - Assert that one can make payments with the endpoint.
        '''

        # set up fundsource
        fs = FundSource.objects.create(user=self.user, last4='4444',
                            bank_name='American', card_type='visa', 
                            exp_month='09', exp_year='2024',
                            is_active=True) 
        trans_data['fund_source_id'] = fs.id

        # mock the create_deposit() method to test payments
        with patch('transactions.serializers.create_deposit') as mock_cp:

            # define a deposit object and add required attributes
            deposit = lambda : None 
            setattr(deposit, 'status', TransactionOptions.SUCCESS)
            message = 'success'

            mock_cp.return_value = message, deposit # define return values
            
            resp = self.client.post(wallet_url, data=trans_data)
      
        # assert payment are successful or no errors encountered
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

