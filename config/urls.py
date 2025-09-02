"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from analisis import views  # ✅ Importa las vistas directamente

urlpatterns = [
    path('admin/', admin.site.urls),
    path('subir/', include('analisis.urls')),
    # ✅ AÑADE ESTAS URLs DIRECTAMENTE:
    path('elegir-ngrama/<int:pk>/', views.elegir_ngrama, name='elegir_ngrama'),
    path('histograma-ngramas/<int:pk>/<int:n>/', views.histograma_ngramas, name='histograma_ngramas'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)