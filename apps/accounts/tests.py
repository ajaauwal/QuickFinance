from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class UserTests(TestCase):
    
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'password123'
        }
        self.user = User.objects.create_user(**self.user_data)
    
    def test_signup(self):
        response = self.client.post(reverse('accounts:signup'), data=self.user_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful signup
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_login(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_password_reset(self):
        response = self.client.post(reverse('accounts:password_reset'), {'email': self.user_data['email']})
        self.assertEqual(response.status_code, 302)
