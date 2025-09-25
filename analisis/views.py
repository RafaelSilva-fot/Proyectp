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

from typing import List, Tuple, Dict
from django.utils.html import escape
from django.urls import reverse
from django.http import StreamingHttpResponse
import csv
from django.http import JsonResponse


from django.http import HttpResponse
from collections import Counter, defaultdict




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

SENT_START = "<s>"
SENT_END = "</s>"

def tokenizar_palabras(texto: str) -> List[str]:
    tokens = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ']+", texto)
    return [normalizar_palabra(t) for t in tokens if len(t) > 0]

def segmentar_oraciones(texto: str):
    # Divide por ., !, ?, … (puntos suspensivos) y tokeniza cada oración
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


def prob_ngramas(request, pk, n):
    """Tabla HTML con MLE para n-gramas. Añade ?fronteras=1 para usar <s>, </s>."""
    n = int(n)
    texto = get_object_or_404(TextoAnalizado, pk=pk)
    with open(texto.archivo.path, 'r', encoding='utf-8', errors='ignore') as f:
        contenido = f.read()

    usar_fronteras = request.GET.get('fronteras') in ('1', 'true', 'True', 'yes', 'on')
    tokens = preparar_tokens_para_mle(contenido, n, usar_fronteras)
    if len(tokens) < n:
        return HttpResponse(f"No hay suficientes tokens para generar {n}-gramas.", status=400)

    filas = mle_probabilidades(tokens, n)
    top = int(request.GET.get('top', '100'))
    filas = filas[:top]

    return render(request, "analisis/prob_ngramas.html", {
        "texto": texto, "n": n, "usar_fronteras": usar_fronteras, "filas": filas,
    })

def comparar_prob_ngramas(request, pk, n):
    """Comparación lado a lado: sin fronteras vs con fronteras."""
    n = int(n)
    texto = get_object_or_404(TextoAnalizado, pk=pk)
    with open(texto.archivo.path, 'r', encoding='utf-8', errors='ignore') as f:
        contenido = f.read()

    
    tokens_a = preparar_tokens_para_mle(contenido, n, usar_fronteras=False)
    filas_a = mle_probabilidades(tokens_a, n) if len(tokens_a) >= n else []

    tokens_b = preparar_tokens_para_mle(contenido, n, usar_fronteras=True)
    filas_b = mle_probabilidades(tokens_b, n) if len(tokens_b) >= n else []

   
    top_q = (request.GET.get('top') or '').strip().lower()
    top = None
    if top_q and top_q != 'all':
        try:
            top = max(1, int(top_q))
        except ValueError:
            top = None  

    if top:
        filas_a = filas_a[:top]
        filas_b = filas_b[:top]

    return render(
        request,
        "analisis/comparar_prob_ngramas.html",
        {
            "texto": texto,
            "n": n,
            "sin_fronteras": filas_a,
            "con_fronteras": filas_b,
            "top": top_q,  
        },
    )

def prob_ngramas_csv(request, pk, n):
    """Descarga CSV de la tabla MLE (con o sin fronteras)."""
    n = int(n)
    texto = get_object_or_404(TextoAnalizado, pk=pk)
    with open(texto.archivo.path, 'r', encoding='utf-8', errors='ignore') as f:
        contenido = f.read()

    usar_fronteras = request.GET.get('fronteras') in ('1','true','True','yes','on')
    tokens = preparar_tokens_para_mle(contenido, n, usar_fronteras)
    if len(tokens) < n:
        return HttpResponse(f"No hay suficientes tokens para generar {n}-gramas.", status=400)

    filas = mle_probabilidades(tokens, n)
    top = int(request.GET.get('top', '100'))
    filas = filas[:top]

    def rows():
        yield ["n", "usar_fronteras", "n-grama", "conteo", "historial", "conteo_historial", "probabilidad"]
        for r in filas:
            yield [n, int(usar_fronteras), r["ngrama"], r["conteo"], r["historial"], r["conteo_hist"], f'{r["prob"]:.10f}']

    class Echo:
        def write(self, value): return value

    writer = csv.writer(Echo())
    resp = StreamingHttpResponse((writer.writerow(row) for row in rows()), content_type="text/csv")
    resp['Content-Disposition'] = f'attachment; filename="mle_{pk}_{n}_{"fronteras" if usar_fronteras else "sin_fronteras"}.csv"'
    return resp


def api_contenido(request, pk):

    texto = get_object_or_404(TextoAnalizado, pk=pk)

    try:
        with open(texto.archivo.path, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    max_param = request.GET.get('max', '')
    if max_param in ('', 'all'):
        snippet = contenido
        truncated = False
    else:
        try:
            m = int(max_param)
        except ValueError:
            m = 1500
        if m <= 0:
            snippet = contenido
            truncated = False
        else:
            snippet = contenido[:m]
            truncated = len(contenido) > m

    return JsonResponse({
        "pk": pk,
        "snippet": snippet,
        "truncated": truncated,
        "total_len": len(contenido),
    })


_word_re = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ']+")

def _tokenizar_query(q: str):
    """Devuelve (tokens_normalizados, termina_con_espacio)."""
    ends_space = bool(re.search(r"\s$", q or ""))
    toks = _word_re.findall(q or "")
    toks = [normalizar_palabra(t) for t in toks if t]
    return toks, ends_space

def _build_all_next_counts(stream, max_n):
    """
    Para cada orden k (2..max_n) construye:
    hist(tuple len k-1) -> Counter(next_token)
    """
    all_counts = [None] * (max_n + 1)
    for k in range(2, max_n + 1):
        d = defaultdict(Counter)

        for i in range(len(stream) - k + 1):
            hist = tuple(stream[i : i + k - 1])
            nxt  = stream[i + k - 1]
            d[hist][nxt] += 1
        all_counts[k] = d
    return all_counts

def api_sugerencias(request, pk):
    texto = get_object_or_404(TextoAnalizado, pk=pk)
    with open(texto.archivo.path, "r", encoding="utf-8", errors="ignore") as f:
        contenido = f.read()

    try: n = int(request.GET.get("n", "2") or 2)
    except: n = 2
    try: top = int(request.GET.get("top", "8") or 8)
    except: top = 8
    usar_fronteras = request.GET.get("fronteras", "0") in ("1","true","True","on")
    q = request.GET.get("q", "") or ""

    stream = tokens_para_tabla(contenido, max(n,1), usar_fronteras)
    if not stream:
        return JsonResponse({"items": [], "order_used": 0})

   
    q_toks, ends_space = _tokenizar_query(q)
    if ends_space:
        history = q_toks[-(n-1):] if n>1 else []
        prefix = ""
    else:
        prefix  = q_toks[-1] if q_toks else ""
        base    = q_toks[:-1] if q_toks else []
        history = base[-(n-1):] if n>1 else []

    all_next = _build_all_next_counts(stream, max_n=max(n,2))
    uni = Counter(stream)
    total_uni = sum(uni.values()) or 1

    items = []
    order_used = None

    cur_n = n
    while cur_n >= 2 and not items:
        hist_tuple = tuple(history[-(cur_n-1):]) if (cur_n>1 and history) else tuple()
        counts = all_next[cur_n].get(hist_tuple) if all_next[cur_n] else None
        if counts:
            total_h = sum(counts.values()) or 1
            tmp = []
            for w,c in counts.items():
                if w in (SENT_START, SENT_END): continue
                if prefix and not w.startswith(prefix): continue
                tmp.append((w, c/total_h))
            items = sorted(tmp, key=lambda x: (-x[1], x[0]))
            order_used = cur_n
        cur_n -= 1


    if not items and prefix:
        history = history + [prefix]
        prefix = ""
        cur_n = n
        while cur_n >= 2 and not items:
            hist_tuple = tuple(history[-(cur_n-1):]) if (cur_n>1 and history) else tuple()
            counts = all_next[cur_n].get(hist_tuple) if all_next[cur_n] else None
            if counts:
                total_h = sum(counts.values()) or 1
                tmp = []
                for w,c in counts.items():
                    if w in (SENT_START, SENT_END): continue
                    tmp.append((w, c/total_h))
                items = sorted(tmp, key=lambda x: (-x[1], x[0]))
                order_used = cur_n
            cur_n -= 1

    
    if not items:
        tmp = []
        for w,c in uni.items():
            if w in (SENT_START, SENT_END): continue
            if prefix and not w.startswith(prefix): continue
            tmp.append((w, c/total_uni))
        items = sorted(tmp, key=lambda x: (-x[1], x[0]))
        order_used = 1

    items = items[:max(1, top)]
    return JsonResponse({"items":[{"word":w,"prob":float(p)} for w,p in items],
                         "order_used": order_used})

    
def tokenizar_palabras(texto: str):
    toks = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ']+", texto)
    return [normalizar_palabra(t) for t in toks if t]

def segmentar_oraciones(texto: str):
    partes = re.split(r"[.!?…]+", texto)
    out = []
    for p in partes:
        t = tokenizar_palabras(p)
        if t:
            out.append(t)
    return out

def tokens_para_tabla(contenido: str, n: int, usar_fronteras: bool):
    """Stream de tokens para tablas. Con fronteras:
       - n=1: <s> x1 al inicio de cada oración, </s> al final
       - n>=2: <s> repetido (n-1) al inicio de cada oración y </s> al final
    """
    if not usar_fronteras:
        return tokenizar_palabras(contenido)

    oraciones = segmentar_oraciones(contenido)
    if n <= 1:
        stream = []
        for toks in oraciones:
            stream.append(SENT_START)
            stream.extend(toks)
            stream.append(SENT_END)
        return stream
    else:
        k = n - 1
        stream = []
        for toks in oraciones:
            stream.extend([SENT_START] * k)
            stream.extend(toks)
            stream.append(SENT_END)
        return stream

def tabla_unigramas(request, pk):
    texto = get_object_or_404(TextoAnalizado, pk=pk)
    with open(texto.archivo.path, 'r', encoding='utf-8', errors='ignore') as f:
        contenido = f.read()

    usar_fronteras = request.GET.get('fronteras', '0') in ('1', 'true', 'True', 'on')

    stream = tokens_para_tabla(contenido, 1, usar_fronteras)
    counter = Counter(stream)
    total = sum(counter.values())

    filas = []
    for token, c in counter.most_common():
        pct = (c / total * 100) if total else 0.0
        filas.append({"token": token, "conteo": c, "pct": pct})

    ctx = {
        "texto": texto,
        "total": total,
        "filas": filas,
        "fronteras": usar_fronteras,   
    }
    return render(request, "analisis/tabla_unigramas.html", ctx)


def tabla_ngramas(request, pk, n):
    texto = get_object_or_404(TextoAnalizado, pk=pk)
    with open(texto.archivo.path, 'r', encoding='utf-8', errors='ignore') as f:
        contenido = f.read()

    usar_fronteras = request.GET.get('fronteras', '0') in ('1', 'true', 'True', 'on')

    stream = tokens_para_tabla(contenido, n, usar_fronteras)
    if n < 1 or len(stream) < n:
        return render(request, "analisis/tabla_ngramas.html",
                      {"texto": texto, "n": n, "total": 0, "filas": [], "fronteras": usar_fronteras})

    ngramas = [' '.join(stream[i:i+n]) for i in range(len(stream) - n + 1)]
    counter = Counter(ngramas)
    total = sum(counter.values())

    filas = []
    for ng, c in counter.most_common():
        pct = (c / total * 100) if total else 0.0
        filas.append({"ngrama": ng, "conteo": c, "pct": pct})

    ctx = {
        "texto": texto,
        "n": n,
        "total": total,
        "filas": filas,
        "fronteras": usar_fronteras,  
    }
    return render(request, "analisis/tabla_ngramas.html", ctx)
