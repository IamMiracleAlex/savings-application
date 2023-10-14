from django.contrib.auth.forms import UserCreationForm
from django import forms
from users.models import CustomUser

class SignUpForm(UserCreationForm):
	class Meta:
		model = CustomUser
		fields = ['first_name', 'last_name', 'email', 'phone_number', 'password1', 'password2']