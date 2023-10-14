from django.test import SimpleTestCase
from django.urls import reverse, resolve

from users import views




class UserUrlsPatternsTest(SimpleTestCase):
    
    def test_user_register_url(self):
        '''assert that the name returns the required path for signup'''

        url_name = reverse('users:register')
        url_path = '/api/v1/register/'
        self.assertEqual(url_name, url_path)

    def test_user_login_url(self):
        '''assert that the name returns the required path for login'''

        url_name = reverse('users:login')
        url_path = '/api/v1/login/'
        self.assertEqual(url_name, url_path)

    def test_user_logout_url(self):
        '''assert that the name returns the required path for logout'''

        url_name = reverse('users:logout')
        url_path = '/api/v1/logout/'
        self.assertEqual(url_name, url_path)



class NotificationsUrlsPatternsTest(SimpleTestCase):

    def test_enable_notifications_url(self):
        '''assert that the name returns the required path for
         enable notifications'''

        url_name = reverse('users:enable_notifications')
        url_path = '/api/v1/users/me/enable_notifications/'
        self.assertEqual(url_name, url_path)


    def test_disable_notifications_url(self):
        '''assert that the name returns the required path for
         disable notifications'''

        url_name = reverse('users:disable_notifications')
        url_path = '/api/v1/users/me/disable_notifications/'
        self.assertEqual(url_name, url_path)



class EmailActivationUrlsPatternsTest(SimpleTestCase):

    def test_send_activation_email_url(self):
        '''assert that the name returns the required path for
         enable notifications'''

        url_name = reverse('users:send_activation_email')
        url_path = '/api/v1/users/me/send_email_activation/'
        self.assertEqual(url_name, url_path)


    def test_activate_email_url(self):
        '''assert that the name returns the required path for
         disable notifications'''

        url_name = reverse('users:activate_email', args=['uidb64', 'token'])
        url_path = '/api/v1/users/activate/uidb64/token'
        self.assertEqual(url_name, url_path)



class UserUrlsResolvesToViewTest(SimpleTestCase):

    def test_login_url_resolves_to_login_view(self):
        '''assert that login url resolves to the login view class'''

        found = resolve('/api/v1/login/')
        # use func.view_class to get the class for the view
        self.assertEquals(found.func.view_class, views.LoginView)

    
    def test_logout_url_resolves_to_logout_view(self):
        '''assert that the logout url resolves to the logout view class'''

        found = resolve('/api/v1/logout/')
        self.assertEquals(found.func.view_class, views.LogoutView) 

    
    def test_register_url_resolves_to_register_view(self):
        '''assert that the register url resolves to the register view'''

        found = resolve('/api/v1/register/')
        self.assertEquals(found.func.view_class, views.SignUpView)       
      
    
    def test_user_detail_url_resolves_to_detail_view(self):
        '''assert that the user detail url resolves to the user detail view'''
        found = resolve('/api/v1/users/me/')
        self.assertEquals(found.func.view_class, views.UsersDetailsView)         
      


class EmailActivationUrlsResolvesToViewTest(SimpleTestCase):
    
    def test_send_activation_email_url_resolves_to_send_activation_view(self):
        '''assert that the send_activation_email url resolves to the right view class'''

        found = resolve('/api/v1/users/me/send_email_activation/')
        self.assertEquals(found.func.view_class, views.SendActivationEmail)         
      
    
    def test_activate_email_url_resolves_to_activate_email_view(self):
        '''assert that the activation_email url resolves to the right view class'''

        found = resolve('/api/v1/users/activate/uidb64/token')
        self.assertEquals(found.func.view_class, views.ActivateEmail)         
      

      
class NotificationUrlsResolvesToViewTest(SimpleTestCase):
    
    def test_enable_notifications_url_resolves_to_enable_notifications_view(self):
        '''assert that the enable_notifications url resolves to the right view class'''

        found = resolve('/api/v1/users/me/enable_notifications/')
        self.assertEquals(found.func.view_class, views.EnableNotifications)         
      
    
    def test_disable_notifications_url_resolves_to_disable_notifications_view(self):
        '''assert that the disable_notifications url resolves to the right view class'''

        found = resolve('/api/v1/users/me/disable_notifications/')
        self.assertEquals(found.func.view_class, views.DisableNotifications)         

        