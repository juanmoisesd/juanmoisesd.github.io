# Sitio académico — Juan Moisés de la Serna

Catálogo de libros con arquitectura escalable:
**Libros → Capítulos → Ediciones anuales**

---

## Estructura del repositorio

```
juanmoises-de-la-serna.github.io/
│
├── _books/                        ← Un .md por libro (generado automáticamente)
│   ├── ciberpsicologia-mente-internet.md
│   ├── estres-trauma-pandemia.md
│   └── ... (76 libros)
│
├── _chapters/                     ← Un .md por capítulo (añadir manualmente)
│   ├── ciberpsicologia-mente-internet-cap01.md
│   └── ...
│
├── _layouts/
│   ├── default.html               ← Layout base
│   ├── book.html                  ← Página de libro (con schema.org Book)
│   └── chapter.html              ← Página de capítulo (con schema.org Chapter)
│
├── assets/css/main.css            ← Estilos
├── libros/index.html              ← Catálogo con filtros y búsqueda
├── index.html                     ← Portada
├── _config.yml                    ← Configuración central
├── Gemfile                        ← Dependencias Ruby/Jekyll
└── generar_sitio.py               ← Script para añadir nuevos libros
```

---

## Publicar en GitHub Pages

### Primera vez

1. Crear cuenta en GitHub (si no tienes)
2. Crear repositorio llamado exactamente: `juanmoises-de-la-serna.github.io`
3. Subir todos los archivos de esta carpeta al repositorio
4. En GitHub → Settings → Pages → Source: `main` branch → `/root`
5. Tu sitio estará en: `https://juanmoises-de-la-serna.github.io`

### Actualizar contenido (sin terminal)

Desde GitHub.com, navega al archivo que quieras editar y pulsa el lápiz ✏️.

---

## Añadir un nuevo libro

1. Ejecuta el script con el CSV actualizado:
   ```bash
   python generar_sitio.py
   ```
   Genera automáticamente el archivo `.md` en `_books/`

2. O crea el archivo manualmente en `_books/`:
   ```markdown
   ---
   layout: book
   title: "Título del Nuevo Libro"
   slug: "titulo-del-nuevo-libro"
   date: 2026-01-01
   year: "2026"
   month: "01"
   date_display: "enero 2026"
   lang: "es"
   authors:
     - "Juan Moisés de la Serna"
   is_open_access: true
   availability: "Full-text available"
   permalink: /libros/titulo-del-nuevo-libro/
   citation: 'De la Serna, J. M. (2026). *Título*. URL'
   last_updated: "2026-01-01"
   schema_type: "Book"
   ---
   ```

---

## Añadir capítulos a un libro

Crea un archivo en `_chapters/` con este formato:

```markdown
---
layout: chapter
title: "Capítulo 1: Introducción a la Ciberpsicología"
slug: "capitulo-01-introduccion"
book_slug: "ciberpsicologia-relacion-entre-mente-e-internet"
book_title: "CiberPsicología: Relación entre Mente e Internet"
date: 2025-01-01
last_updated: "2025-01-01"
lang: "es"
permalink: /libros/ciberpsicologia-relacion-entre-mente-e-internet/capitulo-01-introduccion/

# Historial de actualizaciones del capítulo
versions:
  - year: "2025"
    changes: "Versión inicial"
---

Aquí va el contenido del capítulo en Markdown.

## Primera sección

Texto...
```

Luego añade el capítulo al libro en `_books/ciberpsicologia-relacion-entre-mente-e-internet.md`:

```yaml
chapters:
  - title: "Capítulo 1: Introducción a la Ciberpsicología"
    slug: "capitulo-01-introduccion"
    date: 2025-01-01
```

---

## Actualizar un capítulo cada año

En el archivo `.md` del capítulo, actualiza el campo `last_updated` y añade una entrada en `versions`:

```yaml
last_updated: "2026-03-01"
versions:
  - year: "2026"
    changes: "Añadida sección sobre IA generativa y salud mental"
  - year: "2025"
    changes: "Versión inicial"
```

La URL del capítulo **no cambia**. La actualización es visible en la página.

---

## Previsualizar en local (opcional)

```bash
gem install bundler
bundle install
bundle exec jekyll serve
# Abre http://localhost:4000
```

---

## Escalar a 130+ libros

Cuando tengas el CSV completo de todos tus libros:
```bash
# Edita CSV_PATH en generar_sitio.py
python generar_sitio.py
```
El script evita duplicados de slug y es idempotente (puedes ejecutarlo varias veces).
