from django.apps import AppConfig


class DonorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'donors'

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(self.seed_allowed_users, sender=self)

    def seed_allowed_users(self, sender, **kwargs):
        try:
            from .models import AllowedUser
            default_usernames = ['malli', 'veeresh', 'kiran', 'jagadeesh', 'harish', 'sanju', 'dora']
            for uname in default_usernames:
                AllowedUser.objects.get_or_create(username=uname.lower())
        except Exception:
            pass

