from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from django.http import HttpRequest
from django.urls import reverse
from django.contrib.messages.storage.fallback import FallbackStorage

from users.models import CustomUser, UserMetric, MassNotification
from users import admin



class UserAdminTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.data = {"phone_number":'2348026043569', 
                    'password':'password123', 'email':'example@gmail.com',
                    'first_name':'Miracle', 'last_name':'Alex'}
        cls.user = CustomUser.objects.create_superuser(**cls.data)

        '''Instantiate admin site and a request object'''
        
        cls.site = AdminSite() #instantiate adminsite
        cls.user_admin = admin.CustomUserAdmin(CustomUser, cls.site)

        cls.request = HttpRequest() #instantiate django http

    def test_change_view(self):
        '''Test that the overridden change_view page loads'''

        self.client.login(phone_number=self.data['phone_number'],
                            password=self.data['password'])

        # using dynamic reverse url: appname_modelname_change

        page = self.client.get(reverse('admin:users_customuser_change', args=[self.user.id]))
        self.assertEqual(page.status_code, 200)
        self.assertTemplateUsed('users_change_form.html')
      
        self.client.logout()

    def test_no_of_referrals(self):
        '''test no_of_referrals() method'''

        result = self.user_admin.no_of_referrals(self.user)
        self.assertEqual(result, 0) #user has no referrals

    def test_referred_by(self):
        '''referred_by() method test'''
        result = self.user_admin.refered_by(self.user)
        self.assertIsNone(result)

    def test_export_as_csv(self):
        '''assert that export_to_csv() works'''

        queryset = CustomUser.objects.all()
        request = HttpRequest()

        result = self.user_admin.export_as_csv(self.request, queryset)
        #csv is created and returns success status code
        self.assertEqual(result.status_code, 200) 


class UserMetricAdminTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.site = AdminSite()
        cls.usermetric_admin = admin.UserMetricAdmin(UserMetric, cls.site)

        cls.request = HttpRequest()

        CustomUser.objects.create_superuser(phone_number='08026043569', email='email@example.com', password='password123')


    def test_chart_data_endpoint(self):
        '''assert chart_data_endpoint() works'''

        #pass in request object to admin view to mimic real request
        resp = self.usermetric_admin.chart_data_endpoint(self.request)

        # json endpoint responds
        self.assertEqual(resp.status_code, 200) 

    def test_change_list_view(self):
        '''Test that chart data page loads'''

        self.client.login(phone_number='08026043569',password='password123')

        page = self.client.get(reverse('admin:users_usermetric_changelist'))
        self.assertEqual(page.status_code, 200) #change view page responds
        self.assertTemplateUsed('usermetric_change_list.html')
        self.client.logout()


class  MassNotificationAdminTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.site = AdminSite()
        cls.notify_admin = admin.MassNotificationAdmin(MassNotification, cls.site)

        cls.request = HttpRequest()
        cls.user = CustomUser.objects.create_user(phone_number='08026043569', email='email@example.com', password='password123')

    def test_user_notifications(self):
        '''assert that user notifications runs and redirects to changelist page'''
        data = {
                'title': 'Happy Christmas',
                'message':'We wish you a merry christmass',
                'author': self.user, 'modified_by': self.user
            }

        setattr(self.request, 'session', 'session') # add session to request obj
        messages = FallbackStorage(self.request)    # message middleware instance
        setattr(self.request, '_messages', messages) # add messages to request obj
        obj = MassNotification.objects.create(**data)
        notify_id = obj.pk

        result = self.notify_admin.user_notifications(self.request,
                        notify_id, is_staff=True)

        # the view redirects to the change_list_view
        self.assertEqual(result.status_code, 302)                
