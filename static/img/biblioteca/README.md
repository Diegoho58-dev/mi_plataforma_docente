# Biblioteca visual educativa

Esta carpeta contiene ilustraciones locales para las guías autodidactas.

## Estructura

- `biologia/`: célula, termorregulación, osmorregulación, sistema urinario y plantas.
- `ciencias_naturales/`: ecosistemas y ciclos naturales.
- `matematicas/`: fracciones, ecuaciones y geometría.
- `contexto_cotidiano/`: dinero y actividades prácticas.
- `catalogo_imagenes.json`: metadatos pedagógicos de cada imagen.

## Cómo agregar una imagen

1. Guarda el PNG, JPG o WEBP en la carpeta correspondiente.
2. Usa un nombre estable y descriptivo, por ejemplo `biologia_neurona_001.png`.
3. Registra en `catalogo_imagenes.json`:
   - `id` único.
   - `archivo` relativo a `static/img/`.
   - `materias`.
   - `temas` y palabras clave.
   - `clei`.
   - `tipo`.
   - `descripcion`.
   - `uso`.
4. No uses imágenes genéricas para reemplazar un tema específico. Si no existe una imagen pertinente, se debe registrar como pendiente y no inventar un diagrama abstracto.

## Siguiente fase

La aplicación leerá este catálogo, normalizará el tema de Planeación y buscará coincidencias por materia, CLEI, tema y palabras clave. Gemini podrá ayudar a ordenar las coincidencias, pero nunca será responsable de servir o generar la imagen en tiempo de petición.
