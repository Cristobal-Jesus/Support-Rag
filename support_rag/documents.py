"""Leer Markdown y crear fragmentos que conservan su procedencia."""

import dataclasses
import pathlib
import re

DOMAINS = ("technical", "policies")
DEFAULT_DOCUMENTS = (
    pathlib.Path(__file__).resolve().parent.parent / "knowledge_base"
)


@dataclasses.dataclass(frozen=True)
class Chunk:
    """Una pieza de texto con la información necesaria para citarla.

    Attributes:
        id: Identificador del archivo, sección y ventana de palabras.
        source: Ruta del archivo relativa al directorio del corpus.
        domain: Dominio documental, technical o policies.
        section: Encabezado de la sección que contiene el fragmento.
        text: Contenido del fragmento con espacios normalizados.
    """

    id: str
    source: str
    domain: str
    section: str
    text: str


def split_words(
    text: str, max_words: int = 120, overlap: int = 20
) -> list[str]:
    """Divide un texto en ventanas de palabras con solapamiento.

    Args:
        text: Texto de una única sección documental.
        max_words: Número máximo de palabras por ventana, mayor que cero.
        overlap: Palabras compartidas entre ventanas; de cero a max_words - 1.

    Returns:
        Fragmentos en su orden original, o una lista vacía si no hay palabras.
    """
    if max_words < 1 or not 0 <= overlap < max_words:
        raise ValueError(
            "El tamaño debe ser positivo y 0 <= overlap < max_words."
        )
    words = text.split()
    fragments = []
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        fragments.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - overlap
    return fragments


def load_chunks(
    directory: pathlib.Path = DEFAULT_DOCUMENTS,
    max_words: int = 120,
    overlap: int = 20,
) -> list[Chunk]:
    """Carga fragmentos de los documentos técnicos y de políticas.

    Args:
        directory: Directorio que contiene las carpetas technical y policies.
        max_words: Número máximo de palabras por ventana, mayor que cero.
        overlap: Palabras compartidas entre ventanas; de cero a max_words - 1.

    Returns:
        Fragmentos ordenados por dominio, archivo, sección y ventana.

    Raises:
        ValueError: El directorio no existe, el corpus está vacío o contiene
            texto fuera de secciones delimitadas por encabezados ##.
        OSError: No se puede acceder a un documento.
        UnicodeError: Un documento no tiene una codificación UTF-8 válida.
    """
    # Validar la ventana incluso si no llegamos a encontrar documentos.
    split_words("", max_words, overlap)
    directory = pathlib.Path(directory)
    if not directory.is_dir():
        raise ValueError(f"No existe el directorio de documentos: {directory}")

    chunks = []
    for domain in DOMAINS:
        for path in sorted((directory / domain).rglob("*.md")):
            chunks.extend(_load_document(path, directory, max_words, overlap))
    if not chunks:
        raise ValueError(
            "No hay contenido Markdown en technical/ ni policies/."
        )
    return chunks


def _load_document(
    path: pathlib.Path,
    directory: pathlib.Path,
    max_words: int,
    overlap: int,
) -> list[Chunk]:
    """Carga un Markdown manteniendo separadas sus secciones.

    Args:
        path: Ruta del archivo Markdown.
        directory: Raíz del corpus utilizada para calcular la procedencia.
        max_words: Número máximo de palabras por fragmento.
        overlap: Número de palabras compartidas entre ventanas.

    Returns:
        Fragmentos del archivo con su sección y dominio.

    Raises:
        ValueError: Hay contenido fuera de encabezados ## o estos no existen.
        OSError: No se puede leer el archivo.
        UnicodeError: El archivo no contiene texto UTF-8 válido.
    """
    raw = path.read_text(encoding="utf-8-sig")
    sections = re.split(r"^##[ \t]+(.+)$", raw, flags=re.MULTILINE)
    preamble = re.sub(r"^#[ \t]+.+$", "", sections[0], flags=re.MULTILINE)
    if preamble.strip() or len(sections) == 1:
        raise ValueError(
            f"{path.name}: coloca el contenido bajo encabezados ##."
        )
    relative_path = path.relative_to(directory)
    source = relative_path.as_posix()
    chunks = []
    for section_number, offset in enumerate(range(1, len(sections), 2), 1):
        pieces = split_words(sections[offset + 1], max_words, overlap)
        for piece_number, text in enumerate(pieces, 1):
            chunks.append(
                Chunk(
                    id=f"{source}#s{section_number}-c{piece_number}",
                    source=source,
                    domain=relative_path.parts[0],
                    section=sections[offset].strip(),
                    text=text,
                )
            )
    return chunks
