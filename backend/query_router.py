"""
Query Router and Classifier
Routes user queries to appropriate handlers (SQL, vector search, cache, LLM)
"""

import logging
from typing import Dict, List
from enum import Enum
from dataclasses import dataclass
import asyncio

from transformers import pipeline

logger = logging.getLogger(__name__)


# ---------------------------
# ENUMS
# ---------------------------

class QueryType(Enum):
    CACHED_RESPONSE = "cached"
    VECTOR_SEARCH = "vector"
    HYBRID_SEARCH = "hybrid"
    POLICY_DETAILS = "policy"
    CLAIMS = "claims"
    PRICING = "pricing"
    FAQ = "faq"
    GENERAL = "general"
    COMPLEX = "complex"


class ExecutionStrategy(Enum):
    CACHE_ONLY = "cache"
    FAST_PATH = "fast"
    BALANCED = "balanced"
    FULL = "full"
    SPECULATIVE = "speculative"


# ---------------------------
# ROUTING RESULT
# ---------------------------

@dataclass
class RoutingDecision:
    query_type: QueryType
    strategy: ExecutionStrategy
    use_cache: bool
    use_vector_search: bool
    use_keyword_search: bool
    use_llm: bool
    use_sql: bool
    confidence: float
    reasoning: str


# ---------------------------
# CLASSIFIER
# ---------------------------

class QueryClassifier:
    """
    Lightweight classifier using:
    1. Keyword heuristics
    2. Small zero-shot model fallback
    """

    def __init__(self):

        self.classifier = None
        self.is_initialized = False
        self.keywords_map = self._build_keywords_map()

    @staticmethod
    def _build_keywords_map() -> Dict[QueryType, List[str]]:

        return {
            QueryType.PRICING: [
                "price", "cost", "premium", "rate",
                "how much", "payment", "charge"
            ],

            QueryType.CLAIMS: [
                "claim", "file claim", "submit claim",
                "reimburse", "reimbursement", "deductible"
            ],

            QueryType.POLICY_DETAILS: [
                "policy", "coverage", "plan",
                "benefit", "limit", "renewal"
            ],

            QueryType.FAQ: [
                "how do i", "how can i", "where can i",
                "do you offer", "is it possible"
            ]
        }

    async def initialize(self):

        try:

            # MUCH smaller model
            self.classifier = pipeline(
                "zero-shot-classification",
                model="valhalla/distilbart-mnli-12-1",
                device=-1
            )

            self.is_initialized = True
            logger.info("Classifier initialized")

        except Exception as e:

            logger.warning(f"Classifier load failed: {e}")
            self.is_initialized = False

    async def classify(self, query: str) -> QueryType:

        query_lower = query.lower()

        # -------------------
        # KEYWORD MATCH
        # -------------------

        for qtype, keywords in self.keywords_map.items():

            for keyword in keywords:

                if keyword in query_lower:
                    return qtype

        # -------------------
        # ML CLASSIFICATION
        # -------------------

        if self.is_initialized and self.classifier:

            try:

                candidate_labels = [
                    "pricing question",
                    "claims question",
                    "policy question",
                    "faq question",
                    "general question"
                ]

                result = await asyncio.to_thread(
                    self.classifier,
                    query,
                    candidate_labels
                )

                label = result["labels"][0].lower()

                if "pricing" in label:
                    return QueryType.PRICING

                if "claims" in label:
                    return QueryType.CLAIMS

                if "policy" in label:
                    return QueryType.POLICY_DETAILS

                if "faq" in label:
                    return QueryType.FAQ

            except Exception as e:
                logger.warning(f"ML classification error: {e}")

        # -------------------
        # COMPLEX DETECTION
        # -------------------

        if len(query.split()) > 20:
            return QueryType.COMPLEX

        return QueryType.GENERAL


# ---------------------------
# ROUTER
# ---------------------------

class QueryRouter:

    def __init__(self, classifier: QueryClassifier):

        self.classifier = classifier
        self.query_stats: Dict = {}

    async def route(self, query: str, has_cache_hit: bool = False) -> RoutingDecision:

        # Cache short-circuit
        if has_cache_hit:

            return RoutingDecision(
                query_type=QueryType.CACHED_RESPONSE,
                strategy=ExecutionStrategy.CACHE_ONLY,
                use_cache=True,
                use_vector_search=False,
                use_keyword_search=False,
                use_llm=False,
                use_sql=False,
                confidence=1.0,
                reasoning="Cache hit"
            )

        query_type = await self.classifier.classify(query)

        # -------------------
        # ROUTING LOGIC
        # -------------------

        if query_type == QueryType.PRICING:

            return RoutingDecision(
                query_type=query_type,
                strategy=ExecutionStrategy.FAST_PATH,
                use_cache=True,
                use_vector_search=True,
                use_keyword_search=True,
                use_llm=False,
                use_sql=True,
                confidence=0.95,
                reasoning="Pricing resolved via SQL + search"
            )

        elif query_type == QueryType.CLAIMS:

            return RoutingDecision(
                query_type=query_type,
                strategy=ExecutionStrategy.BALANCED,
                use_cache=True,
                use_vector_search=True,
                use_keyword_search=True,
                use_llm=True,
                use_sql=False,
                confidence=0.9,
                reasoning="Claims require explanation context"
            )

        elif query_type == QueryType.POLICY_DETAILS:

            return RoutingDecision(
                query_type=query_type,
                strategy=ExecutionStrategy.BALANCED,
                use_cache=True,
                use_vector_search=True,
                use_keyword_search=True,
                use_llm=False,
                use_sql=True,
                confidence=0.9,
                reasoning="Policy info from structured data"
            )

        elif query_type == QueryType.FAQ:

            return RoutingDecision(
                query_type=query_type,
                strategy=ExecutionStrategy.FAST_PATH,
                use_cache=True,
                use_vector_search=True,
                use_keyword_search=True,
                use_llm=False,
                use_sql=False,
                confidence=0.88,
                reasoning="FAQ retrieval"
            )

        elif query_type == QueryType.COMPLEX:

            return RoutingDecision(
                query_type=query_type,
                strategy=ExecutionStrategy.FULL,
                use_cache=True,
                use_vector_search=True,
                use_keyword_search=True,
                use_llm=True,
                use_sql=False,
                confidence=0.8,
                reasoning="Complex query needs LLM reasoning"
            )

        return RoutingDecision(
            query_type=query_type,
            strategy=ExecutionStrategy.BALANCED,
            use_cache=True,
            use_vector_search=True,
            use_keyword_search=True,
            use_llm=True,
            use_sql=False,
            confidence=0.75,
            reasoning="General query"
        )

    # ---------------------------
    # STATS
    # ---------------------------

    def record_query(self, query_type: QueryType, latency_ms: float):

        key = query_type.value

        if key not in self.query_stats:
            self.query_stats[key] = {
                "count": 0,
                "total_latency": 0.0,
                "avg_latency": 0.0
            }

        stat = self.query_stats[key]

        stat["count"] += 1
        stat["total_latency"] += latency_ms
        stat["avg_latency"] = stat["total_latency"] / stat["count"]

    def get_stats(self) -> Dict:

        return self.query_stats