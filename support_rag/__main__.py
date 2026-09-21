"""Ejecuta la inspección y la búsqueda con python -m support_rag."""

import argparse
import pathlib

from support_rag import documents
from support_rag import retrieval


def _build_parser() -> argparse.ArgumentParser:
    """Crea el lector de argumentos de los comandos inspect y search."""
    parser = argparse.ArgumentParser(
        description="Support RAG · etapa 1 · recuperación documental"
    )
    parser.add_argument(
        "--documents", type=pathlib.Path, default=documents.DEFAULT_DOCUMENTS
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("inspect", help="Ver documentos y fragmentos.")
    search = commands.add_parser(
        "search", help="Buscar fragmentos por coincidencia de palabras."
    )
    search.add_argument("question")
    search.add_argument("--domain", choices=documents.DOMAINS)
    search.add_argument("--top-k", type=int, default=3)
    return parser


def main() -> None:
    """Lee los argumentos y muestra fragmentos o resultados de búsqueda."""
    parser = _build_parser()
    args = parser.parse_args()
    try:
        chunks = documents.load_chunks(args.documents)
        source_count = len({chunk.source for chunk in chunks})
        print(f"{source_count} documentos · {len(chunks)} fragmentos")
        if args.command == "inspect":
            for chunk in chunks:
                word_count = len(chunk.text.split())
                print(f"[{chunk.id}] {chunk.section} ({word_count} palabras)")
            return

        retriever = retrieval.TfidfRetriever(chunks)
        results = retriever.search(args.question, args.top_k, args.domain)
        print(
            "Búsqueda TF-IDF. El score mide similitud de palabras, "
            "no confianza."
        )
        if not results:
            print(
                "Sin coincidencias de vocabulario. Esto no demuestra "
                "que la respuesta no exista."
            )
        for number, result in enumerate(results, 1):
            print(f"\n{number}. [{result.chunk.id}] · score={result.score:.3f}")
            print(f"Sección: {result.chunk.section}")
            print(result.chunk.text)
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
