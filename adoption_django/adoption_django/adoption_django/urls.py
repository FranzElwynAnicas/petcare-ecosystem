from django.contrib import admin
from django.urls import path, include
from core.admin import shelter_admin_site 

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('admin/', shelter_admin_site.urls),
    path('', include('core.urls')),  # This includes ALL URLs from core app
]