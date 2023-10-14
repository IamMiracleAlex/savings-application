from django.test import SimpleTestCase
from django.urls import reverse, resolve

from safelocks import views



class SafeLocksUrlsPatternsTest(SimpleTestCase):
    
    def test_list_create_url(self):
        '''assert that the name returns the required path for list create 
        subscriptions url'''

        url_name = reverse('safelocks:safelocks')
        url_path = '/api/v1/users/me/safelocks/'
        self.assertEqual(url_name, url_path)

    def test_retrieve_update_url(self):
        '''assert that the name returns the required path for retrieve update 
        subscriptions url'''

        url_name = reverse('safelocks:safelock')
        url_path = '/api/v1/users/me/safelock/'
        self.assertEqual(url_name, url_path)



class SafeLocksUrlsResolvesToViewTest(SimpleTestCase):

    def test_list_create_resolves_to_view(self):
        '''assert that list_create url resolves to the list_create safelocks
        view class'''

        # resolves to the func.view_class
        found = resolve('/api/v1/users/me/safelocks/')
        self.assertEquals(found.func.view_class, views.ListCreateSafeLocksView)

    def test_retrieve_update_resolves_to_view(self):
        '''assert that retrieve_update url resolves to the retrieve_update
        view class'''

        found = resolve('/api/v1/users/me/safelock/')
        self.assertEquals(found.func.view_class, views.RetrieveUpdateSafeLockView)


