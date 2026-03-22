"""
Generador de capítulos — Juan Moisés de la Serna
Lee el CSV de capítulos de ResearchGate y genera 508 archivos Markdown
como páginas independientes citables, con espacio para asignar libro después.

Uso:
    python generar_capitulos.py
"""

import pandas as pd
import re
import unicodedata
from pathlib import Path
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
CSV_PATH      = "capitulos_researchgate_juan_moises_de_la_serna.csv"
CHAPTERS_DIR  = Path("_chapters")
BASE_URL      = "https://juanmoises-de-la-serna.github.io"
AUTHOR        = "Juan Moisés de la Serna"
ORCID         = "https://orcid.org/0000-0002-8401-8018"
RG_URL        = "https://www.researchgate.net/profile/Juan-Moises-De-La-Serna"

MONTH_MAP = {
    "January":"01","February":"02","March":"03","April":"04",
    "May":"05","June":"06","July":"07","August":"08",
    "September":"09","October":"10","November":"11","December":"12"
}
MONTH_ES = {
    "January":"enero","February":"febrero","March":"marzo","April":"abril",
    "May":"mayo","June":"junio","July":"julio","August":"agosto",
    "September":"septiembre","October":"octubre","November":"noviembre","December":"diciembre"
}

# ── UTILIDADES ────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = str(text)
    # Normalizar unicode → ASCII donde sea posible
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text.strip())
    text = re.sub(r'-+', '-', text)
    return text[:70].rstrip('-')


def detectar_idioma(titulo: str) -> str:
    t = str(titulo).lower()
    # Árabe
    if any('\u0600' <= c <= '\u06ff' for c in titulo):
        return "ar"
    # Alemán
    if any(w in t for w in ['die ','der ','das ','wenn ','beziehung','behandlung',
                             'jetzt','emotionale','mobbing','cyber','psycho']):
        return "de"
    # Francés
    if any(w in t for w in ['le ','la ','les ','du ','de la ','vers ','prév',
                             "l'","d'","qu'",'chez ','dans ','avec ']):
        return "fr"
    # Italiano
    if any(w in t for w in [' di ',' il ',' lo ',' la ',' le ',' un ',' una ',
                             'dello','della','degli','alle ','nella']):
        return "it"
    # Portugués
    if any(w in t for w in ['ção','ções','ão ','ões ','quando','também',
                             'psicologia do','da ','uma ']):
        return "pt"
    # Indonesio
    if any(w in t for w in ['masa pandemi','stres dan']):
        return "id"
    # Rumano
    if any(c in titulo for c in ['ș','ț','ă','â','î']):
        return "ro"
    # Inglés
    if any(w in t for w in ['the ','and ','of ','in ','for ','with ','symptoms',
                             'approach','chapter','overview','during','between']):
        return "en"
    return "es"


def parsear_fecha(fecha_str):
    if not fecha_str or pd.isna(fecha_str):
        return "2017", "01", "2017-01-01", "enero 2017"
    partes = str(fecha_str).strip().split()
    mes_en = partes[0] if len(partes) > 1 else "January"
    año    = partes[-1]
    mes_num = MONTH_MAP.get(mes_en, "01")
    mes_es  = MONTH_ES.get(mes_en, mes_en.lower())
    return año, mes_num, f"{año}-{mes_num}-01", f"{mes_es} {año}"


# ── GENERADOR ─────────────────────────────────────────────────────────────────

def generar_chapter_md(row: dict, slug: str, numero: int) -> str:
    titulo  = str(row['Título']).strip()
    autores = str(row['Autores']).strip()
    fecha   = row.get('Fecha', '')
    disp    = str(row.get('Disponibilidad', '')) if not pd.isna(row.get('Disponibilidad','')) else 'private'

    año, mes_num, fecha_iso, fecha_es = parsear_fecha(fecha)
    idioma   = detectar_idioma(titulo)
    es_oa    = "true" if "Full-text" in disp else "false"
    lista_autores = [a.strip() for a in autores.split(";")]

    # Cita APA del capítulo (sin libro asignado aún)
    autores_apa = "; ".join(lista_autores)
    citation = (f'{autores_apa} ({año}). {titulo}. '
                f'[Capítulo en libro por asignar]. {BASE_URL}/capitulos/{slug}/')

    md = f"""---
layout: chapter
title: "{titulo.replace('"', "'")}"
slug: "{slug}"
date: {fecha_iso}
year: "{año}"
month: "{mes_num}"
date_display: "{fecha_es}"
lang: "{idioma}"
authors:
{chr(10).join(f'  - "{a}"' for a in lista_autores)}
is_open_access: {es_oa}
availability: "{disp}"
permalink: /capitulos/{slug}/
citation: '{citation.replace("'", " ")}'
last_updated: "{datetime.now().strftime('%Y-%m-%d')}"
schema_type: "Chapter"
rg_number: {numero}

# ── ASIGNAR AL LIBRO ─────────────────────────────────────────────────────────
# Cuando sepas a qué libro pertenece, descomenta y rellena estas líneas:
# book_slug: "slug-del-libro"
# book_title: "Título completo del libro"
# chapter_number: 1
#
# ── ACTUALIZACIONES ANUALES ──────────────────────────────────────────────────
# versions:
#   - year: "2026"
#     changes: "Descripción de los cambios añadidos"
---
"""
    return md


def main():
    CHAPTERS_DIR.mkdir(exist_ok=True)

    df = pd.read_csv(CSV_PATH)
    print(f"📖 Procesando {len(df)} capítulos...\n")

    slugs_usados = {}
    generados    = 0
    errores      = []

    for _, row in df.iterrows():
        titulo = str(row['Título']).strip()
        numero = int(row['Nº'])

        try:
            slug_base = slugify(titulo)
            if not slug_base or slug_base == '-':
                slug_base = f"capitulo-{numero}"

            # Evitar slugs duplicados añadiendo sufijo numérico
            if slug_base in slugs_usados:
                slugs_usados[slug_base] += 1
                slug = f"{slug_base}-{slugs_usados[slug_base]}"
            else:
                slugs_usados[slug_base] = 1
                slug = slug_base

            contenido = generar_chapter_md(row.to_dict(), slug, numero)
            ruta = CHAPTERS_DIR / f"{slug}.md"
            ruta.write_text(contenido, encoding="utf-8")
            generados += 1

            if generados % 50 == 0:
                print(f"  → {generados}/{len(df)} capítulos generados...")

        except Exception as e:
            errores.append((numero, titulo[:60], str(e)))

    print(f"\n✅ {generados} capítulos generados en _chapters/")

    if errores:
        print(f"\n⚠️  {len(errores)} errores:")
        for n, t, e in errores:
            print(f"   #{n} {t}: {e}")

    # Generar índice CSV de slugs para facilitar el mapeo libro→capítulo
    registros = []
    for f in sorted(CHAPTERS_DIR.glob("*.md")):
        contenido = f.read_text(encoding="utf-8")
        # Extraer campos del YAML
        titulo_match = re.search(r'^title: "(.+)"', contenido, re.M)
        año_match    = re.search(r'^year: "(.+)"', contenido, re.M)
        lang_match   = re.search(r'^lang: "(.+)"', contenido, re.M)
        rg_match     = re.search(r'^rg_number: (\d+)', contenido, re.M)
        registros.append({
            "rg_numero":     rg_match.group(1) if rg_match else "",
            "slug":          f.stem,
            "titulo":        titulo_match.group(1) if titulo_match else "",
            "año":           año_match.group(1) if año_match else "",
            "idioma":        lang_match.group(1) if lang_match else "",
            "book_slug":     "",   # ← rellenar para asignar libro
            "book_title":    "",   # ← rellenar para asignar libro
            "chapter_number":"",   # ← orden dentro del libro
        })

    pd.DataFrame(registros).to_csv("mapeo_capitulos_libros.csv",
                                    index=False, encoding="utf-8")
    print(f"\n📊 Índice de mapeo generado: mapeo_capitulos_libros.csv")
    print("   → Rellena las columnas book_slug, book_title y chapter_number")
    print("   → Luego ejecuta: python aplicar_mapeo.py")
    print(f"\n{'─'*55}")
    print(f"  Total capítulos: {generados}")
    print(f"  Carpeta:         _chapters/")
    print(f"  Índice mapeo:    mapeo_capitulos_libros.csv")


if __name__ == "__main__":
    main()
