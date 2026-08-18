from django.db import models

class Donor(models.Model):
    STATUS_CHOICES = [
        ('PAID', 'Paid'),
        ('DUE', 'Due'),
    ]

    name = models.CharField(max_length=255, db_index=True)
    mobile_number = models.CharField(max_length=15, db_index=True)
    email = models.EmailField(blank=True, null=True, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='DUE',
        db_index=True
    )
    payment_date = models.DateTimeField(blank=True, null=True)
    
    # Google Maps Integration fields
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    google_place_id = models.CharField(max_length=255, blank=True, null=True)

    # Email notification tracking
    notification_sent = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.payment_status} (₹{self.amount})"

    class Meta:
        ordering = ['-created_at']


class AllowedUser(models.Model):
    """
    Model for tracking usernames authorized to log into the website without a password.
    Usernames are stored normalized in lowercase for case-insensitive authentication.
    """
    username = models.CharField(max_length=150, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def clean(self):
        if self.username:
            self.username = self.username.strip().lower()

    def save(self, *args, **kwargs):
        if self.username:
            self.username = self.username.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

    class Meta:
        ordering = ['username']

