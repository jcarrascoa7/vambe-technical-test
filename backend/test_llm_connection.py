"""Quick smoke test for Gemma API connectivity. Run: python -m backend.test_llm_connection"""

import asyncio
import sys

from backend.categorizer.gemma_client import call_gemma


async def main():
    prompt = 'Return ONLY this JSON: {"sector": "Health", "size": "Micro"}'
    print("Calling Gemma API...")
    result = await call_gemma(prompt, max_retries=1, timeout=15.0)
    if result:
        print(f"OK — Response:\n{result}")
    else:
        print("FAIL — Empty response. Check GEMMA_API_KEY and GEMMA_API_URL in .env")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
