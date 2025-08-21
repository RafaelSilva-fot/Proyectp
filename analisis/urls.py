# analisis/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('subir/', views.subir_texto, name='subir_texto'),
    path('', views.lista_textos, name='lista_textos'),
    path('histograma/<int:pk>/', views.histograma_palabras, name='histograma'),
]


urlpatterns = [
    path('', views.lista_textos, name='lista_textos'),
    path('subir/', views.subir_texto, name='subir_texto'),
    path('histograma/<int:pk>/', views.histograma_palabras, name='histograma_palabras'),

]
