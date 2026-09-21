"""Baseline léxico TF-IDF: recuperar evidencia antes de generar respuestas."""

import dataclasses

from sklearn.feature_extraction import text as sklearn_text

from support_rag import documents

# Lista pequeña y explícita. Se usan formas sin tildes porque las normalizamos.
# Conservamos palabras como 'no' y 'sin', que pueden importar en una política.
_STOP_WORDS = tuple(
    "a al algo ante como con cual cuando de del desde donde el ella en es "
    "esta este esto hay la las le les lo los me mi mis o para pero por "
    "porque que se si su sus te tu tus un una uno unos unas y yo".split()
)


@dataclasses.dataclass(frozen=True)
class SearchResult:
    """Un fragmento recuperado y su puntuación de similitud léxica.

    Attributes:
        chunk: Fragmento con su procedencia documental.
        score: Similitud del coseno; no representa una probabilidad de acierto.
    """

    chunk: documents.Chunk
    score: float


# Un recuperador ofrece una sola operación pública: buscar.
# pylint: disable-next=too-few-public-methods
class TfidfRetriever:
    """Un índice en memoria. No usa un LLM ni embeddings semánticos."""

    def __init__(self, chunks: list[documents.Chunk]) -> None:
        """Construye el índice léxico a partir de los fragmentos.

        Args:
            chunks: Lista no vacía de fragmentos que contienen texto.

        Raises:
            ValueError: Los fragmentos no permiten construir un vocabulario.
        """
        if not chunks:
            raise ValueError(
                "No se puede indexar una lista vacía de fragmentos."
            )
        self._chunks = list(chunks)
        self._vectorizer = sklearn_text.TfidfVectorizer(
            lowercase=True,
            strip_accents="unicode",
            stop_words=list(_STOP_WORDS),
            ngram_range=(1, 2),
            norm="l2",
        )
        texts = [f"{chunk.section}\n{chunk.text}" for chunk in self._chunks]
        self._matrix = self._vectorizer.fit_transform(texts)

    def search(
        self, question: str, top_k: int = 3, domain: str | None = None
    ) -> list[SearchResult]:
        """Recupera los fragmentos con mayor similitud de palabras.

        Args:
            question: Consulta que debe contener algún carácter no blanco.
            top_k: Número máximo de resultados, mayor que cero.
            domain: technical, policies o None para buscar en ambos dominios.

        Returns:
            Resultados con puntuación positiva, ordenados de mayor a menor.
            Los empates se ordenan por identificador. Una lista vacía solo
            indica ausencia de coincidencias de vocabulario.
        """
        if not question.strip():
            raise ValueError("Escribe una pregunta que no esté vacía.")
        if top_k < 1:
            raise ValueError("top_k debe ser al menos 1.")
        if domain is not None and domain not in documents.DOMAINS:
            raise ValueError(f"Dominio desconocido: {domain}")

        # La pregunta debe usar el mismo vocabulario que los documentos.
        query = self._vectorizer.transform([question])
        # Con vectores normalizados, producto escalar y coseno coinciden.
        scores = (self._matrix @ query.T).toarray().ravel()
        matches = [
            SearchResult(chunk=chunk, score=float(score))
            for chunk, score in zip(self._chunks, scores, strict=True)
            if score > 0 and (domain is None or chunk.domain == domain)
        ]
        matches.sort(key=lambda result: (-result.score, result.chunk.id))
        return matches[:top_k]
