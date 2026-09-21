"""Pruebas de comportamiento del corpus y la recuperación; no llaman a APIs."""

import pathlib
import tempfile
import unittest

from support_rag import documents
from support_rag import retrieval


class RetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """Construye una sola vez el índice utilizado por las pruebas."""
        cls.chunks = documents.load_chunks()
        cls.retriever = retrieval.TfidfRetriever(cls.chunks)

    def test_exact_error_finds_its_explanation(self) -> None:
        results = self.retriever.search("E202", top_k=1)
        self.assertEqual(len(results), 1)
        self.assertIn("segundo factor caducado", results[0].chunk.section)
        self.assertEqual(results[0].chunk.source, "technical/errors.md")

    def test_domain_filter_prevents_technical_results(self) -> None:
        results = self.retriever.search(
            "VPN ordenadores personales", top_k=3, domain="policies"
        )
        self.assertTrue(results)
        self.assertTrue(all(r.chunk.domain == "policies" for r in results))
        self.assertTrue(
            any("No está permitido" in r.chunk.text for r in results)
        )

    def test_unknown_vocabulary_does_not_return_arbitrary_documents(
        self,
    ) -> None:
        self.assertEqual(
            self.retriever.search("ornitorrinco astrofotografia"), []
        )
        self.assertEqual(self.retriever.search("de la el"), [])

    def test_windows_preserve_all_words_and_overlap(self) -> None:
        words = [f"palabra{i}" for i in range(35)]
        pieces = documents.split_words(" ".join(words), max_words=12, overlap=3)
        rebuilt = pieces[0].split()
        for before, after in zip(pieces[:-1], pieces[1:], strict=True):
            self.assertEqual(before.split()[-3:], after.split()[:3])
            rebuilt.extend(after.split()[3:])
        self.assertEqual(rebuilt, words)
        self.assertTrue(all(len(piece.split()) <= 12 for piece in pieces))

    def test_chunking_keeps_source_and_section_separate(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            directory = pathlib.Path(folder)
            (directory / "technical").mkdir()
            (directory / "technical" / "demo.md").write_text(
                "# Demo\n\n## Primera\nuno dos tres cuatro cinco seis\n"
                "\n## Segunda\nsiete ocho nueve\n",
                encoding="utf-8",
            )
            chunks = documents.load_chunks(directory, max_words=4, overlap=1)
            self.assertEqual(len(chunks), 3)
            self.assertEqual(
                [c.section for c in chunks], ["Primera", "Primera", "Segunda"]
            )
            self.assertTrue(
                all(c.source == "technical/demo.md" for c in chunks)
            )
            self.assertEqual(len({c.id for c in chunks}), len(chunks))
            self.assertNotIn("siete", chunks[1].text)

    def test_text_outside_sections_is_not_silently_discarded(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            directory = pathlib.Path(folder)
            (directory / "technical").mkdir()
            (directory / "technical" / "demo.md").write_text(
                "# Demo\nTexto que no debe perderse.\n## Sección\nContenido.",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "encabezados"):
                documents.load_chunks(directory)

    def test_invalid_inputs_fail_with_clear_errors(self) -> None:
        with self.assertRaises(ValueError):
            self.retriever.search("   ")
        with self.assertRaises(ValueError):
            self.retriever.search("VPN", top_k=0)
        with self.assertRaises(ValueError):
            self.retriever.search("VPN", domain="inventado")
        with self.assertRaises(ValueError):
            documents.split_words("texto", max_words=10, overlap=10)
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "No hay contenido"):
                documents.load_chunks(pathlib.Path(folder))


if __name__ == "__main__":
    unittest.main()
