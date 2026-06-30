"""Quick smoke test for LLM API connectivity. Run: python -m backend.test_llm_connection"""

import asyncio
import sys

from backend.categorizer.llm_client import call_llm


async def main():
    prompt = 'Return ONLY this JSON: {"sector": "Health", "size": "Micro"}'
    print("Calling LLM API...")
    result = await call_llm(prompt, max_retries=1, timeout=15.0)
    if result:
        print(f"OK — Response:\n{result}")
    else:
        print("FAIL — Empty response. Check LLM_API_KEY and LLM_API_URL in .env")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
