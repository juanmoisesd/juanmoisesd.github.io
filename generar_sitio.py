"""
Generador del sitio Jekyll para libros de Juan Moisés de la Serna
Lee el CSV de ResearchGate y genera todos los archivos Markdown
con estructura lista para escalar: libros → capítulos → ediciones anuales

Uso:
    python generar_sitio.py
"""

import pandas as pd
import re
import os
from pathlib import Path
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
CSV_PATH   = "libros_researchgate_juan_moises_de_la_serna.csv"
BOOKS_DIR  = Path("_books")
BASE_URL   = "https://juanmoises-de-la-serna.github.io"
AUTHOR     = "Juan Moisés de la Serna"
ORCID      = "https://orcid.org/0000-0002-8401-8018"
RG_URL     = "https://www.researchgate.net/profile/Juan-Moises-De-La-Serna"
GS_URL     = "https://scholar.google.com/citations?user=TU_ID_AQUI"

MONTH_ES = {
    "January":"enero","February":"febrero","March":"marzo","April":"abril",
    "May":"mayo","June":"junio","July":"julio","August":"agosto",
    "September":"septiembre","October":"octubre","November":"noviembre","December":"diciembre"
}

# ── UTILIDADES ────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower()
    for a, b in [('á','a'),('é','e'),('í','i'),('ó','o'),('ú','u'),
                 ('ä','a'),('ë','e'),('ï','i'),('ö','o'),('ü','u'),
                 ('â','a'),('ê','e'),('î','i'),('ô','o'),('û','u'),
                 ('à','a'),('è','e'),('ì','i'),('ò','o'),('ù','u'),
                 ('ñ','n'),('ç','c'),('ș','s'),('ț','t'),('ă','a'),
                 ('ș','s'),('ğ','g'),('ş','s'),('ı','i'),
                 ("'",""),("«",""),("»",""),("‫",""),("‬","")]:
        text = text.replace(a, b)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text.strip())
    text = re.sub(r'-+', '-', text)
    return text[:70].rstrip('-')


def detectar_idioma(titulo: str) -> str:
    titulo_lower = titulo.lower()
    if any(w in titulo_lower for w in ['the','stress','psychology','emotional','abuse',
                                        'depression','happiness','alexithymia','chronobiology',
                                        'cyberbullying','psycho','trends','new ']):
        return "en"
    if any(w in titulo_lower for w in ['le','la ','les','du','de la','intelligence',
                                        'psychologie','maladie','cyber-harcèlement',
                                        'chronobiologie','alzheimer','accroche']):
        return "fr"
    if any(w in titulo_lower for w in ['die','der','das','wenn','wie','jetzt','emotionale',
                                        'psychoonk','übersetzt','mobbing']):
        return "de"
    if any(w in titulo_lower for w in ['sti','nei','di pandemia','il morbo','approccio',
                                        'aspetti','personale sanitario','cervello']):
        return "it"
    if any(w in titulo_lower for w in ['psicologia do','a mitomania','a intelig',
                                        'ciberdepend','depressão','estresse','inteligência']):
        return "pt"
    if any(w in titulo_lower for w in ['stres','masa pandemi']):
        return "id"
    if any(c in titulo for c in ['ș','ț','ă','â','î','ê']):
        return "ro"
    if any(c in titulo for c in ['ا','ل','م','ن','ع','ر','ذ']):
        return "ar"
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


# ── GENERADOR PRINCIPAL ───────────────────────────────────────────────────────

def generar_libro_md(row: dict, slug: str) -> str:
    titulo   = row['Título'].strip()
    autores  = row['Autores'].strip()
    fecha    = str(row['Fecha']) if not pd.isna(row['Fecha']) else ""
    disp     = str(row['Disponibilidad']) if not pd.isna(row['Disponibilidad']) else "private"
    año, mes_num, fecha_iso, fecha_es = parsear_fecha(fecha)
    idioma   = detectar_idioma(titulo)
    es_oa    = "true" if "Full-text" in disp else "false"
    lista_autores = [a.strip() for a in autores.split(";")]
    primer_autor  = lista_autores[0]

    # Citation recomendada APA
    autores_apa = "; ".join(lista_autores)
    citation = f'{autores_apa} ({año}). *{titulo}*. ResearchGate. {BASE_URL}/libros/{slug}/'

    md = f"""---
layout: book
title: "{titulo.replace('"', "'")}"
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
permalink: /libros/{slug}/
citation: '{citation}'
last_updated: "{datetime.now().strftime('%Y-%m-%d')}"
schema_type: "Book"

# ── CAPÍTULOS (añadir cuando estén listos) ───────────────────────────────────
# chapters:
#   - title: "Capítulo 1: Título"
#     slug: "capitulo-01-titulo"
#     date: 2025-01-01
#
# ── EDICIONES / ACTUALIZACIONES ANUALES ──────────────────────────────────────
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
        titulo = str(row['Título']).strip()
        slug_base = slugify(titulo)

        # Evitar slugs duplicados
        if slug_base in slugs_usados:
            slugs_usados[slug_base] += 1
            slug = f"{slug_base}-{slugs_usados[slug_base]}"
        else:
            slugs_usados[slug_base] = 1
            slug = slug_base

        # Generar archivo Markdown del libro
        contenido = generar_libro_md(row.to_dict(), slug)
        ruta = BOOKS_DIR / f"{slug}.md"
        ruta.write_text(contenido, encoding="utf-8")

        año, mes_num, fecha_iso, fecha_es = parsear_fecha(
            str(row['Fecha']) if not pd.isna(row['Fecha']) else "")
        registros.append({
            "slug": slug,
            "titulo": titulo,
            "año": año,
            "idioma": detectar_idioma(titulo),
            "disponibilidad": str(row['Disponibilidad']),
            "permalink": f"/libros/{slug}/"
        })
        print(f"  ✅ {slug}.md")

    print(f"\n✅ {len(registros)} archivos generados en _books/")
    print("\nPróximo paso: ejecutar 'bundle exec jekyll serve' para previsualizar")
    return registros


if __name__ == "__main__":
    main()
