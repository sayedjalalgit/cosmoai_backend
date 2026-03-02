from ddgs import DDGS


def search_web(query: str, max_results: int = 5) -> str:
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(
                query + " 2025 2026",
                max_results=max_results
            ):
                results.append(r)

        if not results:
            return None

        context = "CURRENT WEB SEARCH RESULTS:\n\n"
        for i, r in enumerate(results):
            context += f"Result {i+1}:\n"
            context += f"Title: {r.get('title', '')}\n"
            context += f"Content: {r.get('body', '')}\n"
            context += f"Source: {r.get('href', '')}\n\n"

        return context

    except Exception as e:
        print(f"Search error: {e}")
        return None


def needs_web_search(message: str) -> bool:
    search_keywords = [
        # English keywords
        'current', 'latest', 'now', 'today',
        'recent', 'new', 'update', 'who is',
        'price', 'news', '2024', '2025', '2026',
        'right now', 'at the moment', 'presently',
        'what happened', 'when did', 'weather',
        'stock', 'rate', 'score', 'result',
        'election', 'president', 'prime minister',
        'pm', 'minister', 'government', 'policy',
        'list of', 'who are', 'names of',
        'leaders', 'head of', 'ruling',
        # Bangla keywords
        'এখন', 'বর্তমান', 'আজ', 'সর্বশেষ',
        'নতুন', 'খবর', 'সাম্প্রতিক', 'কে',
        'দাম', 'মূল্য', 'ফলাফল', 'নির্বাচন',
        'প্রধানমন্ত্রী', 'সরকার', 'মন্ত্রী',
        'তালিকা', 'নেতা',
    ]
    message_lower = message.lower()
    return any(k in message_lower for k in search_keywords)
