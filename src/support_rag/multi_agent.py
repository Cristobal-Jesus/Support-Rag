"""Sistema multi-agente con orquestador y RAG utilizando Ollama.

Este módulo implementa un flujo de orquestación local que clasifica las
consultas del usuario y las delega a un agente especializado en RAG
o a un agente de conversación general.
"""

import os
from typing import List, Literal

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_unstructured import UnstructuredLoader
from pydantic import BaseModel, Field

CHROMA_PATH = "./chroma_db"
DOCS_DIR = "./docs"
LLM_MODEL = "llama3.2"
EMBEDDING_MODEL = "nomic-embed-text"


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
                "1. Para configurar las credenciales, edita el archivo .env "
                "en la raiz del proyecto.\n"
                "2. El puerto por defecto del servicio API es el 8000.\n"
                "3. Para reiniciar el contenedor ejecuta: "
                "docker-compose restart support-rag.\n"
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


class RouteQuery(BaseModel):
    """Esquema Pydantic para clasificar la intención de la consulta."""

    destino: Literal["agente_rag", "agente_general"] = Field(
        description=(
            "Elige 'agente_rag' si la pregunta es sobre soporte tecnico, "
            "configuracion, errores o instalacion. Elige 'agente_general' "
            "para saludos o charla casual."
        )
    )


def agente_rag(
    consulta: str, retriever: VectorStoreRetriever, llm: ChatOllama
) -> str:
    """Procesa consultas técnicas utilizando RAG sobre los documentos indexados.

    Args:
        consulta: Pregunta formulada por el usuario.
        retriever: Recuperador de fragmentos de la base vectorial.
        llm: Instancia del modelo de lenguaje local.

    Returns:
        str: Respuesta generada por el agente basada en el contexto.
    """
    docs = retriever.invoke(consulta)
    contexto = "\n\n".join([doc.page_content for doc in docs])

    prompt = (
        "Eres el Agente Especialista en Soporte Tecnico. "
        "Responde a la duda utilizando UNICAMENTE la siguiente informacion "
        "de contexto:\n\n"
        f"Contexto:\n{contexto}\n\n"
        f"Pregunta: {consulta}"
    )
    respuesta = llm.invoke(prompt)
    return f"[Agente RAG]:\n{respuesta.content}"


def agente_general(consulta: str, llm: ChatOllama) -> str:
    """Procesa consultas generales no relacionadas con soporte técnico.

    Args:
        consulta: Pregunta o saludo del usuario.
        llm: Instancia del modelo de lenguaje local.

    Returns:
        str: Respuesta amable y general del modelo.
    """
    prompt = (
        "Eres el Agente de Atencion General. Responde de forma amable "
        "y directa a la siguiente entrada.\n\n"
        f"Pregunta: {consulta}"
    )
    respuesta = llm.invoke(prompt)
    return f"[Agente General]:\n{respuesta.content}"


def orquestador(
    consulta: str,
    retriever: VectorStoreRetriever,
    llm: ChatOllama,
) -> str:
    """Clasifica la consulta del usuario y la encamina al agente adecuado.

    Args:
        consulta: Mensaje o pregunta enviada por el usuario.
        retriever: Recuperador de fragmentos para el agente RAG.
        llm: Instancia del modelo de lenguaje local.

    Returns:
        str: Respuesta final obtenida del agente delegado.
    """
    system_prompt = (
        "Tu unica tarea es clasificar la intención de la consulta. "
        "Responde 'agente_rag' si es una pregunta tecnica o de soporte, "
        "o 'agente_general' si es un saludo o charla informal."
    )

    router_llm = llm.with_structured_output(RouteQuery)
    decision = router_llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": consulta},
        ]
    )

    if decision.destino == "agente_rag":
        return agente_rag(consulta, retriever, llm)

    return agente_general(consulta, llm)


def main() -> None:
    """Punto de entrada principal para ejecutar el sistema multi-agente."""
    # Nota: Si cambiaste de modelo de embeddings, elimina la carpeta ./chroma_db antes de ejecutar
    vectorstore = inicializar_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    llm = ChatOllama(model=LLM_MODEL, temperature=0)

    print("=== Sistema Multi-Agente Iniciado ===")

    consulta_1 = "Hola, buenos dias"
    print(f"\nConsulta: {consulta_1}")
    print(orquestador(consulta_1, retriever, llm))

    consulta_2 = "Como reinicio el servicio de Support-Rag?"
    print(f"\nConsulta: {consulta_2}")
    print(orquestador(consulta_2, retriever, llm))


if __name__ == "__main__":
    main()