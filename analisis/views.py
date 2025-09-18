from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .forms import TextoAnalizadoForm
from .models import TextoAnalizado

import re
import unicodedata
from collections import Counter
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from io import BytesIO
from django import forms  
#--------------------------------extra
from typing import List, Tuple, Dict
from django.utils.html import escape
from django.urls import reverse
from django.http import StreamingHttpResponse
import csv



class NgramForm(forms.Form):
    n_valor = forms.IntegerField(
        label='Valor de n para n-gramas',
        min_value=1,
        initial=1,
        help_text='1: Unigramas, 2: Bigramas, 3: Trigramas, etc.'
    )
def normalizar_palabra(palabra):
    """Convierte la palabra a minúsculas y elimina acentos/diacríticos."""
    palabra = palabra.lower()
    palabra = unicodedata.normalize('NFD', palabra)
    palabra = ''.join(ch for ch in palabra if unicodedata.category(ch) != 'Mn')
    return palabra

def generar_ngramas(tokens, n):
    """Genera n-gramas a partir de una lista de tokens"""
    if n <= 0:
        raise ValueError("n debe ser mayor a 0")
    if n == 1:
        return tokens 
    return [' '.join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]

#----------------------Extra-------------------

SENT_START = "<s>"
SENT_END = "</s>"

def tokenizar_palabras(texto: str) -> List[str]:
    tokens = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ']+", texto)
    return [normalizar_palabra(t) for t in tokens if len(t) > 0]

def segmentar_oraciones(texto: str):
    
    oraciones_raw = re.split(r"[.!?…]+", texto)
    res = []
    for oracion in oraciones_raw:
        toks = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ']+", oracion)
        toks = [normalizar_palabra(t) for t in toks if len(t) > 0]
        if toks:
            res.append(toks)
    return res

def aplicar_fronteras(oraciones_tokens, n: int):
  
    k = max(0, n - 1)
    stream = []
    for toks in oraciones_tokens:
        stream.extend([SENT_START] * k)
        stream.extend(toks)
        stream.append(SENT_END)
    return stream

def ngramas_y_historial(tokens: List[str], n: int):
  
    if n <= 0:
        raise ValueError("n debe ser mayor a 0")
    if n == 1:
        unis = Counter(tokens)
        total = sum(unis.values())
        return unis, Counter({"": total})
    ngrams = Counter()
    histories = Counter()
    L = len(tokens)
    for i in range(L - n + 1):
        window = tokens[i:i+n]
        hist = tuple(window[:-1])
        ngram = tuple(window)
        ngrams[ngram] += 1
        histories[hist] += 1
    return ngrams, histories

def mle_probabilidades(tokens: List[str], n: int):

    ngrams, histories = ngramas_y_historial(tokens, n)
    filas = []
    if n == 1:
        total = sum(ngrams.values())
        for ng, c in ngrams.most_common():
            prob = c / total if total > 0 else 0.0
            filas.append({"ngrama": ng, "conteo": c, "historial": "", "conteo_hist": total, "prob": prob})
        return filas
    for ng, c in ngrams.most_common():
        hist = tuple(list(ng)[:-1])
        ch = histories.get(hist, 0)
        prob = (c / ch) if ch > 0 else 0.0
        filas.append({
            "ngrama": " ".join(ng),
            "conteo": c,
            "historial": " ".join(hist),
            "conteo_hist": ch,
            "prob": prob
        })
    filas.sort(key=lambda r: (-r["conteo"], -r["prob"]))
    return filas

def preparar_tokens_para_mle(contenido: str, n: int, usar_fronteras: bool):
   
    if usar_fronteras:
        oraciones = segmentar_oraciones(contenido)
        return aplicar_fronteras(oraciones, n)
    else:
        return tokenizar_palabras(contenido)



#-------------------------Extra---------------
def histograma_palabras(request, pk):
    """Devuelve una imagen PNG con todas las palabras encontradas en el texto."""
    texto = get_object_or_404(TextoAnalizado, pk=pk)

    with open(texto.archivo.path, 'r', encoding='utf-8', errors='ignore') as f:
        contenido = f.read()

 
    tokens = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ']+", contenido)

    tokens_norm = [normalizar_palabra(t) for t in tokens if len(t) > 1]


    counter = Counter(tokens_norm)
    palabras, freqs = zip(*counter.most_common()) if counter else ([], [])


    fig, ax = plt.subplots(figsize=(20, 10))  

    if palabras:
        bars = ax.bar(palabras, freqs, color="black", edgecolor="gray")

        ax.set_title("Frecuencia de Palabras en el Texto", fontsize=22, fontweight='bold')
        ax.set_xlabel("Palabras", fontsize=16)
        ax.set_ylabel("Frecuencia", fontsize=16)


        ax.yaxis.set_major_locator(MultipleLocator(1))

        plt.xticks(rotation=90, ha='center', fontsize=11)
        plt.yticks(fontsize=12)

        for bar, freq in zip(bars, freqs):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    str(freq), ha='center', va='bottom', fontsize=10, color="black")

        plt.tight_layout()
    else:
        plt.text(0.5, 0.5, 'Sin palabras suficientes',
                 ha='center', va='center', fontsize=14)
        plt.axis('off')

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=120)  
    plt.close(fig)
    return HttpResponse(buf.getvalue(), content_type='image/png')


def subir_texto(request):
    if request.method == 'POST':
        form = TextoAnalizadoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('lista_textos')
    else:
        form = TextoAnalizadoForm()
    return render(request, 'analisis/subir.html', {'form': form})


def lista_textos(request):
    textos = TextoAnalizado.objects.all().order_by('-fecha_subida')
    return render(request, 'analisis/listar.html', {'textos': textos})


def elegir_ngrama(request, pk):
    """Vista para elegir el valor de n para n-gramas"""
    texto = get_object_or_404(TextoAnalizado, pk=pk)
    
    if request.method == 'POST':
        form = NgramForm(request.POST)
        if form.is_valid():
            n = form.cleaned_data['n_valor']
           
            return redirect('histograma_ngramas', pk=pk, n=n)
    else:
        form = NgramForm()
    
    return render(request, 'analisis/elegir_ngrama.html', {
        'form': form,
        'texto': texto
    })
    
    
def histograma_ngramas(request, pk, n):
    """Devuelve un histograma de n-gramas"""
    texto = get_object_or_404(TextoAnalizado, pk=pk)

    with open(texto.archivo.path, 'r', encoding='utf-8', errors='ignore') as f:
        contenido = f.read()

   
    tokens = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ']+", contenido)
    tokens_norm = [normalizar_palabra(t) for t in tokens if len(t) > 1]

    if not tokens_norm or len(tokens_norm) < n:
        return HttpResponse("No hay suficientes palabras para generar {}-gramas.".format(n))

    
    ngramas = generar_ngramas(tokens_norm, n)
    counter = Counter(ngramas)
    

    elementos, freqs = zip(*counter.most_common(20)) if counter else ([], [])

 
    fig, ax = plt.subplots(figsize=(20, 10))
    
    if elementos:
        bars = ax.bar(elementos, freqs, color="gray", edgecolor="black")

        ax.set_title("Frecuencia de {}-gramas en el Texto".format(n), 
                    fontsize=22, fontweight='bold')
        ax.set_xlabel("{}-gramas".format(n), fontsize=16)
        ax.set_ylabel("Frecuencia", fontsize=16)
        
        plt.xticks(rotation=90, ha='center', fontsize=11)
        plt.yticks(fontsize=12)

        for bar, freq in zip(bars, freqs):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() -0.5,
                    str(freq), ha='center', va='bottom', fontsize=10, color="black")
        
        plt.tight_layout()
    else:
        plt.text(0.5, 0.5, 'Sin {}-gramas suficientes'.format(n),
                 ha='center', va='center', fontsize=14)
        plt.axis('off')

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=120)
    plt.close(fig)
    return HttpResponse(buf.getvalue(), content_type='image/png')


