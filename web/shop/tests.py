from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from .models import Master, Service, Appointment, TelegramUser
from unittest.mock import patch

@patch('shop.signals.requests.post')
class Test_double_entry(TestCase):

    def setUp(self):
        self.master = Master.objects.create(name="Алина")
        self.service = Service.objects.create(name="Стрижка", price=1000)
        self.telegram_user = TelegramUser.objects.create(chat_id=123456789)

    def test_cannot_book_same_time(self, mock_post):
        mock_post.return_value.status_code = 200
        Appointment.objects.create(
        master=self.master,
        service=self.service,
        date="2026-03-15",
        time="12:00")

        with self.assertRaises(IntegrityError):
            Appointment.objects.create(
                master=self.master,
                service=self.service,
                date="2026-03-15",
                time="12:00")
    def test_validation_error_on_same_time(self, mock_post):
        mock_post.return_value.status_code = 200

        Appointment.objects.create(
            master=self.master,
            service=self.service,
            date="2026-03-15",
            time="12:00"
        )

        duplicate_appointment = Appointment(
            master=self.master,
            service=self.service,
            date="2026-03-15",
            time="12:00"
        )

        with self.assertRaises(ValidationError):
            duplicate_appointment.full_clean()

    def test_appointment_via_telegram(self, mock_post):
        mock_post.return_value.status_code = 200

        Appointment.objects.create(
            master=self.master,
            service=self.service,
            date="2026-03-15",
            time="12:00",
            user=self.telegram_user
        )
        self.assertEqual(Appointment.objects.count(), 1)

@patch('shop.signals.requests.post')
class Test_Views(TestCase):
    def setUp(self):
        self.master = Master.objects.create(name="Алина")
        self.service = Service.objects.create(name="Стрижка", price=1000)

    def test_api_master_status_code(self, mock_post):
        response = self.client.get('/api/masters/')
        self.assertEqual(response.status_code, 200)

    def test_api_service_status_code(self, mock_post):
        response = self.client.get('/api/services/')
        self.assertEqual(response.status_code, 200)

    def test_get_booked_slots(self, mock_post):
        mock_post.return_value.status_code = 200

        Appointment.objects.create(
            master=self.master,
            service=self.service,
            date="2026-03-15",
            time="12:00"
        )
        response = self.client.get('/get-booked-slots/', {
            'master_id': self.master.id,
            'date': '2026-03-15'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('12:00', data['booked'])