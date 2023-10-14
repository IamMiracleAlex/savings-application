from django.test import TestCase

from users.models import CustomUser, MassNotification
from accounts.models import Account


class UserModelTest(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(phone_number='2348026043569', 
                            password='password123', email='example@gmail.com',
                            first_name='Miracle', last_name='Alex')
                            

    def test_user_creation(self):
        '''assert fields were created correctly'''

        self.assertEqual(self.user.phone_number, '2348026043569')
        self.assertEqual(self.user.email, 'example@gmail.com')
        self.assertEqual(self.user.first_name, 'Miracle')
        self.assertEqual(self.user.last_name, 'Alex')
        self.assertIsNone(self.user.referer)
        self.assertIsNone(self.user.account_number)
        self.assertIsNone(self.user.account_bank_name)

    def test_user_boolean_fields(self):
        '''assert boolean fields has correct defaults'''

        self.assertIs(self.user.is_active, True)
        self.assertIs(self.user.account_activated, False)
        self.assertIs(self.user.send_notifications, False)
        self.assertIs(self.user.phone_verified, False)

    def test_full_name(self):
        '''assert full_name() works'''

        self.assertEqual(self.user.full_name(), 'Miracle Alex')

    def test_public_id_and_referer_code(self):
        '''assert that public_id and referer code were generated'''

        expected = r'^[a-z0-9]{6}$' #pattern of generated regex
        self.assertRegex(self.user.refer_code, expected)
        self.assertRegex(self.user.public_id, expected)

    def test_populate_accounts(self):
        '''assert that accounts are populated'''

        user_accounts = self.user.account_set.count()
        self.assertEqual(user_accounts, 3) #each user has 3 accounts       

    def test_create_kyc(self):
        '''assert that kyc profile is being created'''

        self.assertIsNotNone(self.user.kycprofile)



class MassNotificationTest(TestCase):

    def test_notification_creation(self):
        '''Test that the model is been created with expected default values'''

        user = CustomUser.objects.create_user(phone_number='08026043569',
                                password='password123', email='email@gmail.com')
        data = {'title': 'Happy Christmas',
                'message':'We wish you a merry christmass',
                'author': user, 'modified_by': user
            }
        notify = MassNotification.objects.create(**data)
        self.assertEqual(notify.title, data.get('title'))
        self.assertEqual(notify.author, data.get('author'))
        self.assertEqual(notify.modified_by, data.get('modified_by'))
        self.assertIsNotNone(notify.created_at)
        self.assertIsNotNone(notify.updated_at)