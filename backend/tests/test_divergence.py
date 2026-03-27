import unittest

from app.schemas.analysis import AtomicClaim, PerArticleFraming
from app.services.divergence import compute_divergence, lexical_fallback_emphasis


class TestDivergence(unittest.TestCase):
    def test_opposing_stance_increases_divergence(self) -> None:
        base_claims = [AtomicClaim(claim="The policy was announced on Monday.", support_quote=None)]
        neutral = PerArticleFraming(
            article_index=0,
            source_label="A",
            stance="neutral",
            sentiment_score=0.0,
            emphasis_terms=["policy", "announcement"],
            protagonist_descriptor="government officials",
            antagonist_descriptor="opposition leaders",
            atomic_claims=base_claims,
            omission_candidates=[],
            evidence=[],
            analysis_notes=None,
        )
        twin = neutral.model_copy(update={"article_index": 1, "source_label": "B"})
        opposed = neutral.model_copy(
            update={
                "article_index": 1,
                "source_label": "B",
                "stance": "critical",
                "sentiment_score": -0.8,
                "emphasis_terms": ["crisis", "backlash", "chaos"],
            },
        )

        same_score = compute_divergence([neutral, twin]).score_0_100
        diff_score = compute_divergence([neutral, opposed]).score_0_100
        self.assertGreater(diff_score, same_score)

    def test_lexical_fallback_emphasis_extracts_tokens(self) -> None:
        text = "The market rallied sharply after the policy announcement and earnings guidance."
        terms = lexical_fallback_emphasis(text, top_k=5)
        self.assertIn("market", terms)
        self.assertIn("policy", terms)


if __name__ == "__main__":
    unittest.main()
