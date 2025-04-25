from django.apps import AppConfig

class TransactionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.transactions'  # Adjust this based on your actual project structure

    def ready(self):
        import apps.transactions.signals  # Ensure this matches the path to your signals.py
