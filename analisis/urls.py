# analisis/urls.py
from django.urls import path
from . import views





   

urlpatterns = [
    path('lista/', views.lista_textos, name='lista_textos'),
    path('', views.subir_texto, name='subir_texto'),
    path('histograma/<int:pk>/', views.histograma_palabras, name='histograma_palabras'),
    path('elegir-ngrama/<int:pk>/', views.elegir_ngrama, name='elegir_ngrama'),
    path('histograma-ngramas/<int:pk>/<int:n>/', views.histograma_ngramas, name='histograma_ngramas'),
    path('prob_ngramas/<int:pk>/<int:n>/', views.prob_ngramas, name='prob_ngramas'),
    path('comparar_prob_ngramas/<int:pk>/<int:n>/', views.comparar_prob_ngramas, name='comparar_prob_ngramas'),
    path('api/contenido/<int:pk>/', views.api_contenido, name='api_contenido'),
    path('api/sugerencias/<int:pk>/', views.api_sugerencias, name='api_sugerencias'),
    path('tabla-unigramas/<int:pk>/', views.tabla_unigramas, name='tabla_unigramas'),
    path('tabla-ngramas/<int:pk>/<int:n>/', views.tabla_ngramas, name='tabla_ngramas'),
    
]
