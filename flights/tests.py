from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
import datetime

from .models import Airport, Flight, Booking, Passenger


class AirportModelTest(TestCase):
    def setUp(self):
        self.airport = Airport.objects.create(
            code='DEL', name='Indira Gandhi International Airport',
            city='Delhi', country='India'
        )

    def test_airport_str(self):
        self.assertIn('DEL', str(self.airport))
        self.assertIn('Delhi', str(self.airport))


class FlightModelTest(TestCase):
    def setUp(self):
        self.origin = Airport.objects.create(code='DEL', name='Delhi Airport', city='Delhi', country='India')
        self.destination = Airport.objects.create(code='BOM', name='Mumbai Airport', city='Mumbai', country='India')
        now = timezone.now() + datetime.timedelta(days=1)
        self.flight = Flight.objects.create(
            flight_number='AI101',
            airline='AirIndia',
            origin=self.origin,
            destination=self.destination,
            departure_time=now,
            arrival_time=now + datetime.timedelta(hours=2),
            economy_price=3500,
            business_price=8000,
            first_price=15000,
        )

    def test_flight_str(self):
        self.assertIn('AI101', str(self.flight))

    def test_duration_minutes(self):
        self.assertEqual(self.flight.duration_minutes, 120)

    def test_duration_display(self):
        self.assertEqual(self.flight.duration_display, '2h 00m')

    def test_get_price(self):
        self.assertEqual(self.flight.get_price('economy'), 3500)
        self.assertEqual(self.flight.get_price('business'), 8000)
        self.assertEqual(self.flight.get_price('first'), 15000)


class BookingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.origin = Airport.objects.create(code='DEL', name='Delhi Airport', city='Delhi', country='India')
        self.destination = Airport.objects.create(code='BOM', name='Mumbai Airport', city='Mumbai', country='India')
        now = timezone.now() + datetime.timedelta(days=1)
        self.flight = Flight.objects.create(
            flight_number='AI101', airline='AirIndia',
            origin=self.origin, destination=self.destination,
            departure_time=now, arrival_time=now + datetime.timedelta(hours=2),
            economy_price=3500, business_price=8000, first_price=15000,
        )

    def test_booking_reference_generated(self):
        booking = Booking.objects.create(
            user=self.user, flight=self.flight,
            seat_class='economy', num_passengers=1,
            total_price=3500, status='confirmed'
        )
        self.assertTrue(booking.booking_reference.startswith('FMS'))
        self.assertEqual(len(booking.booking_reference), 10)

    def test_booking_str(self):
        booking = Booking.objects.create(
            user=self.user, flight=self.flight,
            seat_class='economy', num_passengers=1,
            total_price=3500, status='confirmed'
        )
        self.assertIn('FMS', str(booking))


class ViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123',
            first_name='Test', last_name='User'
        )
        self.origin = Airport.objects.create(code='DEL', name='Delhi Airport', city='Delhi', country='India')
        self.destination = Airport.objects.create(code='BOM', name='Mumbai Airport', city='Mumbai', country='India')

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Flight')

    def test_login_view_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_register_view_get(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_booking_history_requires_login(self):
        response = self.client.get(reverse('booking_history'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_login_and_booking_history(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('booking_history'))
        self.assertEqual(response.status_code, 200)

    def test_flight_search(self):
        import datetime
        future_date = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
        response = self.client.get(reverse('flight_results'), {
            'origin': self.origin.id,
            'destination': self.destination.id,
            'departure_date': future_date,
            'num_passengers': 1,
            'seat_class': 'economy',
        })
        self.assertEqual(response.status_code, 200)
