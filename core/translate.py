"""Translation module — English to Chinese.

Multi-backend fallback chain:
1. translators (youdao — works in China, no API key required)
2. translators (bing   — works outside GFW)
3. translators (alibaba — additional fallback)
4. Empty strings (degraded but functional)
"""

import asyncio
from typing import Optional

TRANSLATE_TIMEOUT = 20


async def _translate_via(backend: str, texts: list[str]) -> Optional[list[str]]:
    """Translate via a specific translators backend."""
    if not texts:
        return []
    try:
        import translators as ts

        batch = "\n".join(texts)
        result = await asyncio.wait_for(
            asyncio.to_thread(
                ts.translate_text, batch,
                translator=backend,
                from_lang="en",
                to_lang="zh",
            ),
            timeout=TRANSLATE_TIMEOUT,
        )
        if not result or not result.strip():
            return None

        lines = result.split("\n")
        translated = [lines[i].strip() if i < len(lines) else "" for i in range(len(texts))]
        if any(r.strip() for r in translated):
            return translated
        return None
    except Exception:
        return None


async def translate_batch(texts: list[str]) -> list[str]:
    """Translate English sentences to Chinese.

    Tries multiple backends in order:
      1. youdao (works in China, no API key)
      2. bing   (works outside GFW)
      3. alibaba (extra fallback)
      4. Empty strings (last resort)

    Returns a list parallel to *texts*.
    """
    if not texts:
        return []

    for backend in ("youdao", "bing", "alibaba"):
        result = await _translate_via(backend, texts)
        if result is not None:
            return result

    return [""] * len(texts)
