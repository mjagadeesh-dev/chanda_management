from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal

from .models import Donor
from .forms import DonorForm

class DonorFormTestCase(TestCase):
    """
    Tests validation logic within DonorForm (Mobile Number and Chanda Amount validation).
    """
    def test_valid_indian_mobile_numbers(self):
        # Test standard 10 digit
        form_data = {
            'name': 'Ravi Kumar',
            'mobile_number': '9876543210',
            'amount': 500,
            'address': 'Adoni, Andhra Pradesh',
            'payment_status': 'DUE'
        }
        form = DonorForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['mobile_number'], '9876543210')

        # Test country prefix +91
        form_data['mobile_number'] = '+919876543210'
        form = DonorForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['mobile_number'], '9876543210')

        # Test leading 0
        form_data['mobile_number'] = '09876543210'
        form = DonorForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['mobile_number'], '9876543210')

    def test_invalid_mobile_numbers(self):
        form_data = {
            'name': 'Ravi Kumar',
            'mobile_number': '1234567890', # Invalid starting digit (must be 6-9)
            'amount': 500,
            'address': 'Adoni, Andhra Pradesh',
            'payment_status': 'DUE'
        }
        form = DonorForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('mobile_number', form.errors)

        form_data['mobile_number'] = '9876543' # Too short
        form = DonorForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('mobile_number', form.errors)

    def test_chanda_amount_validation(self):
        form_data = {
            'name': 'Ravi Kumar',
            'mobile_number': '9876543210',
            'amount': 0, # Invalid amount (must be positive)
            'address': 'Adoni, Andhra Pradesh',
            'payment_status': 'DUE'
        }
        form = DonorForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

        form_data['amount'] = -100 # Negative amount
        form = DonorForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)


class DonorViewsTestCase(TestCase):
    """
    Tests security access constraints, dashboard calculations, and status transitions.
    """
    def setUp(self):
        # Create a test admin user
        self.username = 'admin'
        self.password = 'password123'
        self.user = User.objects.create_superuser(
            username=self.username, 
            password=self.password,
            email='admin@example.com'
        )
        self.client = Client()

    def test_unauthenticated_request_redirects_to_login(self):
        # Accessing dashboard without login should redirect (302) to login page
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_passwordless_login_case_insensitive(self):
        from .models import AllowedUser
        AllowedUser.objects.get_or_create(username='malli')

        # Test exact lowercase username
        response = self.client.post(reverse('login'), {'username': 'malli'})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('dashboard'), response.url)

        self.client.logout()

        # Test uppercase/mixed case username
        response = self.client.post(reverse('login'), {'username': 'MaLLi'})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('dashboard'), response.url)

    def test_passwordless_login_unauthorized_user(self):
        response = self.client.post(reverse('login'), {'username': 'unknown_user'})
        self.assertEqual(response.status_code, 200) # Re-renders login form with error
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_superuser_admin_panel_flow(self):
        from .models import AllowedUser

        # 1. Non-superuser access to admin panel fails
        response = self.client.get(reverse('admin_panel'))
        self.assertEqual(response.status_code, 302)

        # 2. Superuser login
        response = self.client.post(reverse('admin_login'), {'username': self.username, 'password': self.password})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('admin_panel'), response.url)

        # 3. Add new allowed user 'srinivas'
        response = self.client.post(reverse('admin_add_user'), {'username': 'Srinivas'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(AllowedUser.objects.filter(username='srinivas').exists())

        # 4. Verify 'srinivas' can log in passwordless
        self.client.logout()
        response = self.client.post(reverse('login'), {'username': 'SRINIVAS'})
        self.assertEqual(response.status_code, 302)

        # 5. Admin revokes 'srinivas' access
        self.client.login(username=self.username, password=self.password)
        allowed_obj = AllowedUser.objects.get(username='srinivas')
        response = self.client.post(reverse('admin_delete_user', kwargs={'pk': allowed_obj.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(AllowedUser.objects.filter(username='srinivas').exists())

        # 6. Verify 'srinivas' can no longer log in
        self.client.logout()
        response = self.client.post(reverse('login'), {'username': 'srinivas'})
        self.assertEqual(response.status_code, 200)

    def test_dashboard_calculations(self):
        # Login with an allowed user
        from .models import AllowedUser
        AllowedUser.objects.get_or_create(username='malli')
        self.client.post(reverse('login'), {'username': 'malli'})

        # Create mock data
        Donor.objects.create(name='Donor A', mobile_number='9876543210', amount=1000.00, payment_status='PAID', payment_date=timezone.now(), address='Location A')
        Donor.objects.create(name='Donor B', mobile_number='8765432109', amount=500.00, payment_status='PAID', payment_date=timezone.now(), address='Location B')
        Donor.objects.create(name='Donor C', mobile_number='7654321098', amount=250.00, payment_status='DUE', address='Location C')

        # Load Dashboard
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

        # Assert correct calculation variables are passed
        self.assertEqual(response.context['total_donors'], 3)
        self.assertEqual(response.context['paid_donors'], 2)
        self.assertEqual(response.context['due_donors'], 1)
        self.assertEqual(response.context['total_collected'], Decimal('1500.00'))
        self.assertEqual(response.context['total_due'], Decimal('250.00'))

    def test_mark_donor_paid_transition(self):
        from .models import AllowedUser
        AllowedUser.objects.get_or_create(username='malli')
        self.client.post(reverse('login'), {'username': 'malli'})

        # Create a due donor with email
        donor = Donor.objects.create(
            name='Suresh', 
            mobile_number='9876543210', 
            amount=750.00, 
            payment_status='DUE', 
            email='suresh@example.com',
            address='Adoni'
        )
        self.assertEqual(donor.payment_status, 'DUE')
        self.assertFalse(donor.notification_sent)

        # Trigger mark-paid POST request
        response = self.client.post(reverse('donor_mark_paid', kwargs={'pk': donor.pk}))
        self.assertEqual(response.status_code, 302) # Redirects to details page

        # Reload donor from db
        donor.refresh_from_db()
        self.assertEqual(donor.payment_status, 'PAID')
        self.assertIsNotNone(donor.payment_date)
        self.assertTrue(donor.notification_sent)

    def test_donor_delete_admin_authentication(self):
        self.client.login(username=self.username, password=self.password)
        donor = Donor.objects.create(
            name='Test Delete Donor', 
            mobile_number='9876543210', 
            amount=500.00, 
            payment_status='PAID', 
            address='Adoni'
        )

        # 1. Attempt deletion with wrong password -> should fail
        response = self.client.post(reverse('donor_delete', kwargs={'pk': donor.pk}), {'admin_password': 'wrongpassword'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Donor.objects.filter(pk=donor.pk).exists())

        # 2. Attempt deletion with correct password -> should succeed
        response = self.client.post(reverse('donor_delete', kwargs={'pk': donor.pk}), {'admin_password': self.password})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Donor.objects.filter(pk=donor.pk).exists())

