"""Translation module — English to Chinese.

Multi-backend fallback chain:
1. googletrans   (fastest, works outside GFW, supports batch)
2. MyMemory API  (free, works inside GFW, chunked to fit 500-char limit)
3. Empty strings (degraded but functional)
"""

import asyncio
from typing import Optional

import aiohttp

MYMEMORY_URL = "https://api.mymemory.translated.net/get"

GOOGLETRANS_TIMEOUT = 15
MYMEMORY_TIMEOUT = 15
MYMEMORY_MAX_CHARS = 500


async def _translate_googletrans(texts: list[str]) -> Optional[list[str]]:
    """Try googletrans with batch translation."""
    try:
        from googletrans import Translator as GTranslator

        translator = GTranslator()
        loop = asyncio.get_event_loop()

        try:
            results = await asyncio.wait_for(
                loop.run_in_executor(
                    None, lambda: translator.translate(texts, src="en", dest="zh-cn")
                ),
                timeout=GOOGLETRANS_TIMEOUT,
            )
            translated = [r.text for r in results]
            if translated and any(r.strip() for r in translated):
                return translated
        except Exception:
            pass

        return None
    except Exception:
        return None


def _chunk_texts(texts: list[str], max_chars: int) -> list[tuple[int, list[str]]]:
    """Split texts into chunks respecting max_chars total per chunk.

    Returns list of (start_index, chunk_texts) tuples so results
    can be reassembled in order.
    """
    chunks: list[tuple[int, list[str]]] = []
    i = 0
    while i < len(texts):
        chunk: list[str] = []
        char_count = 0
        start = i
        while i < len(texts):
            t = texts[i]
            if char_count + len(t) + (1 if chunk else 0) > max_chars:
                if chunk:
                    break
            chunk.append(t)
            char_count += len(t) + (1 if len(chunk) > 1 else 0)
            i += 1
        chunks.append((start, chunk))
    return chunks


async def _translate_mymemory(texts: list[str]) -> Optional[list[str]]:
    """Fallback: MyMemory API with chunked batch requests.

    Splits texts into chunks that fit within MyMemory's 500-char
    query limit, sends one request per chunk.
    """
    if not texts:
        return []

    try:
        async with aiohttp.ClientSession() as session:
            chunks = _chunk_texts(texts, MYMEMORY_MAX_CHARS)
            results: list[tuple[int, str]] = []

            for start, chunk in chunks:
                batch_query = "\n".join(chunk)
                params = {"q": batch_query, "langpair": "en|zh-CN"}

                async with session.get(
                    MYMEMORY_URL, params=params,
                    timeout=aiohttp.ClientTimeout(total=MYMEMORY_TIMEOUT)
                ) as resp:
                    if resp.status != 200:
                        for j, _ in enumerate(chunk):
                            results.append((start + j, ""))
                        continue

                    data = await resp.json()
                    translated = data.get("responseData", {}).get("translatedText", "")

                if translated and "QUERY LENGTH LIMIT" not in translated:
                    lines = translated.split("\n")
                    for j in range(len(chunk)):
                        text = lines[j].strip() if j < len(lines) else ""
                        results.append((start + j, text))
                else:
                    for j in range(len(chunk)):
                        results.append((start + j, ""))

        results.sort(key=lambda x: x[0])
        translated = [r[1] for r in results]

        if translated and any(r.strip() for r in translated):
            return translated
        return None
    except Exception:
        return None


async def translate_batch(texts: list[str]) -> list[str]:
    """Translate English sentences to Chinese.

    Tries multiple backends in order:
      1. googletrans (batched)
      2. MyMemory API (chunked to stay under 500 chars)
      3. Empty strings (last resort)

    Returns a list parallel to *texts*.
    """
    if not texts:
        return []

    result = await _translate_googletrans(texts)
    if result is not None:
        return result

    result = await _translate_mymemory(texts)
    if result is not None:
        return result

    return [""] * len(texts)
