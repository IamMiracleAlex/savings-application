from django.shortcuts import render, redirect
from .forms import SignUpForm
from django.contrib import messages
from users.views import send_activate_email
from users.models import CustomUser
# Create your views here.

def index(request):
	return render(request, 'web/index.html')

def register(request):
	if request.method == 'POST':
		form = SignUpForm(request.POST)
		if form.is_valid():
			user = form.save()
			send_activate_email(request, user)
			messages.success(request, 'You have signed up successfully!. Download our app to start saving')
			return redirect('web:index')
	else:
		form = SignUpForm()
	return render(request, 'registration/register.html', {'form': form})

def referral_signup(request, refer_code):
	if request.method == 'POST':
		form = SignUpForm(request.POST)
		if form.is_valid():
			user = form.save()
			referer = CustomUser.objects.filter(refer_code=refer_code.lower()).first()
			if referer:
				user.referer = referer
				user.save()
			send_activate_email(request, user)
			messages.success(request, 'You have signed up successfully!. Download our app to start saving')
			return redirect('web:index')
	else:
		form = SignUpForm()
	return render(request, 'registration/register.html', {'form': form})

def terms(request):
	return render(request, 'web/terms_and_conditions.html')

def faq(request):
    	return render(request, 'web/faq.html')
		
def about(request):
	return render(request, 'web/about.html')
