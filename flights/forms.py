from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Booking, Passenger, Flight, Airport
from django.forms import formset_factory
import datetime


class FlightSearchForm(forms.Form):
    origin = forms.ModelChoiceField(
        queryset=Airport.objects.all(),
        empty_label="Select Origin",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_origin'})
    )
    destination = forms.ModelChoiceField(
        queryset=Airport.objects.all(),
        empty_label="Select Destination",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_destination'})
    )
    departure_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'id_departure_date',
            'min': datetime.date.today().isoformat()
        })
    )
    num_passengers = forms.IntegerField(
        min_value=1,
        max_value=9,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_num_passengers'})
    )
    seat_class = forms.ChoiceField(
        choices=[
            ('economy', 'Economy'),
            ('business', 'Business'),
            ('first', 'First Class'),
        ],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_seat_class'})
    )

    def clean(self):
        cleaned_data = super().clean()
        origin = cleaned_data.get('origin')
        destination = cleaned_data.get('destination')
        if origin and destination and origin == destination:
            raise forms.ValidationError("Origin and destination cannot be the same airport.")
        return cleaned_data


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=30, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username', 'autofocus': True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )


class PassengerForm(forms.ModelForm):
    class Meta:
        model = Passenger
        fields = ['first_name', 'last_name', 'date_of_birth', 'passport_number', 'nationality']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'passport_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Passport / ID Number'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nationality'}),
        }


class BookingForm(forms.Form):
    seat_class = forms.ChoiceField(
        choices=[
            ('economy', 'Economy'),
            ('business', 'Business'),
            ('first', 'First Class'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'btn-check'})
    )
    num_passengers = forms.IntegerField(
        min_value=1, max_value=9,
        widget=forms.HiddenInput()
    )
