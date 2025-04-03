from django.test import TestCase
from django.contrib.auth.models import User
from .models import Notification
from .utils import generate_otp, encode_data, decode_data
import pyotp

class NotificationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.notification = Notification.objects.create(user=self.user, message='Test Notification')

    def test_notification_creation(self):
        self.assertEqual(self.notification.user, self.user)
        self.assertEqual(self.notification.message, 'Test Notification')

    def test_generate_otp(self):
        otp = generate_otp()
        self.assertTrue(100000 <= otp <= 999999)

    def test_encode_decode(self):
        data = "test_data"
        encoded = encode_data(data)
        decoded = decode_data(encoded)
        self.assertEqual(decoded, data)


class OTPTestCase(TestCase):
    def test_otp_generation(self):
        secret = 'base32secret3232'
        # Assuming generate_otp uses pyotp internally
        otp = generate_otp(secret)
        self.assertTrue(100000 <= otp <= 999999)
