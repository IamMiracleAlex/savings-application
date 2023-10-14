from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from users.models import CustomUser
from accounts.models import Account
from transactions.models import Transaction
from utils.choices import Transaction as TransactionOptions



class ListCreateTransactionsViewTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user_data = { 
            'phone_number': '2348026043569',
            'password': '@password123',
            'email': 'email@example.com'
        }     
        cls.user = CustomUser.objects.create_user(**cls.user_data)

        acct_data = {'balance':500, 'interest':30,
                'last_interest_withdrawal_day': timezone.now() }
        cls.user.account_set.update(**acct_data)



    def test_list_transactions_view(self):
        '''assert that the GET method for ListCreate view works as expected'''

        account = self.user.account_set.first()
        url = reverse('transactions:transactions', 
                        args=[account.get_type_of_account_display()]
                        )
        # create trans in the db                

        trans_data = {'account': account,
                    'type_of_transaction': TransactionOptions.Deposit,
                    'status': TransactionOptions.SUBMITTED,
                    'reference': 'qwerty',
                    'amount': 200,
                    'balance_after_transaction': 200,
                    'fee': 100,
                    'memo': 'deposit',
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

    def test_create_transactions_view(self):
        '''Assert that the POST method for ListCreate view works, creates a 
        transfer, desc account balance and balance after transaction are processed correctly'''


        account = self.user.account_set.first()
        url = reverse('transactions:transactions', 
                        args=[account.get_type_of_account_display()]
                        )
        # destination user and account setup            

        dest_user_data = self.user_data.copy()
        dest_user_data['phone_number'] = '07069179050'
        dest_user_data['email'] = 'example@yahoo.com'

        dest_user = CustomUser.objects.create_user(**dest_user_data)   
        dest_account = Account.objects.filter(user=dest_user).first()

        # create a trans using a post request

        trans_data = {'account': account,
                    'type_of_transaction': 'transfer',
                    'amount': 200,
                    'dest_account': dest_account,
                    'dest_account_id': dest_account.id,
                } 
        self.client.force_authenticate(self.user)
        resp = self.client.post(url, data=trans_data)

        # get updated data from db
        account.refresh_from_db()
        dest_account.refresh_from_db()
        
        # assert dest acc balance was credited, etc

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('processing', resp.data['message'])
        self.assertEqual(resp.data['data']['amount'], trans_data['amount'])
        self.assertEqual(resp.data['data']['balance_after_transaction'], 
                                    account.balance)
        self.assertEqual(
                        resp.data['data']['data']['dest_account_balance_after_transaction'],
                        dest_account.balance
                        )



class ChickenChangeViewTest(APITestCase):

    @classmethod
    def setUpTestData(cls):

        # load and create staff user
        cls.user_data = { 
            'phone_number': '2348026043569',
            'password': '@password123',
            'email': 'email@example.com',
            'first_name': 'Miracle',
            'last_name': 'Alex'
        }     
        cls.staff_user = CustomUser.objects.create_user(**cls.user_data)

        # update data to create regular user
        cls.user_data['phone_number'] = '2347069179050'
        cls.user_data['email'] = 'example@gmail.com'
        cls.regular_user = CustomUser.objects.create_user(**cls.user_data)

        # get regular user, and staff wallet's account
        cls.r_user_acc = cls.regular_user.account_set.first()
        cls.s_user_acc = cls.staff_user.account_set.first()

    def test_post(self):
        '''CASE 1: Assert deposit is forbidden for NON staff user'''

        url = reverse('chicken_change_deposit')
        data = {'amount': 200,
                'dest_account_id': self.r_user_acc.id}
        self.client.force_authenticate(self.staff_user)
        resp = self.client.post(url, data)     

        self.assertEqual('User must be a staff', resp.data['message'])

        '''CASE 2: Assert that sfaffs can't deposit to own accounts'''

        # update data and make request
        self.staff_user.is_staff = True
        self.staff_user.save()
        data['dest_account_id'] = self.s_user_acc.id
        resp = self.client.post(url, data)  

        self.assertEqual('Deposits to own account is forbidden', resp.data['message'])

        '''Case 3: Assert that amount and dest_account_id must be provided to
            complete a deposit'''

        # remove one entry
        del data['dest_account_id']
        resp = self.client.post(url, data)  

        self.assertEqual('Please provide both dest_account_id and amount',
                    resp.data['message'])

        '''
        Case 4: Assert thaat the chicken deposit works when provided accurate data
        '''

        # add entry
        data['dest_account_id'] = self.r_user_acc.id
        resp = self.client.post(url, data)  

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(f"Your deposit to '{self.regular_user.full_name()}' was successful",
                    resp.data['message'])




class InitializeTransactionTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user_data = { 
            'phone_number': '2348026043569',
            'password': '@password123',
            'email': 'email@example.com'
        }     
        cls.user = CustomUser.objects.create_user(**cls.user_data)

    def test_post(self):
        'Assert that transactions are initialized'

        # prepare parameters
        data = {'amount': 200,
                'email': 'collinsalex50@gmail.com'}
        url = reverse('paystack_initialize')

        response = { # define return values for success
                'status': True,
                'message':  'Authorization URL created',
                'data': {'authorization_url': 'https://paystack.com',
                        'access_code': '8yib99iv1gbkwwh',
                        'reference': 'yhmza4djc2'},
            }
        
        with patch('transactions.views.PaystackService.initialize_transaction') as pit:
            
            pit.return_value = response # define return values
            self.client.force_authenticate(self.user)
            resp = self.client.post(url, data)

        # assertions
        self.assertEqual(resp.data['message'], response['message'])
        self.assertEqual(resp.data['status'], response['status'])
        self.assertEqual(resp.data['data']['reference'], response['data']['reference'])


class ResolveAccountNumberTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user_data = { 
            'phone_number': '2348026043569',
            'password': '@password123',
            'email': 'email@example.com'
        }     
        cls.user = CustomUser.objects.create_user(**cls.user_data)

    def test_post(self):
        'Assert that accounts numbers are resolved'

        # prepare parameters
        url = reverse('paystack_resolve_acct_number')
        data = {
            'account_number': '0707302302',
            'bank_code': '044'
        }
        success_response = {
                        "status": 'true',
                        "message": "Account number resolved",
                        "data": {
                            "account_number": "0707302302",
                            "account_name": "MIRACLE COLLINS ALEX",
                            "bank_id": 1
                        }
                    }

        
        with patch('transactions.views.PaystackService.resolve_account_number') as prac:
            
            prac.return_value = success_response # define return values
            self.client.force_authenticate(self.user)
            resp = self.client.post(url, data)

        # assertions
        self.assertEqual(resp.data['message'], success_response['message'])
        self.assertEqual(resp.data['data']['account_name'], success_response['data']['account_name'])
        self.assertEqual(resp.data['data']['account_number'], success_response['data']['account_number'])
   