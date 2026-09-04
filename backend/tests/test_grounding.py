import asyncio

from app.db.session import AsyncSessionLocal
from app.services.assistant_service import answer_question


async def main():
    question = "What is the history of the Roman Empire?"

    async with AsyncSessionLocal() as session:
        result = await answer_question(
            session=session,
            question=question,
        )

    print("=" * 80)
    print("ANSWER")
    print("=" * 80)
    print(result.answer)

    print()
    print("=" * 80)
    print("SOURCES")
    print("=" * 80)

    for source in result.sources:
        print(source)


if __name__ == "__main__":
    asyncio.run(main())
