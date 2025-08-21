from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .forms import TextoAnalizadoForm
from .models import TextoAnalizado

# --- librerías para el histograma ---
import re
from collections import Counter
import matplotlib
matplotlib.use('Agg')  # backend sin ventana
import matplotlib.pyplot as plt
from io import BytesIO

# Stopwords muy básicas (puedes ampliarlas o usar nltk)
STOPWORDS = {
    'de','la','que','el','en','y','a','los','del','se','las','por','un','para','con',
    'no','una','su','al','lo','como','o','pero','sus','le','ya','sí','porque','muy',
    'sin','sobre','también','me','hasta','hay','donde','quien','desde','todo','todos'
}

def histograma_palabras(request, pk):
    """Devuelve una imagen PNG con todas las palabras encontradas en el texto."""
    texto = get_object_or_404(TextoAnalizado, pk=pk)

    # leer archivo
    with open(texto.archivo.path, 'r', encoding='utf-8', errors='ignore') as f:
        contenido = f.read()

    # tokenizar (minúsculas, letras con acentos)
    tokens = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ']+", contenido.lower())
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]

    # contar palabras
    counter = Counter(tokens)
    palabras, freqs = zip(*counter.most_common()) if counter else ([], [])

    # gráfico estético
    fig, ax = plt.subplots(figsize=(18, 9))  # más grande y legible

    if palabras:
        bars = ax.bar(palabras, freqs, color="skyblue", edgecolor="black")

        # título y etiquetas
        ax.set_title("Frecuencia de Palabras en el Texto", fontsize=20, fontweight='bold')
        ax.set_xlabel("Palabras", fontsize=16)
        ax.set_ylabel("Frecuencia", fontsize=16)

        # rotación y tamaño de etiquetas
        plt.xticks(rotation=90, ha='right', fontsize=12)
        plt.yticks(fontsize=12)

        # agregar números encima de cada barra
        for bar, freq in zip(bars, freqs):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    str(freq), ha='center', va='bottom', fontsize=10, color="black")

        plt.tight_layout()
    else:
        plt.text(0.5, 0.5, 'Sin palabras suficientes',
                 ha='center', va='center', fontsize=14)
        plt.axis('off')

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=120)  # mejor resolución
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



#amklcas