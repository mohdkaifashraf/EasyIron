from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Address, CustomerProfile

User = get_user_model()


class CustomerSignUpForm(forms.Form):
    name = forms.CharField(
        label="Name",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Your full name"}),
    )
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "you@example.com"}),
    )
    mobile = forms.CharField(
        label="Mobile number",
        max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "+91 98765 43210"}),
    )
    location = forms.CharField(
        label="Address",
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Home address or landmark"}),
    )
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Enter a strong password"}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirm your password"}),
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError("A user with that email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("The two password fields didn’t match.")

        if password1:
            validate_password(password1)

        return cleaned_data

    def save(self, commit=True):
        email = self.cleaned_data["email"]
        user = User.objects.create_user(
            username=email,
            email=email,
            password=self.cleaned_data["password1"],
            first_name=self.cleaned_data["name"],
        )
        if commit:
            user.save()
            CustomerProfile.objects.create(
                user=user,
                mobile=self.cleaned_data["mobile"],
                address=self.cleaned_data["location"],
            )
        return user


class ProfileUpdateForm(forms.Form):
    name = forms.CharField(
        label="Name",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Your full name"}),
    )
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "you@example.com"}),
    )
    mobile = forms.CharField(
        label="Mobile number",
        max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "+91 98765 43210"}),
    )
    address = forms.CharField(
        label="Address",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Home address or landmark"}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and self.user and email.lower() != self.user.email.lower():
            if User.objects.filter(email__iexact=email).exists():
                raise ValidationError("A user with that email address already exists.")
        return email

    def save(self):
        if not self.user:
            raise ValueError("User is required to save profile data.")

        self.user.first_name = self.cleaned_data["name"]
        self.user.email = self.cleaned_data["email"]
        self.user.username = self.cleaned_data["email"]
        self.user.save()

        profile, _ = CustomerProfile.objects.get_or_create(user=self.user)
        profile.mobile = self.cleaned_data["mobile"]
        profile.address = self.cleaned_data["address"]
        profile.save()

        return self.user


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ["label", "line1", "line2", "city", "state", "postal_code", "country", "is_default"]
        widgets = {
            "label": forms.TextInput(attrs={"class": "form-control", "placeholder": "Home / Work / Other"}),
            "line1": forms.TextInput(attrs={"class": "form-control", "placeholder": "Street address"}),
            "line2": forms.TextInput(attrs={"class": "form-control", "placeholder": "Apartment, suite, unit (optional)"}),
            "city": forms.TextInput(attrs={"class": "form-control", "placeholder": "City"}),
            "state": forms.TextInput(attrs={"class": "form-control", "placeholder": "State"}),
            "postal_code": forms.TextInput(attrs={"class": "form-control", "placeholder": "Postal code"}),
            "country": forms.TextInput(attrs={"class": "form-control", "placeholder": "Country"}),
            "is_default": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class AccountSettingsForm(forms.ModelForm):
    class Meta:
        model = CustomerProfile
        fields = ["allow_marketing", "share_data"]
        widgets = {
            "allow_marketing": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "share_data": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
