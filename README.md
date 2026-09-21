# Support-Rag | Sistema Multi-Agente y RAG Local con LangGraph

Sistema de soporte tecnico inteligente basado en una arquitectura multi-agente totalmente local, gratuita y respetuosa con la privacidad. Utiliza LangGraph para la orquestacion mediante grafos de estado, Pydantic para la validacion estricta de rutas y ChromaDB junto a Tools para la resolucion de consultas tecnicas.

---

## Arquitectura del Sistema

El flujo de trabajo está diseñado como un **Grafo de Estado Dirigido (`StateGraph`)**:

```text
                  ┌──────────────────────┐
                  │   [START] Entrada    │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   Nodo Orquestador   │
                  │ (Pydantic Routing)   │
                  └──────────┬───────────┘
                             │
                 ┌───────────┴───────────┐
                 │  Arista Condicional   │
                 └─────┬───────────┬─────┘
  agente_general       │           │      agente_rag
┌──────────────────────┘           └──────────────────────┐
│                                                         │
▼                                                         ▼
┌──────────────────────┐               ┌──────────────────────────┐
│ Nodo Agente General  │               │     Nodo Agente RAG      │
└──────────┬───────────┘               │ (ChromaDB + Tool Calling)│
           │                           └────────────┬─────────────┘
           │                                        │
           │                             ┌──────────┴───────────┐
           │                             │ ¿Invoca Tool o Fin?  │
           │                             └─────┬───────────┬────┘
           │                            tools  │           │  __end__
           │                           ┌───────┘           │
           │                           ▼                   │
           │               ┌───────────────────────┐       │
           │               │  Nodo ToolNode        │       │
           │               │  (Mock Tools)         │       │
           │               └───────────┬───────────┘       │
           │                           │ (retorno)         │
           │                           └───────────────────┤
           │                                               │
           ▼                                               ▼
┌──────────────────────────────────────────────────────────┐
│                        [END] Fin                         │
└──────────────────────────────────────────────────────────┘
```text

1. Orquestador (Router): Evalua la consulta del usuario usando salidas estructuradas (Pydantic) para determinar el nodo de destino de forma determinista.
2. Agente General: Responde a saludos, despedidas o conversacion casual.
3. Agente RAG + Tools: Realiza una busqueda por similitud en la base vectorial ChromaDB para responder preguntas tecnicas y, si es necesario, invoca herramientas del sistema (mock tools para verificar servidor, reiniciar contenedores Docker o consultar logs).

---

## Tech Stack y Requisitos

* Lenguaje: Python 3.10+
* Gestor de Entorno y Paquetes: uv (Gestor ultrarrapido en Rust)
* Orquestacion Multi-Agente: langgraph, langchain
* Inferencia y Embeddings Locales: Ollama (llama3.2 y nomic-embed-text)
* Base de Datos Vectorial: ChromaDB
* Estandar de Codigo: Guia de Estilo de Python de Google (Type hints, Google-style docstrings).

---

## Prerrequisitos

Antes de comenzar, asegurate de tener instalado en tu sistema:

1. Python 3.10 o superior.
2. uv (Gestor de proyectos Python).
3. Ollama (disponible en la web oficial de Ollama).

---

## Instalacion y Configuracion

### 1. Descargar los modelos en Ollama
Asegurate de que el servicio de Ollama este ejecutandose y descarga los modelos requeridos:

ollama pull llama3.2
ollama pull nomic-embed-text

### 2. Clonar el repositorio
Obten el codigo fuente desde tu repositorio remoto o carpeta local y accede al directorio del proyecto:

cd Support-Rag

### 3. Sincronizar el entorno de dependencias
Utiliza uv para crear el entorno virtual e instalar todas las dependencias bloqueadas automaticamente:

uv sync

---

## Uso e Instrucciones de Ejecucion

Para iniciar el pipeline multi-agente ejecuta:

uv run python src/support_rag/multi_agent.py

### ¿Que sucedera durante la ejecucion?

1. Si no existe la carpeta ./docs, el programa creara una automaticamente con un documento de soporte de muestra (manual_soporte.txt).
2. Se inicializara o cargara la base de datos vectorial en ./chroma_db.
3. El grafo compilado procesara las consultas enviadas y mostrara en consola las trazas de ejecucion en tiempo real (que nodo se ejecuta, si se invocan tools y la respuesta final).

---

## Estructura del Proyecto

Support-Rag/
|-- chroma_db/             # Base de datos vectorial persistente (generada automaticamente)
|-- docs/                  # Documentos fuente (.txt, .pdf) para el pipeline RAG
|-- src/
|   `-- support_rag/
|       |-- __init__.py
|       `-- multi_agent.py # Implementacion del grafo de estado (LangGraph + RAG + Tools)
|-- pyproject.toml         # Configuracion del proyecto y dependencias
|-- uv.lock                # Archivo de bloqueo de dependencias de uv
`-- README.md              # Documentacion del proyecto

---

## Estandares de Calidad

Este proyecto esta construido siguiendo la Guia de Estilo de Python de Google:
* Anotaciones de Tipo (Type Hints): Tipado estatico completo en variables, funciones y contratos de retorno.
* Docstrings Estructurados: Formato oficial de Google (Args:, Returns:, Attributes:).
* Validacion de Datos: Uso estricto de Pydantic para evitar alucinaciones en el enrutamiento.

---

