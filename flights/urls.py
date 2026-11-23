from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Flight search
    path('flights/search/', views.flight_results, name='flight_results'),

    # Booking flow
    path('flights/<int:flight_id>/book/', views.booking, name='booking'),
    path('booking/confirmation/<str:booking_ref>/', views.confirmation, name='confirmation'),
    path('booking/history/', views.booking_history, name='booking_history'),
    path('booking/cancel/<str:booking_ref>/', views.cancel_booking, name='cancel_booking'),

    # Admin dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # API
    path('api/airports/', views.airport_search_api, name='airport_search_api'),
]
