from django.urls import reverse
from django.test import TestCase, SimpleTestCase
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.http import HttpRequest

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from users.models import CustomUser
from accounts.models import Account
from utils.helpers import AccountActivationTokenGenerator
from users.views import generate_account_number, register_user_device, send_sms_registration





class LoginViewTest(TestCase):   

    @classmethod
    def setUpTestData(cls):
        cls.auth_data = { 
            'phone_number': '2348026043569',
            'password': '@password123',
            'email': 'email@example.com'
        }     
        cls.url = reverse('users:login')

    def test_invalid_user(self):
        '''login with invalid credentials'''
        data = { 
            'phone_number': '2348026043569',
            'password': '@password123'
        }
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.data['message'], 'Invalid Credentials')

    def test_incomplete_credentials(self):
        '''Login with incomplete credentials'''
        data = { 
            'phone_number': '2348026043569',
        }
        resp = self.client.post(self.url, data=data)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data['message'], 'Please provide both phone number and password')

    def test_login(self):
        '''Login with correct credentials'''
        CustomUser.objects.create_user(**self.auth_data)

        login = self.client.post(self.url, data=self.auth_data)
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.data['message'], 'Login Successful')
        self.client.logout()



class SignUpViewTest(APITestCase):

    @classmethod
    def setUpTestData(cls):

        cls.url = reverse('users:register')
        cls.data = {'phone_number':'08026043569', 
                    'password':'password123',
                    'email':'email@example.com'}

    def test_user_creation(self):
        ''' create a new user with mvp data'''

        resp = self.client.post(self.url, self.data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('User created', resp.data['message'])
     
    def  test_user_single_account_creation(self):
        '''assert that users can only create accounts with single data'''

        CustomUser.objects.create_user(**self.data)

        resp = self.client.post(self.url, self.data, format='json')
        self.assertNotEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('User created', resp.data['message'])

    def test_token_and_json_data_creation(self):
        '''test that token and json data were created'''

        resp = self.client.post(self.url, self.data, format='json')
        expected = r'^\w+$'  #token format

        self.assertRegex(resp.data['data']['token'], expected)
        self.assertEqual(resp.data['data']['phone_number'], '08026043569')


    def test_amount_to_save_available_and_referral_created(self):
        '''assert that when amount_to_save is available and a user is staff, user is created, 
        referrals are created and amount created is the same as provided. However, creating a staff user
        possed a challenge.'''

        old_user =  CustomUser.objects.create_user(**self.data)
        refer_code = old_user.refer_code

        new_user_data = {'phone_number':'07069179050', 'password':'password123',
                        'amount_to_save': 300, 'refer_code': refer_code }
        new_user = self.client.post(self.url, new_user_data, format='json')

        self.assertEqual(new_user.status_code, status.HTTP_201_CREATED)

        new_user_public_id = new_user.data['data']['public_id'] # get new user public id
        referer = CustomUser.objects.get(referrals__public_id=new_user_public_id)

        #confirmed the old user is actually the referer
        self.assertEqual(referer.phone_number, old_user.phone_number)
    


class UserDetailsViewTest(APITestCase):

    def setUp(self):

        self.detail_url = reverse('users:users')
        self.signup_url = reverse('users:register')
        self.data = {'phone_number':'08026043569', 'password':'password123',
                        'email':'email@example.com'}

    
    def test_user_detail_get_method(self):
        '''assert that get and post method for user details works. user is retrieved by their token'''

        self.client.post(self.signup_url, self.data, format='json')

        # get token
        token = Token.objects.get(user__phone_number=self.data['phone_number'])

        # authorize token
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')        
        resp = self.client.get(self.detail_url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['data']['phone_number'], self.data['phone_number'])

    def test_user_detail_put_method(self):
        '''assert that put method for user details works. Data is sent to the user using their token'''

        self.client.post(self.signup_url, self.data, format='json')
        token = Token.objects.get(user__phone_number=self.data['phone_number'])
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')      
        new_data = { 'first_name':'Miracle', 'last_name':'Alex',
                                'email': 'example@gmail.com'} 

        # update data and assert they were updated
        resp = self.client.put(self.detail_url, new_data) 

        self.assertEqual(resp.data['data']['phone_number'], self.data['phone_number'])
        self.assertEqual(resp.data['data']['first_name'], new_data['first_name'])
        self.assertEqual(resp.data['data']['last_name'], new_data['last_name'])
        self.assertEqual(resp.data['data']['full_name'], 'Miracle Alex')


class SendActivationEmailTest(APITestCase):

    def setUp(self):

        self.activation_url = reverse('users:send_activation_email')
        self.signup_url = reverse('users:register')
        self.data = {'phone_number':'08022113344', 'password':'password123',
                        'email': 'collinsale50@gmail.com'}

        self.client.post(self.signup_url, self.data, format='json')
        self.user = CustomUser.objects.get(phone_number=self.data['phone_number'])
        self.token = Token.objects.get(user__phone_number=self.data['phone_number'])


    def test_send_activation_email_api_view(self):
        '''assert that the activation email api endpoint works'''

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        resp = self.client.post(self.activation_url)

        # endpoints returns 200 as successful
        self.assertEqual(resp.status_code, 200)


class ActivateEmailTest(APITestCase):

    def setUp(self):
        
        self.signup_url = reverse('users:register')
        self.data = {'phone_number':'08022113344', 'password':'password123',
                        'email': 'collinsale50@gmail.com'}

        self.client.post(self.signup_url, self.data, format='json')
        self.user = CustomUser.objects.get(phone_number=self.data['phone_number'])

    def test_activate_email(self):
        '''assert that activate email view works'''

        account_activation_token = AccountActivationTokenGenerator() # generate token
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.id)) # generate uid
        token = account_activation_token.make_token(self.user)
        activate_url = reverse('users:activate_email', args=[uidb64, token]) # parse args in docs
        resp = self.client.get(activate_url, format='json' )

        self.assertEqual(resp.status_code, 200)
        updated_user = CustomUser.objects.get(phone_number=self.data['phone_number'])
        self.assertTrue(updated_user.email_verified) # email has been verified


class EnableNotificationsTest(APITestCase):

    def setUp(self):
        
        self.enable_url = reverse('users:enable_notifications')
        self.signup_url = reverse('users:register')
        self.data = {'phone_number':'08022113344', 'password':'password123'}


    def test_notifications_enabled(self):
        '''assert that notifications are enabled'''

        self.client.post(self.signup_url, self.data, format='json')
        token = Token.objects.get(user__phone_number=self.data['phone_number'])
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        resp = self.client.post(self.enable_url)
        user = CustomUser.objects.get(phone_number=self.data['phone_number'])

        self.assertTrue(user.send_notifications)
        self.assertEqual(resp.status_code, 200)


class DisableNotificationsTest(APITestCase):

    def setUp(self):
        
        self.disable_url = reverse('users:disable_notifications')
        self.signup_url = reverse('users:register')
        self.data = {'phone_number':'08022113344', 'password':'password123'}

    def test_notifications_disabled(self):
        '''assert that notifications are disabled'''

        self.client.post(self.signup_url, self.data, format='json')
        token = Token.objects.get(user__phone_number=self.data['phone_number'])
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        resp = self.client.post(self.disable_url)
        user = CustomUser.objects.get(phone_number=self.data['phone_number'])

        self.assertFalse(user.send_notifications)
        self.assertEqual(resp.status_code, 200)


class GenerateAccountNumberTest(TestCase):

    def setUp(self):
        
        self.data = {'phone_number':'08022113344', 'password':'password123',
                'email': 'example@gmail.com', 'first_name':'Miracle', 'last_name':'Alex'}
                        
    def test_generate_account_number(self):
        '''assert that an account number is generated and is saved on the user model'''
        user = CustomUser.objects.create_user(**self.data)
        generate_account_number(user.id) # generate acc no with user id
        updated_user = CustomUser.objects.get(id=user.id)

        self.assertIsNotNone(updated_user.account_number)
        self.assertIsNotNone(updated_user.account_bank_name)


class RegisterUserDeviceTest(TestCase):
    
    def test_register_user_device(self):
        '''assert that user device function works for android'''

        user_data = {'phone_number':'08011223344', 'password':'password123',
                'email': 'email@gmail.com', 'first_name':'Miracle', 'last_name':'Alex'}
        user = CustomUser.objects.create_user(**user_data)

        # mock data for android device
        data = {
            'registration_id':'fdo9cajdo-4:APA91bHfPf8nE5KHrON4OKCVPqvjgZEB97FQ2a2VJOie3sQkMbaD59ZP9tvQgvZb9Qdaa1K7_TaiDGkXspgkOiFGMJ6srfiB6tIgVJZa-fIUe-jFALA7zoTpAXilr_f8liQpZcY7G_fK',
            'os':'android'}
        request = HttpRequest()
        request.data = data # add data to request obj

        # call fn to register the device
        resp =  register_user_device(request, user) 
        self.assertTrue(resp)


class SMSRegistrationTest(TestCase):
    
    def test_send_sms_registration(self):
        '''assert that sms registration is sent'''

        user_data = {'phone_number':'08026043569', 'password':'password123',
                'email': 'email@gmail.com', 'first_name':'Miracle', 'last_name':'Alex'}
        user = CustomUser.objects.create_user(**user_data)

        # call fn to register the device and assert successful
        resp = send_sms_registration(user, amount=300)
        
        self.assertEqual(resp['data']['status'], 'success')