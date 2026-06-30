"""Manual test: categorize first N transcriptions and verify DB persistence."""

import asyncio
import sys

from backend.categorizer.gemma_client import call_gemma
from backend.categorizer.prompts import build_categorization_prompt
from backend.categorizer.validator import validate_response
from backend.database import SessionLocal
from backend.models import Client


async def categorize_one(transcription: str) -> dict | None:
    prompt = build_categorization_prompt(transcription)
    raw = await call_gemma(prompt)
    if not raw:
        return None
    return validate_response(raw)


async def main(n: int = 20):
    db = SessionLocal()
    try:
        records = (
            db.query(Client)
            .filter(
                Client.categorized == False, Client.transcription.isnot(None)
            )  # noqa: E712
            .order_by(Client.id)
            .limit(n)
            .all()
        )
        print(f"Found {len(records)} uncategorized records\n")

        success = 0
        fail = 0
        for i, record in enumerate(records, 1):
            print(f"[{i}/{n}] Client {record.id}: {record.name}")
            result = await categorize_one(record.transcription or "")
            if result:
                for dim, value in result.items():
                    setattr(record, dim, value)
                record.categorized = True
                success += 1
                print(
                    f"  sector={result['sector']} size={result['size']} "
                    f"volume={result['inquiry_volume']} channel={result['channel']} "
                    f"source={result['source']} pain={result['pain']}"
                )
            else:
                fail += 1
                print("  FAILED - will retry on next run")

            await asyncio.sleep(4)  # rate limit: 15 req/min

        db.commit()
        print(f"\nDone: {success} categorized, {fail} failed")

        # Verify persistence
        print("\n--- Verifying DB persistence ---")
        ids = [r.id for r in records]
        saved = db.query(Client).filter(Client.id.in_(ids)).all()
        categorized_count = sum(1 for c in saved if c.categorized)
        print(f"Records in DB: {len(saved)}, categorized={categorized_count}")

        print("\n--- Sample results from DB ---")
        for c in saved[:5]:
            print(
                f"  {c.id}: {c.name} | sector={c.sector} size={c.size} "
                f"channel={c.channel} pain={c.pain} concreteness={c.concreteness}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    asyncio.run(main(n))
