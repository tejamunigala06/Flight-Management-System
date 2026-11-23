from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.forms import formset_factory
from django.http import JsonResponse
import datetime

from .models import Airport, Flight, Booking, Passenger
from .forms import (
    FlightSearchForm, RegisterForm, LoginForm,
    PassengerForm, BookingForm
)


# ─────────────────────────────────────────
# HOME
# ─────────────────────────────────────────
def home(request):
    form = FlightSearchForm()
    airports = Airport.objects.all().order_by('city')
    featured_destinations = [
        {'city': 'Dubai', 'country': 'UAE', 'code': 'DXB', 'img': 'dubai'},
        {'city': 'London', 'country': 'UK', 'code': 'LHR', 'img': 'london'},
        {'city': 'Singapore', 'country': 'Singapore', 'code': 'SIN', 'img': 'singapore'},
        {'city': 'New York', 'country': 'USA', 'code': 'JFK', 'img': 'newyork'},
    ]
    # Stats for hero
    total_flights = Flight.objects.filter(status='scheduled').count()
    total_destinations = Airport.objects.count()
    total_airlines = Flight.objects.values('airline').distinct().count()
    context = {
        'form': form,
        'airports': airports,
        'featured_destinations': featured_destinations,
        'total_flights': total_flights,
        'total_destinations': total_destinations,
        'total_airlines': total_airlines,
    }
    return render(request, 'home.html', context)


# ─────────────────────────────────────────
# FLIGHT SEARCH RESULTS
# ─────────────────────────────────────────
def flight_results(request):
    form = FlightSearchForm(request.GET or None)
    flights = Flight.objects.none()
    search_params = {}

    if request.GET and form.is_valid():
        origin = form.cleaned_data['origin']
        destination = form.cleaned_data['destination']
        departure_date = form.cleaned_data['departure_date']
        num_passengers = form.cleaned_data['num_passengers']
        seat_class = form.cleaned_data['seat_class']

        search_params = {
            'origin': origin,
            'destination': destination,
            'departure_date': departure_date,
            'num_passengers': num_passengers,
            'seat_class': seat_class,
        }

        # Filter flights by route and date
        flights = Flight.objects.filter(
            origin=origin,
            destination=destination,
            departure_time__date=departure_date,
            status__in=['scheduled', 'boarding'],
        ).select_related('origin', 'destination')

        # Filter by seat availability
        if seat_class == 'economy':
            flights = flights.filter(economy_available__gte=num_passengers)
        elif seat_class == 'business':
            flights = flights.filter(business_available__gte=num_passengers)
        elif seat_class == 'first':
            flights = flights.filter(first_available__gte=num_passengers)

        # Sorting
        sort_by = request.GET.get('sort', 'price')
        if sort_by == 'price':
            if seat_class == 'economy':
                flights = flights.order_by('economy_price')
            elif seat_class == 'business':
                flights = flights.order_by('business_price')
            else:
                flights = flights.order_by('first_price')
        elif sort_by == 'duration':
            flights = sorted(flights, key=lambda f: f.duration_minutes)
        elif sort_by == 'departure':
            flights = flights.order_by('departure_time')

    # Enrich flights with price and availability for the selected class
    enriched = []
    for flight in flights:
        sc = search_params.get('seat_class', 'economy')
        enriched.append({
            'flight': flight,
            'price': flight.get_price(sc),
            'available': flight.get_available(sc),
            'seat_class': sc,
            'num_passengers': search_params.get('num_passengers', 1),
            'total_price': flight.get_price(sc) * search_params.get('num_passengers', 1),
        })

    context = {
        'form': form,
        'enriched': enriched,
        'search_params': search_params,
        'sort_by': request.GET.get('sort', 'price'),
        'result_count': len(enriched),
        'airports': Airport.objects.all(),
    }
    return render(request, 'flight_results.html', context)


# ─────────────────────────────────────────
# BOOKING
# ─────────────────────────────────────────
@login_required
def booking(request, flight_id):
    flight = get_object_or_404(Flight, id=flight_id)
    num_passengers = int(request.GET.get('num_passengers', 1))
    seat_class = request.GET.get('seat_class', 'economy')

    # Build a dynamic formset
    PassengerFormSet = formset_factory(PassengerForm, extra=num_passengers, max_num=num_passengers)

    if request.method == 'POST':
        formset = PassengerFormSet(request.POST)
        seat_class = request.POST.get('seat_class', 'economy')
        num_passengers = int(request.POST.get('num_passengers', 1))

        if formset.is_valid():
            price_per = flight.get_price(seat_class)
            total_price = price_per * num_passengers

            # Check availability
            available = flight.get_available(seat_class)
            if available < num_passengers:
                messages.error(request, f"Not enough seats available in {seat_class.title()} class.")
                return redirect('booking', flight_id=flight_id)

            # Create booking
            booking_obj = Booking.objects.create(
                user=request.user,
                flight=flight,
                seat_class=seat_class,
                num_passengers=num_passengers,
                total_price=total_price,
                status='confirmed',
            )

            # Assign seat numbers & save passengers
            import random, string
            seat_letters = ['A', 'B', 'C', 'D', 'E', 'F']
            used_seats = set()
            for i, pform in enumerate(formset):
                passenger = pform.save(commit=False)
                passenger.booking = booking_obj
                # Simple seat assignment
                while True:
                    row = random.randint(1, 30)
                    col = random.choice(seat_letters)
                    seat = f"{row}{col}"
                    if seat not in used_seats:
                        used_seats.add(seat)
                        break
                passenger.seat_number = seat
                passenger.save()

            # Decrement available seats
            if seat_class == 'economy':
                flight.economy_available = max(0, flight.economy_available - num_passengers)
            elif seat_class == 'business':
                flight.business_available = max(0, flight.business_available - num_passengers)
            elif seat_class == 'first':
                flight.first_available = max(0, flight.first_available - num_passengers)
            flight.save()

            messages.success(request, f"Booking confirmed! Reference: {booking_obj.booking_reference}")
            return redirect('confirmation', booking_ref=booking_obj.booking_reference)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        formset = PassengerFormSet()

    price_per = flight.get_price(seat_class)
    total_price = price_per * num_passengers

    context = {
        'flight': flight,
        'formset': formset,
        'seat_class': seat_class,
        'num_passengers': num_passengers,
        'price_per': price_per,
        'total_price': total_price,
        'seat_class_display': dict([('economy', 'Economy'), ('business', 'Business'), ('first', 'First Class')]).get(seat_class, 'Economy'),
    }
    return render(request, 'booking.html', context)


# ─────────────────────────────────────────
# BOOKING CONFIRMATION
# ─────────────────────────────────────────
@login_required
def confirmation(request, booking_ref):
    booking_obj = get_object_or_404(Booking, booking_reference=booking_ref, user=request.user)
    passengers = booking_obj.passengers.all()
    context = {
        'booking': booking_obj,
        'passengers': passengers,
    }
    return render(request, 'confirmation.html', context)


# ─────────────────────────────────────────
# BOOKING HISTORY
# ─────────────────────────────────────────
@login_required
def booking_history(request):
    bookings = Booking.objects.filter(user=request.user).select_related('flight__origin', 'flight__destination')
    context = {
        'bookings': bookings,
        'confirmed_count': bookings.filter(status='confirmed').count(),
        'cancelled_count': bookings.filter(status='cancelled').count(),
        'total_spent': bookings.filter(status='confirmed').aggregate(total=Sum('total_price'))['total'] or 0,
        'now': timezone.now(),
    }
    return render(request, 'booking_history.html', context)


# ─────────────────────────────────────────
# CANCEL BOOKING
# ─────────────────────────────────────────
@login_required
def cancel_booking(request, booking_ref):
    booking_obj = get_object_or_404(Booking, booking_reference=booking_ref, user=request.user)
    if booking_obj.status == 'confirmed':
        booking_obj.status = 'cancelled'
        booking_obj.save()

        # Restore seats
        flight = booking_obj.flight
        sc = booking_obj.seat_class
        if sc == 'economy':
            flight.economy_available = min(flight.economy_capacity, flight.economy_available + booking_obj.num_passengers)
        elif sc == 'business':
            flight.business_available = min(flight.business_capacity, flight.business_available + booking_obj.num_passengers)
        elif sc == 'first':
            flight.first_available = min(flight.first_capacity, flight.first_available + booking_obj.num_passengers)
        flight.save()

        messages.success(request, f"Booking {booking_ref} has been cancelled.")
    else:
        messages.warning(request, "This booking is already cancelled.")
    return redirect('booking_history')


# ─────────────────────────────────────────
# ADMIN DASHBOARD
# ─────────────────────────────────────────
@login_required
def dashboard(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access the dashboard.")
        return redirect('home')

    from django.contrib.auth.models import User as AuthUser
    from django.db.models.functions import TruncDate

    total_flights = Flight.objects.count()
    total_bookings = Booking.objects.count()
    total_users = AuthUser.objects.filter(is_staff=False).count()
    total_revenue = Booking.objects.filter(status='confirmed').aggregate(total=Sum('total_price'))['total'] or 0
    confirmed_bookings = Booking.objects.filter(status='confirmed').count()
    cancelled_bookings = Booking.objects.filter(status='cancelled').count()
    scheduled_flights = Flight.objects.filter(status='scheduled').count()
    cancelled_flights = Flight.objects.filter(status='cancelled').count()

    # Recent bookings
    recent_bookings = Booking.objects.select_related(
        'user', 'flight__origin', 'flight__destination'
    ).order_by('-created_at')[:10]

    # Top routes
    top_routes = Booking.objects.filter(status='confirmed').values(
        'flight__origin__city', 'flight__destination__city'
    ).annotate(count=Count('id')).order_by('-count')[:5]

    # Bookings per day (last 7 days)
    seven_days_ago = timezone.now() - datetime.timedelta(days=7)
    bookings_by_day = (
        Booking.objects
        .filter(created_at__gte=seven_days_ago)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    chart_labels = [str(b['date']) for b in bookings_by_day]
    chart_data = [b['count'] for b in bookings_by_day]

    # Revenue by airline
    revenue_by_airline = (
        Booking.objects
        .filter(status='confirmed')
        .values('flight__airline')
        .annotate(revenue=Sum('total_price'))
        .order_by('-revenue')[:6]
    )

    context = {
        'total_flights': total_flights,
        'total_bookings': total_bookings,
        'total_users': total_users,
        'total_revenue': total_revenue,
        'confirmed_bookings': confirmed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'scheduled_flights': scheduled_flights,
        'cancelled_flights': cancelled_flights,
        'recent_bookings': recent_bookings,
        'top_routes': top_routes,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'revenue_by_airline': revenue_by_airline,
    }
    return render(request, 'dashboard.html', context)


# ─────────────────────────────────────────
# AUTHENTICATION
# ─────────────────────────────────────────
def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name}! Your account has been created.")
            return redirect('home')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('home')


# ─────────────────────────────────────────
# API: Airport autocomplete
# ─────────────────────────────────────────
def airport_search_api(request):
    q = request.GET.get('q', '')
    airports = Airport.objects.filter(
        Q(code__icontains=q) | Q(city__icontains=q) | Q(name__icontains=q)
    )[:10]
    data = [{'id': a.id, 'code': a.code, 'city': a.city, 'country': a.country, 'name': a.name} for a in airports]
    return JsonResponse(data, safe=False)
