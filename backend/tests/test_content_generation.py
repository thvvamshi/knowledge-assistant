import asyncio

from sqlalchemy import select

from app.agents.assistant_agent import AssistantAgent
from app.db.session import AsyncSessionLocal
from app.rag.context import build_rag_context
from app.rag.retriever import retrieve_chunks


async def main():
    question = (
        "Write a long-form article about practical product strategy "
        "principles for product managers."
    )

    async with AsyncSessionLocal() as db:
        results = await retrieve_chunks(
            db,
            question,
            top_k=5,
            similarity_threshold=0.55,
        )

        if not results:
            print("No knowledge-base results were retrieved.")
            return

        print("\nRetrieved sources:")
        for index, result in enumerate(results, start=1):
            print(
                f"{index}. {result.episode_title} "
                f"| {result.guest_name} "
                f"| {result.timestamp} "
                f"| similarity={result.similarity:.4f}"
            )

        rag_context = build_rag_context(results)

        agent = AssistantAgent(provider_name="ollama")

        response = await agent.generate(
            question=question,
            rag_context=rag_context,
            history="No previous conversation.",
        )

        print("\nProvider:", response.provider)
        print("Model:", response.model)
        print("\n" + "=" * 80)
        print("GENERATED ARTICLE")
        print("=" * 80)
        print(response.content)


if __name__ == "__main__":
    asyncio.run(main())