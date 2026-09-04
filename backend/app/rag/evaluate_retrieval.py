import asyncio

from app.db.session import AsyncSessionLocal
from app.rag.retriever import retrieve_chunks


TEST_CASES = [
    {
        "query": "How should a product manager develop product strategy?",
        "expected_terms": [
            "product strategy",
            "strategy",
            "product manager",
        ],
        "should_retrieve": True,
    },
    {
        "query": "What is a good framework for product strategy and prioritization?",
        "expected_terms": [
            "product strategy",
            "prioritization",
            "framework",
        ],
        "should_retrieve": True,
    },
    {
        "query": "How should product teams decide what to build?",
        "expected_terms": [
            "product",
            "build",
            "decisions",
        ],
        "should_retrieve": True,
    },
    {
        "query": "How can product managers become more strategic?",
        "expected_terms": [
            "product",
            "strategic",
            "strategy",
        ],
        "should_retrieve": True,
    },
    {
        "query": "How should a company build and organize a growth team?",
        "expected_terms": [
            "growth",
            "team",
            "organizing",
        ],
        "should_retrieve": True,
    },
    {
        "query": "What are important principles for building AI products?",
        "expected_terms": [
            "AI",
            "product",
            "building",
        ],
        "should_retrieve": True,
    },
    {
        "query": "What is the best way to bake a chocolate cake on Mars?",
        "expected_terms": [
            "chocolate",
            "cake",
            "Mars",
        ],
        "should_retrieve": False,
    },
]


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def has_expected_term(results, expected_terms):
    combined_content = normalize(
        " ".join(result.content for result in results)
    )

    return any(
        normalize(term) in combined_content
        for term in expected_terms
    )


def calculate_mrr(results, expected_terms):
    for rank, result in enumerate(results, start=1):
        content = normalize(result.content)

        if any(
            normalize(term) in content
            for term in expected_terms
        ):
            return 1 / rank

    return 0.0


def count_duplicate_episodes(results):
    episode_keys = [
        (
            normalize(result.episode_title),
            normalize(result.guest_name or ""),
        )
        for result in results
    ]

    return len(episode_keys) - len(set(episode_keys))


async def evaluate_case(case):
    async with AsyncSessionLocal() as session:
        results = await retrieve_chunks(
            session=session,
            query=case["query"],
            top_k=5,
            similarity_threshold=0.55,
        )

    relevant = has_expected_term(
        results,
        case["expected_terms"],
    )

    mrr = calculate_mrr(
        results,
        case["expected_terms"],
    )

    duplicate_count = count_duplicate_episodes(results)

    if case["should_retrieve"]:
        passed = relevant
    else:
        passed = len(results) == 0

    print("=" * 100)
    print(f"QUERY: {case['query']}")
    print("=" * 100)

    print(f"Expected retrieval: {'YES' if case['should_retrieve'] else 'NO'}")
    print(f"Results returned:   {len(results)}")
    print(f"Relevant found:     {'YES' if relevant else 'NO'}")
    print(f"MRR@5:              {mrr:.4f}")
    print(f"Duplicate episodes: {duplicate_count}")
    print(f"PASS:               {'YES' if passed else 'NO'}")
    print()

    for rank, result in enumerate(results, start=1):
        preview = " ".join(result.content.split())

        if len(preview) > 220:
            preview = preview[:220] + "..."

        print(
            f"{rank}. "
            f"{result.episode_title} | "
            f"{result.guest_name or 'Unknown'} | "
            f"{result.timestamp or 'No timestamp'} | "
            f"similarity={result.similarity:.4f}"
        )
        print(f"   {preview}")

    print()

    return {
        "passed": passed,
        "relevant": relevant,
        "mrr": mrr,
        "duplicate_count": duplicate_count,
    }


async def main():
    print("=" * 100)
    print("RETRIEVAL BENCHMARK")
    print("=" * 100)
    print(f"Test cases: {len(TEST_CASES)}")
    print()

    results = []

    for case in TEST_CASES:
        result = await evaluate_case(case)
        results.append(result)

    retrieval_cases = [
        result
        for case, result in zip(TEST_CASES, results)
        if case["should_retrieve"]
    ]

    unsupported_cases = [
        result
        for case, result in zip(TEST_CASES, results)
        if not case["should_retrieve"]
    ]

    retrieval_pass_rate = (
        sum(result["relevant"] for result in retrieval_cases)
        / len(retrieval_cases)
        if retrieval_cases
        else 0
    )

    unsupported_pass_rate = (
        sum(result["passed"] for result in unsupported_cases)
        / len(unsupported_cases)
        if unsupported_cases
        else 0
    )

    average_mrr = (
        sum(result["mrr"] for result in retrieval_cases)
        / len(retrieval_cases)
        if retrieval_cases
        else 0
    )

    total_duplicates = sum(
        result["duplicate_count"]
        for result in results
    )

    print("=" * 100)
    print("BENCHMARK SUMMARY")
    print("=" * 100)

    print(
        f"Retrieval Recall@5:      "
        f"{retrieval_pass_rate:.2%}"
    )

    print(
        f"Unsupported Query Pass:  "
        f"{unsupported_pass_rate:.2%}"
    )

    print(
        f"Average MRR@5:           "
        f"{average_mrr:.4f}"
    )

    print(
        f"Duplicate Results:       "
        f"{total_duplicates}"
    )

    print()

    all_passed = all(result["passed"] for result in results)

    print(
        f"OVERALL: "
        f"{'PASS' if all_passed else 'NEEDS IMPROVEMENT'}"
    )


if __name__ == "__main__":
    asyncio.run(main())