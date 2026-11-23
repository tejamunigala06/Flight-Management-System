"""
Management command to seed the database with sample airports, flights, and users.
Usage: python manage.py seed_flights
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from flights.models import Airport, Flight, Booking, Passenger
import datetime
import random


AIRPORTS = [
    {'code': 'DEL', 'name': 'Indira Gandhi International Airport', 'city': 'New Delhi', 'country': 'India'},
    {'code': 'BOM', 'name': 'Chhatrapati Shivaji Maharaj International Airport', 'city': 'Mumbai', 'country': 'India'},
    {'code': 'BLR', 'name': 'Kempegowda International Airport', 'city': 'Bangalore', 'country': 'India'},
    {'code': 'MAA', 'name': 'Chennai International Airport', 'city': 'Chennai', 'country': 'India'},
    {'code': 'CCU', 'name': 'Netaji Subhas Chandra Bose International Airport', 'city': 'Kolkata', 'country': 'India'},
    {'code': 'DXB', 'name': 'Dubai International Airport', 'city': 'Dubai', 'country': 'UAE'},
    {'code': 'LHR', 'name': 'Heathrow Airport', 'city': 'London', 'country': 'United Kingdom'},
    {'code': 'SIN', 'name': 'Changi Airport', 'city': 'Singapore', 'country': 'Singapore'},
    {'code': 'JFK', 'name': 'John F. Kennedy International Airport', 'city': 'New York', 'country': 'USA'},
    {'code': 'FRA', 'name': 'Frankfurt Airport', 'city': 'Frankfurt', 'country': 'Germany'},
]

AIRLINES = [
    ('AirIndia', 'AI', 'Boeing 787'),
    ('IndiGo', '6E', 'Airbus A320'),
    ('Emirates', 'EK', 'Airbus A380'),
    ('Lufthansa', 'LH', 'Airbus A350'),
    ('Singapore Airlines', 'SQ', 'Boeing 777'),
    ('British Airways', 'BA', 'Boeing 787'),
    ('Qatar Airways', 'QR', 'Airbus A350'),
]

ROUTES = [
    ('DEL', 'BOM', 2, 2.5),
    ('BOM', 'DEL', 2, 2.5),
    ('DEL', 'BLR', 2.5, 3),
    ('BLR', 'DEL', 2.5, 3),
    ('DEL', 'DXB', 3.5, 4),
    ('DXB', 'DEL', 3.5, 4),
    ('DEL', 'LHR', 8, 9),
    ('LHR', 'DEL', 8, 9),
    ('BOM', 'DXB', 3, 3.5),
    ('DXB', 'BOM', 3, 3.5),
    ('BLR', 'SIN', 5, 5.5),
    ('SIN', 'BLR', 5, 5.5),
    ('DEL', 'SIN', 5.5, 6),
    ('SIN', 'DEL', 5.5, 6),
    ('BOM', 'LHR', 8.5, 9),
    ('DEL', 'JFK', 14, 15),
    ('JFK', 'DEL', 14, 15),
    ('DEL', 'FRA', 7.5, 8),
    ('FRA', 'DEL', 7.5, 8),
    ('MAA', 'DXB', 4, 4.5),
    ('CCU', 'DEL', 1.5, 2),
    ('DEL', 'CCU', 1.5, 2),
    ('BOM', 'BLR', 1.5, 2),
    ('BLR', 'BOM', 1.5, 2),
]


class Command(BaseCommand):
    help = 'Seed the database with sample airports, flights, and users'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Flight.objects.all().delete()
            Airport.objects.all().delete()
            Booking.objects.all().delete()
            Passenger.objects.all().delete()

        self.stdout.write('Seeding airports...')
        airport_map = {}
        for a in AIRPORTS:
            obj, created = Airport.objects.get_or_create(code=a['code'], defaults=a)
            airport_map[a['code']] = obj
            if created:
                self.stdout.write(f"  Created airport: {obj}")

        self.stdout.write('Seeding flights...')
        flight_count = 0
        today = timezone.now().date()
        for day_offset in range(0, 14):  # 2 weeks of flights
            flight_date = today + datetime.timedelta(days=day_offset)
            for origin_code, dest_code, min_hours, max_hours in ROUTES:
                # 2-3 flights per route per day
                num_flights = random.randint(2, 3)
                for i in range(num_flights):
                    airline_tuple = random.choice(AIRLINES)
                    airline_name, airline_code, aircraft = airline_tuple
                    hour = random.choice([6, 9, 11, 14, 17, 20, 22])
                    minute = random.choice([0, 15, 30, 45])
                    dep_dt = timezone.make_aware(
                        datetime.datetime(flight_date.year, flight_date.month, flight_date.day, hour, minute)
                    )
                    duration_hours = round(random.uniform(min_hours, max_hours), 1)
                    arr_dt = dep_dt + datetime.timedelta(hours=duration_hours)

                    fn = f"{airline_code}{random.randint(100, 999)}"
                    # Avoid duplicate flight numbers
                    while Flight.objects.filter(flight_number=fn).exists():
                        fn = f"{airline_code}{random.randint(100, 999)}"

                    # Pricing (domestic cheaper, international more expensive)
                    is_international = airport_map[origin_code].country != airport_map[dest_code].country
                    base = random.randint(5000, 20000) if is_international else random.randint(2000, 8000)
                    eco_price = round(base * random.uniform(0.8, 1.2), -2)
                    bus_price = round(eco_price * random.uniform(2.5, 4.0), -2)
                    first_price = round(eco_price * random.uniform(5.0, 8.0), -2)

                    eco_cap = random.randint(120, 180)
                    bus_cap = random.randint(20, 40)
                    first_cap = random.randint(8, 16)

                    # Randomly use some seats
                    eco_avail = eco_cap - random.randint(0, eco_cap // 3)
                    bus_avail = bus_cap - random.randint(0, bus_cap // 3)
                    first_avail = first_cap - random.randint(0, first_cap // 3)

                    Flight.objects.create(
                        flight_number=fn,
                        airline=airline_name,
                        origin=airport_map[origin_code],
                        destination=airport_map[dest_code],
                        departure_time=dep_dt,
                        arrival_time=arr_dt,
                        aircraft_type=aircraft,
                        status='scheduled',
                        economy_capacity=eco_cap,
                        economy_available=eco_avail,
                        economy_price=eco_price,
                        business_capacity=bus_cap,
                        business_available=bus_avail,
                        business_price=bus_price,
                        first_capacity=first_cap,
                        first_available=first_avail,
                        first_price=first_price,
                    )
                    flight_count += 1

        self.stdout.write(f'  Created {flight_count} flights.')

        self.stdout.write('Creating users...')

        # Create demo users without hardcoded passwords
        demo_users = [
            {
                'username': 'user1',
                'first_name': 'Rahul',
                'last_name': 'Sharma',
                'email': 'rahul@example.com'
            },
            {
                'username': 'user2',
                'first_name': 'Priya',
                'last_name': 'Patel',
                'email': 'priya@example.com'
            }
        ]

        created_users = []

        for ud in demo_users:
            if not User.objects.filter(username=ud['username']).exists():
                u = User.objects.create_user(
                    username=ud['username'],
                    email=ud['email'],
                    first_name=ud['first_name'],
                    last_name=ud['last_name']
                )
                u.set_unusable_password()
                u.save()
                created_users.append(u)
                self.stdout.write(f"  Created demo user: {ud['username']}")

        # Seed sample bookings
        if created_users:
            self.stdout.write('Seeding sample bookings...')

            flights_list = list(Flight.objects.all()[:20])

            if flights_list:
                for u in created_users:
                    for _ in range(random.randint(2, 4)):
                        flight = random.choice(flights_list)
                        sc = random.choice(['economy', 'business'])
                        num_p = random.randint(1, 2)
                        price = flight.get_price(sc) * num_p

                        booking = Booking.objects.create(
                            user=u,
                            flight=flight,
                            seat_class=sc,
                            num_passengers=num_p,
                            total_price=price,
                            status='confirmed'
                        )

                        names = [
                            ('Amit', 'Kumar'),
                            ('Sunita', 'Verma'),
                            ('Rajan', 'Mehta'),
                            ('Anjali', 'Singh'),
                            ('Vikram', 'Nair'),
                            ('Pooja', 'Reddy')
                        ]

                        seat_letters = ['A', 'B', 'C', 'D', 'E', 'F']

                        for j in range(num_p):
                            fn, ln = random.choice(names)

                            Passenger.objects.create(
                                booking=booking,
                                first_name=fn,
                                last_name=ln,
                                date_of_birth=datetime.date(
                                    random.randint(1970, 2000),
                                    random.randint(1, 12),
                                    random.randint(1, 28)
                                ),
                                passport_number='P' + str(random.randint(1000000, 9999999)),
                                nationality='Indian',
                                seat_number=f"{random.randint(1, 30)}{random.choice(seat_letters)}"
                            )

                self.stdout.write('  Sample bookings created.')

        self.stdout.write(
            self.style.SUCCESS('\n[OK] Database seeded successfully!')
        )
