"""Scaffold for planned FIX specification retrieval.

This module does not currently implement hybrid retrieval, vector search,
BM25, reranking, LLM generation, or RAGAS evaluation.

It preserves an interface for the planned contextual-validation layer while
the deterministic FIX validator remains the executable source of validation.
"""

from typing import Dict, List


class FIXSpecRAG:
    def __init__(self):
        self.spec_docs = ["FIX specification", "regulatory/onboarding rules"]

    def retrieve(self, fix_msg: str, k: int = 5) -> List[Dict]:
        """Placeholder for future FIX-spec retrieval."""
        return []

    def validate_with_context(self, fix_msg: str, ctx: List[Dict]) -> Dict:
        """Placeholder for future context-grounded validation/evaluation."""
        return {
            "status": "NOT_IMPLEMENTED",
            "violations": [],
        }