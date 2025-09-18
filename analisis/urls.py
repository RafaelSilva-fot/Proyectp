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
]
