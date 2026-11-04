import re


_ENGLISH_WEB_PATTERNS = (
    r"\b(search|browse|look\s+up|find\s+online|web\s+search|internet|research|investigate)\b",
    r"\b(latest|newest|recent|today|yesterday|this\s+week|past\s+week|last\s+week)\b",
    r"\b(news|headlines|current\s+(?:events|facts|price|prices|schedule))\b",
)
_PERSIAN_WEB_PATTERNS = (
    r"(جست.?وجو|جستجو|بگرد|پیدا\s*کن|تحقیق|در\s*وب|در\s*اینترنت|وب\s*گردی)",
    r"(آخرین|جدیدترین|به.?روز|امروز|دیروز|هفته\s*اخیر|هفته\s*گذشته|روزهای\s*اخیر)",
    r"(خبر|اخبار|قیمت|نرخ|وضعیت\s*فعلی|رویدادهای\s*جاری)",
)


def message_text(content):
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = []
    for item in content:
        if isinstance(item, str):
            parts.append(item)
        elif isinstance(item, dict):
            value = item.get("text")
            if isinstance(value, str):
                parts.append(value)
    return " ".join(parts)


def is_web_research_request(text):
    if not isinstance(text, str) or not text.strip():
        return False
    normalized = text.replace("ي", "ی").replace("ك", "ک").lower()
    return any(
        re.search(pattern, normalized, flags=re.IGNORECASE)
        for pattern in (*_ENGLISH_WEB_PATTERNS, *_PERSIAN_WEB_PATTERNS)
    )
