import asyncio

from app.db.session import AsyncSessionLocal
from app.rag.retriever import retrieve_chunks


async def main() -> None:
    query = "practical product strategy principles for product managers"

    async with AsyncSessionLocal() as session:
        results = await retrieve_chunks(
            session=session,
            query=query,
            top_k=5,
            similarity_threshold=0.55,
        )

    print("=" * 80)
    print("HYBRID RETRIEVAL CHECK")
    print("=" * 80)
    print(f"Query: {query}")
    print(f"Results: {len(results)}")
    print()

    if not results:
        print("No results retrieved.")
        return

    for index, result in enumerate(results, start=1):
        print("=" * 80)
        print(f"RESULT {index}")
        print("=" * 80)
        print(f"ID: {result.id}")
        print(f"Episode: {result.episode_title}")
        print(f"Guest: {result.guest_name}")
        print(f"Date: {result.episode_date}")
        print(f"Timestamp: {result.timestamp}")
        print(f"Similarity: {result.similarity:.4f}")
        print(f"Source: {result.source_path}")
        print(f"YouTube URL: {result.youtube_url}")
        print()
        print("CONTENT")
        print("-" * 80)
        print(result.content)
        print()


if __name__ == "__main__":
    asyncio.run(main())