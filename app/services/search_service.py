from ddgs import DDGS


def search_web(query: str, max_results: int = 3) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(
                query,
                max_results=max_results
            ))

        if not results:
            return None

        context = "WEB SEARCH RESULTS:\n\n"
        for r in results:
            context += f"Title: {r['title']}\n"
            context += f"Content: {r['body']}\n"
            context += f"Source: {r['href']}\n\n"

        return context

    except Exception as e:
        print(f"Search error: {e}")
        return None


def needs_web_search(message: str) -> bool:
    search_keywords = [
        'current', 'latest', 'now', 'today',
        'recent', 'new', 'update', 'who is',
        'price', 'news', '2024', '2025', '2026',
        'right now', 'at the moment', 'presently',
        'what happened', 'when did', 'weather',
        'stock', 'rate', 'score', 'result',
        'election', 'president', 'prime minister',
        'pm', 'minister', 'government', 'policy',
        'এখন', 'বর্তমান', 'আজ', 'সর্বশেষ',
        'নতুন', 'খবর', 'সাম্প্রতিক', 'কে',
        'দাম', 'মূল্য', 'ফলাফল', 'নির্বাচন',
        'প্রধানমন্ত্রী', 'সরকার', 'মন্ত্রী',
    ]
    message_lower = message.lower()
    return any(k in message_lower for k in search_keywords)
