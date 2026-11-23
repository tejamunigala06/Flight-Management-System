from django.contrib import admin
from .models import Airport, Flight, Booking, Passenger


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'city', 'country']
    search_fields = ['code', 'name', 'city', 'country']
    ordering = ['code']


class PassengerInline(admin.TabularInline):
    model = Passenger
    extra = 0
    readonly_fields = ['first_name', 'last_name', 'date_of_birth', 'passport_number', 'nationality', 'seat_number']


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ['flight_number', 'airline', 'origin', 'destination', 'departure_time', 'arrival_time', 'status',
                    'economy_available', 'business_available', 'first_available']
    list_filter = ['airline', 'status', 'departure_time']
    search_fields = ['flight_number', 'origin__city', 'destination__city', 'airline']
    ordering = ['departure_time']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Flight Info', {
            'fields': ('flight_number', 'airline', 'aircraft_type', 'status')
        }),
        ('Route', {
            'fields': ('origin', 'destination', 'departure_time', 'arrival_time')
        }),
        ('Economy', {
            'fields': ('economy_capacity', 'economy_available', 'economy_price')
        }),
        ('Business', {
            'fields': ('business_capacity', 'business_available', 'business_price')
        }),
        ('First Class', {
            'fields': ('first_capacity', 'first_available', 'first_price')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_reference', 'user', 'flight', 'seat_class', 'num_passengers', 'total_price', 'status', 'created_at']
    list_filter = ['status', 'seat_class', 'created_at']
    search_fields = ['booking_reference', 'user__username', 'flight__flight_number']
    readonly_fields = ['booking_reference', 'created_at', 'updated_at']
    inlines = [PassengerInline]


@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'booking', 'passport_number', 'nationality', 'seat_number']
    search_fields = ['first_name', 'last_name', 'passport_number']
