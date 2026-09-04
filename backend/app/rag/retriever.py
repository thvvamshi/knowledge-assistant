from dataclasses import dataclass
import re

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.embedder import embed_texts
from app.models.transcript import TranscriptChunk


DEFAULT_TOP_K = 5
DEFAULT_SIMILARITY_THRESHOLD = 0.55

VECTOR_CANDIDATE_MULTIPLIER = 5
MIN_CANDIDATES = 20

RRF_K = 60

# Weighting for the final deterministic reranker.
SEMANTIC_WEIGHT = 0.65
LEXICAL_WEIGHT = 0.35


@dataclass
class RetrievedChunk:
    id: str
    episode_title: str
    guest_name: str | None
    episode_date: str | None
    timestamp: str | None
    content: str
    source_path: str
    youtube_url: str | None
    video_id: str | None
    similarity: float


def _youtube_timestamp_url(
    youtube_url: str | None,
    timestamp: str | None,
) -> str | None:
    if not youtube_url or not timestamp:
        return youtube_url

    try:
        hours, minutes, seconds = map(int, timestamp.split(":"))
        total_seconds = hours * 3600 + minutes * 60 + seconds
    except ValueError:
        return youtube_url

    separator = "&" if "?" in youtube_url else "?"
    return f"{youtube_url}{separator}t={total_seconds}s"


def _episode_key(result: RetrievedChunk) -> tuple[str, str | None]:
    return (
        result.episode_title.strip().lower(),
        result.guest_name.strip().lower() if result.guest_name else None,
    )


def _chunk_key(result: RetrievedChunk) -> tuple:
    return (
        result.episode_title.strip().lower(),
        result.timestamp,
        result.content.strip(),
    )


def _diversify_results(
    results: list[RetrievedChunk],
    top_k: int,
) -> list[RetrievedChunk]:
    if not results:
        return []

    selected: list[RetrievedChunk] = []
    seen_chunks: set[tuple] = set()
    seen_episodes: set[tuple[str, str | None]] = set()

    # First pass: one chunk per episode.
    for result in results:
        chunk_key = _chunk_key(result)
        episode_key = _episode_key(result)

        if chunk_key in seen_chunks:
            continue

        if episode_key in seen_episodes:
            continue

        selected.append(result)
        seen_chunks.add(chunk_key)
        seen_episodes.add(episode_key)

        if len(selected) >= top_k:
            return selected

    # Second pass: fill remaining slots with unique chunks.
    for result in results:
        chunk_key = _chunk_key(result)

        if chunk_key in seen_chunks:
            continue

        selected.append(result)
        seen_chunks.add(chunk_key)

        if len(selected) >= top_k:
            break

    return selected


def _to_retrieved_chunk(
    chunk: TranscriptChunk,
    similarity: float,
) -> RetrievedChunk:
    return RetrievedChunk(
        id=str(chunk.id),
        episode_title=chunk.episode_title,
        guest_name=chunk.guest_name,
        episode_date=chunk.episode_date,
        timestamp=chunk.timestamp,
        content=chunk.content,
        source_path=chunk.source_path,
        youtube_url=_youtube_timestamp_url(
            chunk.youtube_url,
            chunk.timestamp,
        ),
        video_id=chunk.video_id,
        similarity=similarity,
    )


async def _vector_search(
    session: AsyncSession,
    query_embedding: list[float],
    candidate_limit: int,
    similarity_threshold: float,
) -> list[RetrievedChunk]:
    distance = TranscriptChunk.embedding.cosine_distance(query_embedding)
    similarity = 1 - distance

    statement = (
        select(
            TranscriptChunk,
            similarity.label("similarity"),
        )
        .where(similarity >= similarity_threshold)
        .order_by(distance)
        .limit(candidate_limit)
    )

    result = await session.execute(statement)

    candidates: list[RetrievedChunk] = []

    for chunk, score in result.all():
        candidates.append(
            _to_retrieved_chunk(
                chunk=chunk,
                similarity=float(score),
            )
        )

    return candidates


async def _lexical_search(
    session: AsyncSession,
    query: str,
    candidate_limit: int,
) -> list[RetrievedChunk]:
    search_query = func.websearch_to_tsquery(
        "english",
        query,
    )

    search_vector = func.to_tsvector(
        "english",
        TranscriptChunk.content,
    )

    lexical_rank = func.ts_rank_cd(
        search_vector,
        search_query,
    )

    statement = (
        select(
            TranscriptChunk,
            lexical_rank.label("lexical_rank"),
        )
        .where(
            search_vector.op("@@")(search_query),
        )
        .order_by(lexical_rank.desc())
        .limit(candidate_limit)
    )

    result = await session.execute(statement)

    candidates: list[RetrievedChunk] = []

    for chunk, _lexical_score in result.all():
        candidates.append(
            _to_retrieved_chunk(
                chunk=chunk,
                similarity=0.0,
            )
        )

    return candidates


def _reciprocal_rank_fusion(
    vector_results: list[RetrievedChunk],
    lexical_results: list[RetrievedChunk],
) -> list[RetrievedChunk]:
    fused_scores: dict[tuple, float] = {}
    result_by_key: dict[tuple, RetrievedChunk] = {}

    for rank, result in enumerate(vector_results, start=1):
        key = _chunk_key(result)

        fused_scores[key] = fused_scores.get(key, 0.0) + (
            1.0 / (RRF_K + rank)
        )

        result_by_key[key] = result

    for rank, result in enumerate(lexical_results, start=1):
        key = _chunk_key(result)

        fused_scores[key] = fused_scores.get(key, 0.0) + (
            1.0 / (RRF_K + rank)
        )

        if key not in result_by_key:
            result_by_key[key] = result

    ranked_keys = sorted(
        fused_scores,
        key=lambda key: fused_scores[key],
        reverse=True,
    )

    return [
        result_by_key[key]
        for key in ranked_keys
    ]


def _query_terms(query: str) -> list[str]:
    """
    Extract useful terms for the deterministic reranker.

    Stop words are intentionally removed so that common words such as
    "the", "what", and "how" don't dominate the score.
    """

    stop_words = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "can",
        "do",
        "for",
        "from",
        "how",
        "i",
        "in",
        "is",
        "it",
        "me",
        "of",
        "on",
        "or",
        "should",
        "that",
        "the",
        "this",
        "to",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "with",
        "you",
        "your",
    }

    words = re.findall(r"\b[a-zA-Z0-9]+\b", query.lower())

    return [
        word
        for word in words
        if word not in stop_words and len(word) > 2
    ]


def _lexical_overlap_score(
    query: str,
    content: str,
) -> float:
    """
    Calculate a lightweight lexical overlap score.

    This is intentionally deterministic and local. It is not intended
    to replace an ML cross-encoder; it provides a second signal that
    helps exact topic matches outrank generic semantically related text.
    """

    terms = _query_terms(query)

    if not terms:
        return 0.0

    normalized_content = content.lower()

    matched = sum(
        1
        for term in terms
        if re.search(
            rf"\b{re.escape(term)}\b",
            normalized_content,
        )
    )

    return matched / len(terms)


def _rerank_results(
    query: str,
    results: list[RetrievedChunk],
) -> list[RetrievedChunk]:
    """
    Apply a deterministic reranking pass.

    Semantic similarity remains the primary signal.
    Lexical term overlap provides a secondary signal.

    The existing `similarity` field remains untouched and continues
    to represent the actual vector cosine similarity.
    """

    if not results:
        return []

    max_similarity = max(
        (result.similarity for result in results),
        default=0.0,
    )

    min_similarity = min(
        (result.similarity for result in results),
        default=0.0,
    )

    similarity_range = max_similarity - min_similarity

    scored: list[tuple[float, RetrievedChunk]] = []

    for result in results:
        if similarity_range > 0:
            normalized_semantic = (
                (result.similarity - min_similarity)
                / similarity_range
            )
        else:
            normalized_semantic = 1.0

        lexical_score = _lexical_overlap_score(
            query=query,
            content=result.content,
        )

        final_score = (
            SEMANTIC_WEIGHT * normalized_semantic
            + LEXICAL_WEIGHT * lexical_score
        )

        scored.append(
            (final_score, result)
        )

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return [
        result
        for _, result in scored
    ]


async def retrieve_chunks(
    session: AsyncSession,
    query: str,
    top_k: int = DEFAULT_TOP_K,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> list[RetrievedChunk]:
    """
    Hybrid transcript retrieval pipeline:

        Query
          │
          ├── Vector search
          │
          └── PostgreSQL full-text search
                    │
                    ▼
             Reciprocal Rank Fusion
                    │
                    ▼
               Deterministic
                 reranking
                    │
                    ▼
              Deduplication
                    │
                    ▼
             Episode diversification
                    │
                    ▼
                  Top K
    """

    if not query.strip():
        return []

    if top_k <= 0:
        return []

    query_embedding = embed_texts([query])[0]

    candidate_limit = max(
        top_k * VECTOR_CANDIDATE_MULTIPLIER,
        MIN_CANDIDATES,
    )

    vector_results = await _vector_search(
        session=session,
        query_embedding=query_embedding,
        candidate_limit=candidate_limit,
        similarity_threshold=similarity_threshold,
    )

    lexical_results = await _lexical_search(
        session=session,
        query=query,
        candidate_limit=candidate_limit,
    )

    fused_results = _reciprocal_rank_fusion(
        vector_results=vector_results,
        lexical_results=lexical_results,
    )

    reranked_results = _rerank_results(
        query=query,
        results=fused_results,
    )

    return _diversify_results(
        results=reranked_results,
        top_k=top_k,
    )