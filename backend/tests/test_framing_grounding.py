import unittest

from app.schemas.analysis import EvidenceSpan, PerArticleFraming
from app.services.framing_grounding import (
    inject_verbatim_evidence_fallback,
    quote_appears_in_body,
    sanitize_framing_against_source,
)


class TestFramingGrounding(unittest.TestCase):
    def test_quote_appears_in_body_substring(self) -> None:
        body = "Thousands gathered peacefully at the capital to demand accountability."
        self.assertTrue(quote_appears_in_body("peacefully at the capital", body))

    def test_meta_commentary_removed_from_evidence(self) -> None:
        body = "Police described the gathering as an unlawful assembly."
        row = PerArticleFraming(
            article_index=0,
            source_label="A",
            stance="critical",
            sentiment_score=-0.5,
            emphasis_terms=["assembly"],
            protagonist_descriptor=None,
            antagonist_descriptor=None,
            atomic_claims=[],
            omission_candidates=[],
            evidence=[
                EvidenceSpan(
                    quote="Text is insufficient to determine the tone of the authorities' statement.",
                    role="tone",
                )
            ],
            analysis_notes=None,
        )
        out, changed = sanitize_framing_against_source(row, body)
        self.assertTrue(changed)
        self.assertEqual(out.evidence, [])

    def test_inject_evidence_when_empty(self) -> None:
        body = (
            "Citizens gathered at the capital. They demanded accountability from elected leaders. "
            "Organizers emphasized peaceful assembly."
        )
        row = PerArticleFraming(
            article_index=0,
            source_label="A",
            stance="supportive",
            sentiment_score=0.5,
            emphasis_terms=[],
            protagonist_descriptor=None,
            antagonist_descriptor=None,
            atomic_claims=[],
            omission_candidates=[],
            evidence=[],
            analysis_notes=None,
        )
        out, added = inject_verbatim_evidence_fallback(row, body)
        self.assertTrue(added)
        self.assertGreaterEqual(len(out.evidence), 1)
        for ev in out.evidence:
            self.assertTrue(quote_appears_in_body(ev.quote, body))

    def test_verbatim_quote_kept(self) -> None:
        body = "Citizens emphasized constitutional rights and non-violent assembly."
        row = PerArticleFraming(
            article_index=0,
            source_label="A",
            stance="supportive",
            sentiment_score=0.5,
            emphasis_terms=[],
            protagonist_descriptor=None,
            antagonist_descriptor=None,
            atomic_claims=[],
            omission_candidates=[],
            evidence=[EvidenceSpan(quote="constitutional rights and non-violent assembly", role="emphasis")],
            analysis_notes=None,
        )
        out, changed = sanitize_framing_against_source(row, body)
        self.assertFalse(changed)
        self.assertEqual(len(out.evidence), 1)


if __name__ == "__main__":
    unittest.main()
