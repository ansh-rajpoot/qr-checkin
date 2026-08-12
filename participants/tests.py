from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from participants.models import Participant

class ParticipantModelTest(TestCase):
    def test_participant_creation_and_qr_generation(self):
        participant = Participant.objects.create(
            name="Rahul Sharma",
            email="rahul@example.com",
            roll_number="23CSE101"
        )
        self.assertIsNotNone(participant.qr_token)
        self.assertTrue(bool(participant.qr_code_image))
        self.assertFalse(participant.attended)
        self.assertIsNone(participant.checked_in_at)
        self.assertTrue(participant.qr_code_image.name.startswith("qr_codes/qr_23CSE101_"))

    def test_unique_roll_number(self):
        Participant.objects.create(
            name="Participant One",
            email="p1@example.com",
            roll_number="23CSE101"
        )
        response = self.client.post(reverse('register'), {
            'name': 'Participant Two',
            'email': 'p2@example.com',
            'roll_number': '23CSE101'
        })
        self.assertFormError(response.context['form'], 'roll_number', 'A participant with this Roll Number is already registered.')

class ParticipantViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='Password123!',
            is_staff=True
        )


    def test_registration_view_post_success(self):
        response = self.client.post(reverse('register'), {
            'name': 'Anita Roy',
            'email': 'anita@example.com',
            'roll_number': '23ECE044'
        }, follow=True)
        self.assertContains(response, "Registration successful for Anita Roy!")
        self.assertEqual(Participant.objects.count(), 1)
        participant = Participant.objects.get(roll_number="23ECE044")
        self.assertRedirects(response, reverse('qr_detail', kwargs={'qr_token': participant.qr_token}))

    def test_admin_dashboard_access_control(self):
        # Unauthenticated access should redirect to login
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)

        # Staff login
        self.client.login(username='staffuser', password='Password123!')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Event Attendance Dashboard")
