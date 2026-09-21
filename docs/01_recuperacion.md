# Etapa 1: entender cómo recuperamos los documentos

## 1. Antes de programar: qué problema estamos resolviendo

Un LLM no conoce automáticamente los manuales privados de una empresa. RAG significa *Retrieval-Augmented Generation*: recuperar información y proporcionársela al modelo para que genere una respuesta basada en ella.

En esta etapa implementamos la **recuperación**, empezando por una técnica léxica sencilla. En una etapa posterior conectaremos la generación y compararemos la búsqueda léxica con embeddings semánticos. Tener una referencia sencilla nos permitirá medir qué mejora realmente.

El caso de ejemplo combina dos preguntas diferentes: «¿cómo arreglo la VPN?» y «¿qué equipos están autorizados?». Por eso los documentos están separados en `technical` y `policies`. Más adelante, cada especialista tendrá su propia herramienta de búsqueda.

## 2. Leer los documentos

Abre `knowledge_base/technical/errors.md`. Es un archivo Markdown normal. Un encabezado `#` identifica el documento y cada encabezado `##` identifica una sección.

Después abre `support_rag/documents.py`. `load_chunks()` recorre los Markdown de ambos dominios y lee su texto con UTF-8. Todo el contenido del corpus debe estar bajo un encabezado `##`; el lector avisa si encuentra texto fuera de esas secciones para evitar pérdidas silenciosas.

No hay scraping ni PDFs en esta primera etapa. Trabajamos con una fuente controlada y fácil de inspeccionar.

## 3. Dividir sin perder la procedencia

Un *chunk* es un fragmento recuperable. El objeto `Chunk` guarda:

| Campo | Ejemplo | Para qué sirve |
| --- | --- | --- |
| `id` | `technical/errors.md#s2-c1` | Identifica la segunda sección y su primer fragmento dentro del archivo. |
| `source` | `technical/errors.md` | Permite localizar el documento de origen. |
| `domain` | `technical` | Permite filtrar el material de un especialista. |
| `section` | `Error VPN E202: segundo factor caducado` | Conserva el contexto del apartado. |
| `text` | La explicación del error. | Es la evidencia que recuperamos. |

Primero separamos por `##`. Si una sección supera las 120 palabras, `split_words()` crea ventanas de 120 palabras con 20 palabras repetidas entre ventanas consecutivas. Ese solapamiento reduce la pérdida de contexto en los cortes, aunque no garantiza que todas las condiciones permanezcan juntas. Las ventanas nunca cruzan de una sección a otra.

Los números son un punto de partida didáctico, no valores universales. Se cuentan **palabras**, no tokens del modelo. En los documentos actuales todas las secciones caben en una ventana; las pruebas incluyen una sección larga para comprobar el solapamiento.

Los identificadores son deterministas mientras no cambie el documento. Si insertas secciones o cambias la fragmentación, algunos identificadores pueden cambiar: no son referencias permanentes entre versiones.

Ejecuta `python -m support_rag inspect` utilizando el Python de tu entorno. Debes poder relacionar cada identificador de la salida con una sección del Markdown original.

## 4. Convertir el texto en números

Abre `support_rag/retrieval.py`. `TfidfRetriever.__init__()` recibe los fragmentos y construye un índice en memoria.

TF-IDF asigna pesos a palabras y parejas de palabras. Una palabra frecuente en un fragmento y poco común en el resto del corpus puede resultar más informativa para distinguirlo. El código normaliza mayúsculas y tildes y elimina una lista pequeña de palabras muy comunes.

```python
self._matrix = self._vectorizer.fit_transform(texts)
```

`fit_transform()` aprende el vocabulario a partir de los fragmentos y produce una matriz: una fila por fragmento y una columna por término. Son vectores numéricos léxicos; no son embeddings semánticos producidos por una red neuronal.

Cuando llega una pregunta, usamos el mismo vocabulario:

```python
query = self._vectorizer.transform([question])
```

Aquí usamos `transform()`, no `fit_transform()`. Si volviéramos a aprender un vocabulario distinto con cada pregunta, las columnas dejarían de representar los mismos términos y no podríamos comparar los vectores correctamente.

## 5. Buscar y conservar las fuentes

La matriz y la pregunta están normalizadas. Su producto escalar equivale a la similitud del coseno:

```python
scores = (self._matrix @ query.T).toarray().ravel()
```

El método `search()` filtra el dominio solicitado, descarta puntuaciones cero y devuelve como máximo `top_k` resultados ordenados por puntuación. `SearchResult` contiene el fragmento completo con su procedencia, además del score.

Prueba estas búsquedas utilizando el Python de tu entorno:

```bash
python -m support_rag search "E202"
python -m support_rag search "VPN ordenadores personales" --domain policies
python -m support_rag search "ornitorrinco astrofotografia"
```

En la primera debes encontrar el error del segundo factor. En la segunda solo deben aparecer políticas, incluida la restricción de VPN en ordenadores personales. En la tercera no debe devolver fragmentos arbitrarios con puntuación cero.

Prueba también a cambiar «ordenadores personales» por «ordenador personal». Con el corpus incluido, la consulta singular prioriza el apartado del escritorio virtual y deja la prohibición principal fuera de los tres primeros resultados. Esta versión no agrupa singular y plural. Es una limitación observada del baseline, y un caso útil para evaluar si la búsqueda semántica mejora la recuperación.

Ahora prueba `python -m support_rag search "Mi VPN falla justo antes de una reunión"`. Puede recuperar textos con palabras compartidas, pero eso no demuestra que resuelvan toda la pregunta. **El score no es la probabilidad de que la respuesta sea correcta.**

## 6. La responsabilidad de cada archivo

`documents.py` se encarga de leer y fragmentar. `retrieval.py` se encarga de buscar. `__main__.py` lee los argumentos de la terminal y muestra el resultado. Esa separación nos permite cambiar TF-IDF por embeddings sin reescribir el lector de documentos.

Cuando añadamos el LLM, recibirá la pregunta junto con los fragmentos recuperados y sus identificadores. Tendremos que comprobar que sus afirmaciones están respaldadas por esos fragmentos. Una cita existente puede estar mal utilizada; verificar solo que existe un ID no será suficiente.

## 7. Ejercicio para entenderlo

1. Busca `E202` y localiza el párrafo exacto del resultado en el archivo original.
2. Ejecuta la consulta de ordenadores personales con `--domain technical` y luego con `--domain policies`. Compara qué información recupera cada uno.
3. Añade una sección `## Error E404 de demostración` a `technical/errors.md`, escribe una explicación ficticia y busca `E404`. El índice se reconstruye automáticamente en cada ejecución.
4. Cambia las palabras de una pregunta sin cambiar su significado. Observa cuándo falla la coincidencia léxica: ahí tendrás un motivo concreto para probar embeddings.

## 8. Lo que debes poder explicar en la entrevista

- Qué diferencia hay entre recuperar información y generar una respuesta.
- Por qué guardamos documento y sección junto a cada fragmento.
- Qué representa TF-IDF y por qué un score alto no equivale a certeza.
- Por qué los especialistas consultarán dominios diferentes.
- Cómo sabremos si la búsqueda semántica mejora esta base.

La siguiente etapa será añadir embeddings y medir la recuperación con el mismo corpus y las mismas preguntas. El LLM y los agentes llegarán después de que esta base esté clara.
