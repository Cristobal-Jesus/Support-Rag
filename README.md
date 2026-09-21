# Support RAG

Asistente de soporte empresarial que construiremos paso a paso: documentos, recuperación, respuestas con fuentes y coordinación de agentes.

**Estado actual: etapa 1 implementada — corpus, fragmentación y búsqueda léxica.**

Esta versión recupera fragmentos de seis documentos ficticios y muestra su procedencia. Usa TF-IDF para buscar por palabras. Todavía no genera respuestas con un LLM, no utiliza embeddings semánticos y no contiene agentes. La base funciona localmente, sin claves de API ni llamadas de pago.

## El problema que queremos resolver

> No me funciona la VPN del portátil de empresa. ¿Puedo conectarme desde mi ordenador personal?

La futura aplicación tendrá que combinar un manual técnico con una política interna: una solución técnicamente posible puede no estar autorizada. Todas las normas, herramientas, códigos de error y nombres de este repositorio pertenecen a **NexoDemo, una empresa ficticia**. No describen sistemas reales ni políticas de NTT DATA.

## Ejecutar la primera etapa

Requiere **Python 3.11 o superior**. Abre una terminal en la carpeta que contiene este README. El nombre del paquete de Python usa guion bajo: `support_rag`.

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m support_rag inspect
.\.venv\Scripts\python.exe -m support_rag search "E202"
.\.venv\Scripts\python.exe -m support_rag search "VPN ordenadores personales" --domain policies
```

Si `py` no existe pero tienes Python instalado, utiliza `python` en la primera línea. No hace falta activar el entorno: los comandos llaman directamente a su ejecutable.

### macOS / Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m support_rag inspect
.venv/bin/python -m support_rag search "E202"
.venv/bin/python -m support_rag search "VPN ordenadores personales" --domain policies
```

La instalación necesita Internet; una vez instalada la dependencia, estas búsquedas son locales.

## Qué deberías ver

`inspect` muestra **6 documentos y 18 fragmentos** con el corpus incluido. Al buscar `E202`, el primer resultado debe ser:

```text
[technical/errors.md#s2-c1]
Sección: Error VPN E202: segundo factor caducado
```

Después aparece el texto recuperado de esa sección. No es una respuesta inventada ni una solución generada: es evidencia que un LLM podrá utilizar más adelante. El valor `score` es similitud léxica, **no un porcentaje de confianza ni una prueba de que el texto responda a la pregunta**.

## Por dónde leer el código

| Archivo | Qué aprenderás |
| --- | --- |
| `knowledge_base/technical/` | Los manuales de VPN, errores y recuperación de acceso. |
| `knowledge_base/policies/` | Las condiciones de uso y los criterios de escalado. |
| `support_rag/documents.py` | Cómo leer documentos, dividirlos y conservar sus fuentes. |
| `support_rag/retrieval.py` | Cómo convertir texto en vectores TF-IDF y ordenarlos por similitud. |
| `support_rag/__main__.py` | Cómo conectar las piezas con una interfaz de terminal. |
| `tests/test_retrieval.py` | Cómo comprobar que la recuperación respeta fuentes y dominios. |

La explicación detallada está en [la guía de la etapa 1](docs/01_recuperacion.md). Lee primero esa guía y después el código en el orden de la tabla.

## Probarlo

Windows:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

macOS / Linux:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Las pruebas no utilizan Internet ni servicios de IA.

## Próximas etapas

El desarrollo sigue la [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html).
Las decisiones aplicadas y los comandos de comprobación están en
[Estilo y mantenimiento](docs/00_estilo.md). La preferencia también queda
registrada en `AGENTS.md` para las siguientes etapas.

| Etapa | Resultado | Estado |
| --- | --- | --- |
| 1 | Documentos, fragmentos con fuente y baseline léxico TF-IDF. | Implementada. |
| 2 | Embeddings semánticos e índice vectorial; comparar con TF-IDF. | Pendiente. |
| 3 | LLM que responde con fuentes y señala información insuficiente. | Pendiente. |
| 4 | Coordinador, especialista técnico y especialista en políticas con LangGraph. | Pendiente. |
| 5 | Interfaz Streamlit y comparación con un RAG de un solo agente. | Pendiente. |

El objetivo final es un prototipo multiagente; esta primera entrega es su base de recuperación. No se ha medido todavía ninguna mejora de un sistema multiagente.

## Límites de esta etapa

- TF-IDF compara palabras; puede fallar con sinónimos, paráfrasis o preguntas en otro idioma.
- La ausencia de coincidencias no demuestra que la respuesta no exista. Una coincidencia tampoco garantiza relevancia.
- El filtro de dominio separa las búsquedas de los futuros especialistas. No es un sistema de permisos de usuarios.
- Los fragmentos se delimitan por secciones y ventanas de palabras. Un corte puede separar una condición de su excepción; siempre hay que inspeccionar el texto recuperado.
- El índice se reconstruye en memoria en cada ejecución. Es suficiente para este corpus pequeño.
- El programa no modifica equipos, concede accesos ni crea tickets.

## Referencia

La implementación utiliza [TfidfVectorizer de scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html). La versión fijada en `requirements.txt` es la utilizada para comprobar el código; no se presenta como la más reciente.
