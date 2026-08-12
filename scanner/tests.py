import json
import uuid
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from participants.models import Participant

class ScannerAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='scannerstaff',
            password='Password123!',
            is_staff=True
        )

        self.participant = Participant.objects.create(
            name="Aman Verma",
            email="aman@example.com",
            roll_number="23ME105"
        )
        self.url = reverse('check_in_api')

    def test_scanner_page_access_restricted(self):
        # Anonymous user blocked
        response = self.client.get(reverse('scanner_page'))
        self.assertEqual(response.status_code, 302)

        # Staff user allowed
        self.client.login(username='scannerstaff', password='Password123!')
        response = self.client.get(reverse('scanner_page'))
        self.assertEqual(response.status_code, 200)

    def test_check_in_api_valid_first_time(self):
        self.client.login(username='scannerstaff', password='Password123!')
        payload = json.dumps({'token': str(self.participant.qr_token)})
        response = self.client.post(self.url, data=payload, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Check-in successful')
        self.assertEqual(data['participant']['name'], 'Aman Verma')

        # Check DB update
        self.participant.refresh_from_db()
        self.assertTrue(self.participant.attended)
        self.assertIsNotNone(self.participant.checked_in_at)

    def test_check_in_api_duplicate_scan(self):
        self.client.login(username='scannerstaff', password='Password123!')
        
        # First scan
        self.participant.attended = True
        self.participant.checked_in_at = timezone.now()
        self.participant.save()

        payload = json.dumps({'token': str(self.participant.qr_token)})
        response = self.client.post(self.url, data=payload, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Participant has already checked in')

    def test_check_in_api_invalid_qr_token(self):
        self.client.login(username='scannerstaff', password='Password123!')
        random_uuid = str(uuid.uuid4())
        payload = json.dumps({'token': random_uuid})
        response = self.client.post(self.url, data=payload, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Invalid QR code')

    def test_check_in_api_extracts_token_from_full_url(self):
        self.client.login(username='scannerstaff', password='Password123!')
        url_payload = f"https://techpass.college.edu/scanner/check/{self.participant.qr_token}/"
        payload = json.dumps({'token': url_payload})
        response = self.client.post(self.url, data=payload, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['participant']['roll_number'], '23ME105')
