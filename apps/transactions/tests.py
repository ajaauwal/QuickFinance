from django.test import TestCase
from django.contrib.auth.models import User
from services.models import Service
from .models import Transaction
from django.test import TestCase
from .models import Profile, Wallet



class TransactionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.service = Service.objects.create(name='Airtime Recharge', description='Recharge your airtime', price=100.00, category='Utility')
        self.transaction = Transaction.objects.create(
            user=self.user,
            service=self.service,
            amount=100.00,
            transaction_id='12345ABC',
            status='Completed'
        )

    def test_transaction_creation(self):
        transaction = Transaction.objects.get(transaction_id='12345ABC')
        self.assertEqual(transaction.user.username, 'testuser')
        self.assertEqual(transaction.service.name, 'Airtime Recharge')
        self.assertEqual(transaction.amount, 100.00)
        self.assertEqual(transaction.status, 'Completed')
        self.assertIsNotNone(transaction.timestamp)




class WalletSignalTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")

    def test_wallet_creation(self):
        profile = Profile.objects.create(user=self.user)
        self.assertTrue(Wallet.objects.filter(profile=profile).exists())
        wallet = Wallet.objects.get(profile=profile)
        self.assertEqual(wallet.balance, 0.00)
