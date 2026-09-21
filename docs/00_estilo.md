# Estilo y mantenimiento

Seguimos la [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html):
cuatro espacios, líneas de hasta 80 caracteres, imports por módulos con rutas
absolutas y docstrings con secciones como `Args`, `Returns` y `Attributes`.
Las excepciones relevantes de lectura documental se describen con `Raises`.

Los nombres del código están en inglés; las explicaciones y los comentarios,
en español para facilitar el aprendizaje. No añadimos una explicación que solo
repita el nombre de cada prueba.

## Qué significa en este proyecto

`documents.Chunk` representa un fragmento y sus metadatos. Es una dataclass
inmutable: al crearla indicamos sus campos y después no se modifican.
Su docstring documenta lo que significa cada campo con `Attributes`.

`documents.load_chunks()` recorre las carpetas y llama a `_load_document()`
para cada archivo. El prefijo `_` señala una función interna del módulo;
el resto del programa utiliza la interfaz pública `load_chunks()`.

`retrieval.TfidfRetriever` conserva su índice en atributos internos:
`_chunks`, `_vectorizer` y `_matrix`. El resto del programa consulta ese índice
mediante `search()`, sin modificar directamente su representación.

El único aviso de Pylint suprimido en el código de producción es
`too-few-public-methods`, con una explicación junto a la clase: un recuperador
tiene una única operación pública, buscar. Añadir métodos artificiales solo
para satisfacer ese aviso haría el diseño más complicado.

## Comprobar el estilo

Las herramientas de desarrollo están separadas de la dependencia necesaria
para ejecutar la aplicación. Desde la raíz del repositorio, en Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m black --check support_rag tests
.\.venv\Scripts\python.exe -m pylint support_rag tests
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

En macOS o Linux sustituye el ejecutable por `.venv/bin/python`.

Black comprueba el formato y Pylint busca errores y problemas de estilo.
`pyproject.toml` configura ambas herramientas para este proyecto; es una
configuración local, no una copia completa del archivo de Google.
Estas comprobaciones complementan la revisión manual de imports, claridad y
docstrings: no certifican por sí solas toda la guía.

Para aplicar el formato automáticamente, ejecuta Black sin `--check`.
Después vuelve a ejecutar las comprobaciones y las pruebas.

## Orden recomendado para entender el programa

1. Lee una sección de `knowledge_base/technical/errors.md`.
2. Revisa `Chunk` y `split_words()` en `support_rag/documents.py`.
3. Sigue `load_chunks()` y su llamada a `_load_document()`.
4. Revisa `TfidfRetriever.__init__()` y `search()` en `retrieval.py`.
5. Sigue el comando `search` desde `main()` en `__main__.py`.

La explicación del algoritmo y los ejercicios están en
[la guía de recuperación](01_recuperacion.md).
