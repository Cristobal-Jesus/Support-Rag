"""Sistema Multi-Agente con LangGraph y Herramientas Simuladas (Mock Tools).

Adhiere a la Guía de Estilo de Python de Google.
"""

import os
from typing import Any, Dict, List, Literal, TypedDict

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_unstructured import UnstructuredLoader
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field

# Constantes de configuración del sistema
CHROMA_PATH: str = "./chroma_db"
DOCS_DIR: str = "./docs"
LLM_MODEL: str = "llama3.2"
EMBEDDING_MODEL: str = "nomic-embed-text"


# ------------------------------------------------------------------------------
# 1. Definición de Herramientas Simuladas (Mock Tools)
# ------------------------------------------------------------------------------
@tool
def reiniciar_servicio_docker(nombre_servicio: str) -> str:
    """Simula el reinicio de un contenedor o servicio Docker en el servidor.

    Args:
        nombre_servicio: El nombre exacto del servicio a reiniciar (ej. 'support-rag').

    Returns:
        str: Mensaje simulado de confirmación del estado del servicio.
    """
    return (
        f"[MOCK TOOL]: El servicio '{nombre_servicio}' se ha reiniciado "
        "correctamente en el contenedor Docker local. Estado actual: RUNNING."
    )


@tool
def verificar_estado_servidor() -> str:
    """Simula una comprobación de salud del servidor (CPU, Memoria y Uptime).

    Returns:
        str: Reporte simulado con las métricas del sistema.
    """
    return (
        "[MOCK TOOL]: Estado del Servidor -> CPU: 12% | RAM: 4.2GB / 16GB "
        "| Disco: 45% usado | Uptime: 14 días, 3 horas | Status: OK."
    )


@tool
def obtener_logs_sistema(lineas: int = 5) -> str:
    """Simula la lectura de los últimos registros de log del sistema de soporte.

    Args:
        lineas: Cantidad de líneas de log a recuperar. Por defecto es 5.

    Returns:
        str: Salida simulada de los logs del sistema.
    """
    return (
        f"[MOCK TOOL]: Recuperando las últimas {lineas} líneas de log:\n"
        "2026-09-21 14:00:01 [INFO] Servicio iniciado correctamente.\n"
        "2026-09-21 14:15:22 [INFO] Solicitud RAG procesada - HTTP 200.\n"
        "2026-09-21 14:30:10 [INFO] Búsqueda en ChromaDB ejecutada con éxito."
    )


# Lista de herramientas disponibles para el agente técnico
HERRAMIENTAS_SOPORTE = [
    reiniciar_servicio_docker,
    verificar_estado_servidor,
    obtener_logs_sistema,
]


# ------------------------------------------------------------------------------
# 2. Definición del Estado del Grafo
# ------------------------------------------------------------------------------
class AgentState(TypedDict):
    """Estado compartido que circula a través de todos los nodos del grafo.

    Attributes:
        consulta: La entrada o pregunta formulada por el usuario.
        destino: La decisión tomada por el nodo orquestador.
        messages: Historial de mensajes para el flujo de herramientas.
        respuesta: La respuesta final generada por el agente.
    """

    consulta: str
    destino: str
    messages: List[Any]
    respuesta: str


# ------------------------------------------------------------------------------
# 3. Base de Datos Vectorial
# ------------------------------------------------------------------------------
def inicializar_vectorstore() -> Chroma:
    """Carga o inicializa la base de datos vectorial Chroma local.

    Returns:
        Chroma: Instancia de la base de datos vectorial configurada.
    """
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

    if os.path.exists(CHROMA_PATH) and os.listdir(CHROMA_PATH):
        return Chroma(
            collection_name="support_docs",
            embedding_function=embeddings,
            persist_directory=CHROMA_PATH,
        )

    os.makedirs(DOCS_DIR, exist_ok=True)

    if not os.listdir(DOCS_DIR):
        archivo_prueba = os.path.join(DOCS_DIR, "manual_soporte.txt")
        with open(archivo_prueba, "w", encoding="utf-8") as file_handle:
            file_handle.write(
                "DOCUMENTO DE SOPORTE SUPPORT-RAG:\n"
                "1. Para configurar las credenciales, edita el archivo .env.\n"
                "2. El puerto por defecto del servicio API es el 8000.\n"
                "3. Para reiniciar el servicio ejecuta: docker-compose restart support-rag.\n"
            )

    documentos: List[Document] = []
    for archivo in os.listdir(DOCS_DIR):
        ruta = os.path.join(DOCS_DIR, archivo)
        if archivo.endswith((".txt", ".pdf")):
            loader = UnstructuredLoader(ruta)
            documentos.extend(loader.load())

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    chunks = text_splitter.split_documents(documentos)

    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name="support_docs",
        persist_directory=CHROMA_PATH,
    )


# ------------------------------------------------------------------------------
# 4. Esquema Pydantic para Enrutamiento
# ------------------------------------------------------------------------------
class RouteQuery(BaseModel):
    """Esquema Pydantic para el enrutamiento estructurado de consultas.

    Attributes:
        destino: Etiqueta elegida por el LLM.
    """

    destino: Literal["agente_rag", "agente_general"] = Field(
        description=(
            "Elige 'agente_rag' si la pregunta es sobre soporte tecnico, "
            "configuracion, estado del servidor, logs o comandos. "
            "Elige 'agente_general' para saludos o charla casual."
        )
    )


# ------------------------------------------------------------------------------
# 5. Nodos del Grafo
# ------------------------------------------------------------------------------
def nodo_orquestador(state: AgentState, llm: ChatOllama) -> Dict[str, Any]:
    """Nodo del grafo que clasifica la intención del usuario."""
    system_prompt = (
        "Clasifica la intención del usuario. Responde 'agente_rag' para "
        "dudas técnicas, estado del sistema, logs o herramientas; "
        "o 'agente_general' para saludos y conversación casual."
    )
    router_llm = llm.with_structured_output(RouteQuery)
    decision = router_llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": state["consulta"]},
        ]
    )
    return {
        "destino": decision.destino,
        "messages": [("user", state["consulta"])],
    }


def nodo_agente_rag(
    state: AgentState, retriever: VectorStoreRetriever, llm: ChatOllama
) -> Dict[str, Any]:
    """Nodo especializado que cuenta con RAG y acceso a Herramientas."""
    consulta = state["consulta"]
    docs = retriever.invoke(consulta)
    contexto = "\n\n".join([doc.page_content for doc in docs])

    # Vinculamos las mock tools al modelo
    llm_con_herramientas = llm.bind_tools(HERRAMIENTAS_SOPORTE)

    system_prompt = (
        "Eres el Agente de Soporte Técnico. Tienes acceso a información de contexto "
        "y a herramientas para interactuar con el sistema.\n"
        f"Contexto disponible:\n{contexto}"
    )

    mensajes = [("system", system_prompt)] + state.get("messages", [])
    respuesta = llm_con_herramientas.invoke(mensajes)

    return {
        "messages": state.get("messages", []) + [respuesta],
        "respuesta": f"[Agente RAG]:\n{respuesta.content}",
    }


def nodo_agente_general(
    state: AgentState, llm: ChatOllama
) -> Dict[str, str]:
    """Nodo encargado de responder interacciones conversacionales generales."""
    prompt = (
        "Eres el Agente de Atencion General. Responde de forma amable "
        f"a la siguiente entrada:\n\n{state['consulta']}"
    )
    respuesta = llm.invoke(prompt)
    return {"respuesta": f"[Agente General]:\n{respuesta.content}"}


def decidir_siguiente_nodo(state: AgentState) -> str:
    """Función de decisión para la arista condicional del orquestador."""
    return state["destino"]


# ------------------------------------------------------------------------------
# 6. Construcción del Grafo
# ------------------------------------------------------------------------------
def construir_grafo(
    retriever: VectorStoreRetriever, llm: ChatOllama
) -> CompiledStateGraph:
    """Ensambla los nodos, herramientas y aristas en un grafo ejecutable."""
    workflow = StateGraph(AgentState)

    # Nodo preconstruido de LangGraph para ejecutar herramientas
    nodo_herramientas = ToolNode(HERRAMIENTAS_SOPORTE)

    # Registro de Nodos
    workflow.add_node("orquestador", lambda state: nodo_orquestador(state, llm))
    workflow.add_node(
        "agente_rag", lambda state: nodo_agente_rag(state, retriever, llm)
    )
    workflow.add_node(
        "agente_general", lambda state: nodo_agente_general(state, llm)
    )
    workflow.add_node("ejecutar_herramientas", nodo_herramientas)

    # Configuración de entrada
    workflow.set_entry_point("orquestador")

    # Arista condicional desde el orquestador
    workflow.add_conditional_edges(
        "orquestador",
        decidir_siguiente_nodo,
        {
            "agente_rag": "agente_rag",
            "agente_general": "agente_general",
        },
    )

    # Arista condicional desde Agente RAG: ¿Quiere llamar a una herramienta o terminar?
    workflow.add_conditional_edges(
        "agente_rag",
        tools_condition,
        {
            "tools": "ejecutar_herramientas",
            "__end__": END,
        },
    )

    # Tras ejecutar la herramienta, regresa al Agente RAG para dar la respuesta final
    workflow.add_edge("ejecutar_herramientas", "agente_rag")
    workflow.add_edge("agente_general", END)

    return workflow.compile()


# ------------------------------------------------------------------------------
# 7. Función Principal con Trazas de Ejecución
# ------------------------------------------------------------------------------
def main() -> None:
    """Ejecuta el sistema multi-agente evaluando el uso de herramientas."""
    vectorstore = inicializar_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    llm = ChatOllama(model=LLM_MODEL, temperature=0)

    app = construir_grafo(retriever, llm)

    print("=== Sistema Multi-Agente con LangGraph & Mock Tools ===")

    # Prueba de llamada a Tool
    consulta = "¿Puedes verificar el estado del servidor y mostrarme los logs?"
    print(f"\nConsulta: {consulta}")
    print("--- Trazas de ejecución en tiempo real ---")

    for event in app.stream({"consulta": consulta}):
        for node_name, state_update in event.items():
            print(f"-> Nodo ejecutado: [{node_name}]")
            if "respuesta" in state_update and state_update["respuesta"]:
                print(f"   Salida: {state_update['respuesta']}\n")


if __name__ == "__main__":
    main()
