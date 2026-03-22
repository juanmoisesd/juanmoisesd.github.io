"""
aplicar_mapeo.py — Juan Moisés de la Serna

Lee mapeo_capitulos_libros.csv (con book_slug y book_title rellenados)
y actualiza cada archivo .md en _chapters/ añadiendo la asignación al libro.

También actualiza los _books/ correspondientes añadiendo la lista de capítulos.

Uso:
    1. Rellena mapeo_capitulos_libros.csv (columnas book_slug, book_title, chapter_number)
    2. python aplicar_mapeo.py
    3. Sube los cambios a GitHub
"""

import pandas as pd
import re
from pathlib import Path

CHAPTERS_DIR = Path("_chapters")
BOOKS_DIR    = Path("_books")
MAPEO_CSV    = "mapeo_capitulos_libros.csv"


def actualizar_chapter(slug: str, book_slug: str, book_title: str, chapter_number: str):
    """Descomenta y rellena book_slug, book_title y chapter_number en el .md."""
    ruta = CHAPTERS_DIR / f"{slug}.md"
    if not ruta.exists():
        print(f"  ⚠️  No encontrado: {slug}.md")
        return

    contenido = ruta.read_text(encoding="utf-8")

    # Reemplazar líneas comentadas con valores reales
    contenido = re.sub(
        r'# book_slug: "slug-del-libro"',
        f'book_slug: "{book_slug}"',
        contenido
    )
    contenido = re.sub(
        r'# book_title: "Título completo del libro"',
        f'book_title: "{book_title.replace(chr(34), chr(39))}"',
        contenido
    )
    if chapter_number:
        contenido = re.sub(
            r'# chapter_number: 1',
            f'chapter_number: {chapter_number}',
            contenido
        )

    # Actualizar también la cita APA con el libro
    contenido = re.sub(
        r"citation: '(.+?)\[Capítulo en libro por asignar\](.+?)'",
        f"citation: '\\1En {book_title.replace(chr(39),' ')}\\2'",
        contenido
    )

    ruta.write_text(contenido, encoding="utf-8")


def actualizar_book_chapters(book_slug: str, capitulos: list):
    """
    Añade o actualiza la sección 'chapters:' en el .md del libro.
    capitulos: lista de dicts {title, slug, date, chapter_number}
    """
    ruta = BOOKS_DIR / f"{book_slug}.md"
    if not ruta.exists():
        print(f"  ⚠️  Libro no encontrado: {book_slug}.md")
        return

    contenido = ruta.read_text(encoding="utf-8")

    # Ordenar por chapter_number si existe
    capitulos_sorted = sorted(
        capitulos,
        key=lambda x: int(x.get('chapter_number') or 999)
    )

    # Construir bloque YAML de capítulos
    lineas = ["chapters:"]
    for ch in capitulos_sorted:
        lineas.append(f"  - title: \"{ch['title'].replace(chr(34), chr(39))}\"")
        lineas.append(f"    slug: \"{ch['slug']}\"")
        if ch.get('date'):
            lineas.append(f"    date: {ch['date']}")
        if ch.get('chapter_number'):
            lineas.append(f"    chapter_number: {ch['chapter_number']}")
    bloque = "\n".join(lineas)

    # Si ya hay sección chapters, reemplazar; si no, añadir antes del cierre ---
    if re.search(r'^chapters:', contenido, re.M):
        contenido = re.sub(
            r'^chapters:.*?(?=\n\w|\n#|\Z)',
            bloque,
            contenido,
            flags=re.M | re.DOTALL
        )
    else:
        # Insertar justo antes del cierre del YAML (---)
        contenido = re.sub(
            r'^(# ── CAPÍTULOS.*?# ── EDICIONES)',
            bloque + "\n\n# ── EDICIONES",
            contenido,
            flags=re.M | re.DOTALL
        )

    ruta.write_text(contenido, encoding="utf-8")
    print(f"  📚 Libro actualizado: {book_slug} ({len(capitulos)} capítulos)")


def main():
    print("=" * 55)
    print("  APLICAR MAPEO CAPÍTULO → LIBRO")
    print("=" * 55)

    df = pd.read_csv(MAPEO_CSV)

    # Solo procesar filas con book_slug rellenado
    df_asignados = df[df['book_slug'].notna() & (df['book_slug'] != '')]
    print(f"\n📊 Filas con libro asignado: {len(df_asignados)} / {len(df)}")

    if len(df_asignados) == 0:
        print("\n⚠️  No hay filas con book_slug rellenado en el CSV.")
        print("   Rellena las columnas book_slug, book_title y chapter_number")
        print("   y vuelve a ejecutar este script.")
        return

    # Actualizar capítulos individuales
    print("\n📖 Actualizando archivos de capítulos...")
    for _, row in df_asignados.iterrows():
        actualizar_chapter(
            slug=str(row['slug']),
            book_slug=str(row['book_slug']),
            book_title=str(row['book_title']),
            chapter_number=str(row.get('chapter_number', '')) if pd.notna(row.get('chapter_number')) else ''
        )

    # Actualizar libros con lista de capítulos
    print("\n📚 Actualizando libros con sus capítulos...")
    for book_slug, grupo in df_asignados.groupby('book_slug'):
        capitulos = []
        for _, row in grupo.iterrows():
            # Leer title y date del .md del capítulo
            ruta_ch = CHAPTERS_DIR / f"{row['slug']}.md"
            title = str(row['titulo'])
            date  = ""
            if ruta_ch.exists():
                ch_content = ruta_ch.read_text(encoding="utf-8")
                date_m = re.search(r'^date: (\S+)', ch_content, re.M)
                if date_m:
                    date = date_m.group(1)
            capitulos.append({
                'title':          title,
                'slug':           str(row['slug']),
                'date':           date,
                'chapter_number': str(row.get('chapter_number','')) if pd.notna(row.get('chapter_number')) else ''
            })
        actualizar_book_chapters(str(book_slug), capitulos)

    print(f"\n✅ Mapeo aplicado correctamente")
    print("   Sube los cambios a GitHub para publicar.")


if __name__ == "__main__":
    main()
