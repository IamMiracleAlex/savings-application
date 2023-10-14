from django.contrib import admin

def admin_header_processor(request):
    return {"site_header": "Savest"}