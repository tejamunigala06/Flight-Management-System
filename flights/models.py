from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone


class Airport(models.Model):
    code = models.CharField(max_length=3, unique=True)  # IATA code e.g. JFK
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)

    class Meta:
        ordering = ['city']

    def __str__(self):
        return f"{self.code} — {self.city}, {self.country}"


class Flight(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('boarding', 'Boarding'),
        ('departed', 'Departed'),
        ('landed', 'Landed'),
        ('cancelled', 'Cancelled'),
        ('delayed', 'Delayed'),
    ]

    AIRLINE_CHOICES = [
        ('AirIndia', 'Air India'),
        ('IndiGo', 'IndiGo'),
        ('Emirates', 'Emirates'),
        ('Lufthansa', 'Lufthansa'),
        ('Singapore Airlines', 'Singapore Airlines'),
        ('British Airways', 'British Airways'),
        ('Qatar Airways', 'Qatar Airways'),
        ('United Airlines', 'United Airlines'),
        ('Delta Airlines', 'Delta Airlines'),
        ('American Airlines', 'American Airlines'),
    ]

    flight_number = models.CharField(max_length=10, unique=True)
    airline = models.CharField(max_length=50, choices=AIRLINE_CHOICES)
    origin = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='departures')
    destination = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='arrivals')
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    aircraft_type = models.CharField(max_length=50, default='Boeing 737')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    # Seat capacities
    economy_capacity = models.PositiveIntegerField(default=150)
    business_capacity = models.PositiveIntegerField(default=30)
    first_capacity = models.PositiveIntegerField(default=10)

    # Available seats
    economy_available = models.PositiveIntegerField(default=150)
    business_available = models.PositiveIntegerField(default=30)
    first_available = models.PositiveIntegerField(default=10)

    # Prices
    economy_price = models.DecimalField(max_digits=10, decimal_places=2)
    business_price = models.DecimalField(max_digits=10, decimal_places=2)
    first_price = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['departure_time']

    def __str__(self):
        return f"{self.flight_number} | {self.origin.code} → {self.destination.code} | {self.departure_time.strftime('%d %b %Y %H:%M')}"

    @property
    def duration_minutes(self):
        delta = self.arrival_time - self.departure_time
        return int(delta.total_seconds() / 60)

    @property
    def duration_display(self):
        mins = self.duration_minutes
        hours = mins // 60
        minutes = mins % 60
        return f"{hours}h {minutes:02d}m"

    def get_price(self, seat_class):
        prices = {
            'economy': self.economy_price,
            'business': self.business_price,
            'first': self.first_price,
        }
        return prices.get(seat_class, self.economy_price)

    def get_available(self, seat_class):
        available = {
            'economy': self.economy_available,
            'business': self.business_available,
            'first': self.first_available,
        }
        return available.get(seat_class, 0)

    def status_badge_class(self):
        badge_map = {
            'scheduled': 'bg-primary',
            'boarding': 'bg-warning text-dark',
            'departed': 'bg-info',
            'landed': 'bg-success',
            'cancelled': 'bg-danger',
            'delayed': 'bg-orange',
        }
        return badge_map.get(self.status, 'bg-secondary')


class Booking(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending'),
    ]

    SEAT_CLASS_CHOICES = [
        ('economy', 'Economy'),
        ('business', 'Business'),
        ('first', 'First Class'),
    ]

    booking_reference = models.CharField(max_length=12, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='bookings')
    seat_class = models.CharField(max_length=20, choices=SEAT_CLASS_CHOICES, default='economy')
    num_passengers = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking {self.booking_reference} — {self.user.username} on {self.flight.flight_number}"

    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = self._generate_reference()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_reference():
        import random
        import string
        chars = string.ascii_uppercase + string.digits
        while True:
            ref = 'FMS' + ''.join(random.choices(chars, k=7))
            if not Booking.objects.filter(booking_reference=ref).exists():
                return ref

    def status_badge_class(self):
        badge_map = {
            'confirmed': 'bg-success',
            'cancelled': 'bg-danger',
            'pending': 'bg-warning text-dark',
        }
        return badge_map.get(self.status, 'bg-secondary')


class Passenger(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='passengers')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    passport_number = models.CharField(max_length=20)
    nationality = models.CharField(max_length=100, default='Indian')
    seat_number = models.CharField(max_length=5, blank=True, null=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} (Booking: {self.booking.booking_reference})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
