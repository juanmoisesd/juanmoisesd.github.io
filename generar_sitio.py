"""
Generador del sitio Jekyll para libros de Juan Moisés de la Serna
Lee el CSV de ResearchGate y genera todos los archivos Markdown.

Uso: python generar_sitio.py
"""
import pandas as pd
import re
import os
from pathlib import Path
from datetime import datetime

# ── CONFIG ──────────────────────────────────────────────────────────────────
CSV_PATH  = "libros_researchgate_juan_moises_de_la_serna.csv"
BOOKS_DIR = Path("_books")
BASE_URL  = "https://juanmoisesd.github.io"   # ← URL correcta del sitio
AUTHOR    = "Juan Moisés de la Serna"
ORCID     = "https://orcid.org/0000-0002-8401-8018"
RG_URL    = "https://www.researchgate.net/profile/Juan-Moises-De-La-Serna"

# Prefijos de biblioteca por idioma
LANG_PREFIX = {
    "es": "biblioteca-cientifica-es",
    "en": "scientific-library-en",
    "fr": "bibliotheque-scientifique-fr",
    "de": "wissenschaftliche-bibliothek-de",
    "pt": "biblioteca-cientifica-pt",
    "ar": "biblioteca-ar",
    "it": "biblioteca-scientifica-it",
    "id": "perpustakaan-ilmiah-id",
    "ro": "biblioteca-stiintifica-ro",
}

MONTH_ES = {
    "January":"enero","February":"febrero","March":"marzo","April":"abril",
    "May":"mayo","June":"junio","July":"julio","August":"agosto",
    "September":"septiembre","October":"octubre","November":"noviembre","December":"diciembre"
}

# Transliteración básica árabe → latin para slugs
AR_TRANSLIT = {
    'ا':'a','ب':'b','ت':'t','ث':'th','ج':'j','ح':'h','خ':'kh',
    'د':'d','ذ':'dh','ر':'r','ز':'z','س':'s','ش':'sh','ص':'s',
    'ض':'d','ط':'t','ظ':'z','ع':'a','غ':'gh','ف':'f','ق':'q',
    'ك':'k','ل':'l','م':'m','ن':'n','ه':'h','و':'w','ي':'y',
    'ى':'a','ة':'a','أ':'a','إ':'i','آ':'aa','ؤ':'w','ئ':'y',
    'ذ':'dh','ء':'',
}

def transliterar_arabe(texto: str) -> str:
    resultado = []
    for c in texto:
        if c in AR_TRANSLIT:
            resultado.append(AR_TRANSLIT[c])
        elif ord(c) > 0x0600 and ord(c) < 0x06FF:
            pass  # Ignorar otros caracteres árabes no mapeados
        else:
            resultado.append(c)
    return ''.join(resultado)

# ── UTILIDADES ──────────────────────────────────────────────────────────────
def slugify(text: str) -> str:
    # 1. Transliterar árabe si es necesario
    if any(ord(c) > 0x0600 and ord(c) < 0x06FF for c in text):
        text = transliterar_arabe(text)

    text = text.lower()
    # 2. Reemplazar caracteres con diacríticos
    for a, b in [
        ('á','a'),('é','e'),('í','i'),('ó','o'),('ú','u'),
        ('ä','a'),('ë','e'),('ï','i'),('ö','o'),('ü','u'),
        ('â','a'),('ê','e'),('î','i'),('ô','o'),('û','u'),
        ('à','a'),('è','e'),('ì','i'),('ò','o'),('ù','u'),
        ('ñ','n'),('ç','c'),('ș','s'),('ț','t'),('ă','a'),
        ('ş','s'),('ğ','g'),('ı','i'),
        ("'",""),("«",""),("»",""),("‫",""),("‬",""),("—","-"),
    ]:
        text = text.replace(a, b)
    # 3. Eliminar caracteres no ASCII-safe
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text.strip())
    text = re.sub(r'-+', '-', text)
    slug = text[:70].rstrip('-').lstrip('-')

    # 4. Validar que el slug no quede vacío
    if not slug or len(slug) < 2:
        # Generar slug basado en hash del título original
        import hashlib
        slug = 'libro-' + hashlib.md5(text.encode()).hexdigest()[:8]
    return slug


def detectar_idioma(titulo: str) -> str:
    titulo_lower = titulo.lower()
    # Árabe (caracteres Unicode árabes)
    if any(ord(c) > 0x0600 and ord(c) < 0x06FF for c in titulo):
        return "ar"
    if any(w in titulo_lower for w in ['the ','stress and','psychology','emotional intelligence',
            'abuse','depression','happiness','alexithymia','chronobiology',
            'cyberbullying','psycho-oncology','trends','new ']):
        return "en"
    if any(w in titulo_lower for w in [' le ',' la ',' les ',' du ',' de la ',
            'intelligence é','psychologie','maladie','cyber-harcèlement',
            'chronobiologie','alzheimer','accroche','apprenez']):
        return "fr"
    if any(w in titulo_lower for w in [' die ',' der ',' das ','wenn ','wie ','emotionale',
            'psychoonk','übersetzt','mobbing','biologie der zeit']):
        return "de"
    if any(w in titulo_lower for w in ['approccio','aspetti psicologici','il morbo',
            'personale sanitario','cervello matematico']):
        return "it"
    if any(w in titulo_lower for w in ['psicologia do','a mitomania','a intelig',
            'ciberdepend','estresse','inteligência']):
        return "pt"
    if any(w in titulo_lower for w in ['stres dan','masa pandemi','perpustakaan']):
        return "id"
    if any(c in titulo for c in ['ș','ț','ă','â','î']):
        return "ro"
    return "es"


def parsear_fecha(fecha_str: str):
    """Devuelve (año, mes_num, fecha_iso, fecha_es)"""
    if not fecha_str or pd.isna(fecha_str):
        return "2017", "01", "2017-01-01", "enero 2017"
    partes = str(fecha_str).strip().split()
    mes_en = partes[0] if len(partes) > 1 else "January"
    año    = partes[-1]
    meses  = {"January":"01","February":"02","March":"03","April":"04",
               "May":"05","June":"06","July":"07","August":"08",
               "September":"09","October":"10","November":"11","December":"12"}
    mes_num = meses.get(mes_en, "01")
    mes_es  = MONTH_ES.get(mes_en, mes_en.lower())
    return año, mes_num, f"{año}-{mes_num}-01", f"{mes_es} {año}"


# ── GENERADOR PRINCIPAL ─────────────────────────────────────────────────────
def generar_libro_md(row: dict, slug: str) -> str:
    titulo  = row['Título'].strip()
    autores = row['Autores'].strip()
    fecha   = str(row['Fecha']) if not pd.isna(row['Fecha']) else ""
    disp    = str(row['Disponibilidad']) if not pd.isna(row['Disponibilidad']) else "private"

    año, mes_num, fecha_iso, fecha_es = parsear_fecha(fecha)
    idioma      = detectar_idioma(titulo)
    es_oa       = "true" if "Full-text" in disp else "false"
    lista_autores = [a.strip() for a in autores.split(";")]
    primer_autor  = lista_autores[0]
    prefijo       = LANG_PREFIX.get(idioma, "libros")

    # Permalink coherente con la estructura de directorios
    permalink = f"/{prefijo}/libros/{slug}/"

    # Citation APA — usa BASE_URL correcto
    autores_apa = "; ".join(lista_autores)
    citation    = f"{autores_apa} ({año}). *{titulo}*. ResearchGate. {BASE_URL}{permalink}"

    titulo_safe = titulo.replace('"', "'").replace("\\", "")

    md = f"""---
layout: book
title: "{titulo_safe}"
slug: "{slug}"
date: {fecha_iso}
year: "{año}"
month: "{mes_num}"
date_display: "{fecha_es}"
lang: "{idioma}"
authors:
{chr(10).join(f'  - "{a}"' for a in lista_autores)}
primary_author: "{primer_autor}"
orcid: "{ORCID}"
researchgate_url: "{RG_URL}"
is_open_access: {es_oa}
availability: "{disp}"
permalink: {permalink}
citation: '{citation}'
last_updated: "{datetime.now().strftime('%Y-%m-%d')}"
schema_type: "Book"
# ── CAPÍTULOS (añadir cuando estén listos) ──────────────────────────────────
# chapters:
#   - title: "Capítulo 1: Título"
#     slug: "capitulo-01-titulo"
#     date: 2025-01-01
#
# ── EDICIONES / ACTUALIZACIONES ANUALES ────────────────────────────────────
# editions:
#   - year: "2026"
#     date: 2026-01-01
#     changes: "Actualización de referencias y nuevo capítulo sobre IA"
---
{titulo}
"""
    return md


def main():
    BOOKS_DIR.mkdir(exist_ok=True)
    df = pd.read_csv(CSV_PATH)
    print(f"📚 Procesando {len(df)} libros...\n")

    slugs_usados = {}
    registros    = []

    for _, row in df.iterrows():
        titulo    = str(row['Título']).strip()
        slug_base = slugify(titulo)

        # Evitar slugs duplicados
        if slug_base in slugs_usados:
            slugs_usados[slug_base] += 1
            slug = f"{slug_base}-{slugs_usados[slug_base]}"
        else:
            slugs_usados[slug_base] = 1
            slug = slug_base

        contenido = generar_libro_md(row.to_dict(), slug)
        ruta      = BOOKS_DIR / f"{slug}.md"
        ruta.write_text(contenido, encoding="utf-8")

        idioma = detectar_idioma(titulo)
        registros.append({
            "slug":           slug,
            "titulo":         titulo,
            "año":            parsear_fecha(str(row['Fecha']) if not pd.isna(row['Fecha']) else "")[0],
            "idioma":         idioma,
            "disponibilidad": str(row['Disponibilidad']),
            "permalink":      f"/{LANG_PREFIX.get(idioma, 'libros')}/libros/{slug}/",
        })
        print(f"  ✅ {slug}.md  [{idioma}]")

    print(f"\n✅ {len(registros)} archivos generados en _books/")
    print("\nPróximo paso: bundle exec jekyll serve")
    return registros


if __name__ == "__main__":
    main()
