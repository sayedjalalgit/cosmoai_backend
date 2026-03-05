import time
from groq import Groq
from app.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)


def get_language_instruction(language: str) -> str:
    if language == "bn":
        return "Always respond in Bangla (Bengali). Use Bangla script only."
    elif language == "en":
        return "Always respond in English."
    return "Detect the language of the user message and respond in the same language. If Bangla respond in Bangla. If English respond in English."


def chat_with_groq(
    messages: list,
    language: str = "auto",
    document_context: str = None,
    current_query: str = None
) -> tuple[str, float, int]:
    start_time = time.time()
    lang_instruction = get_language_instruction(language)

    # Use current_query for web search detection
    query_to_check = current_query or ""
    if not query_to_check and messages:
        for m in reversed(messages):
            if m["role"] == "user":
                query_to_check = m["content"]
                break

    print(f"Query: {query_to_check}")

    # Search web if needed
    web_context = None
    try:
        from app.services.search_service import search_web, needs_web_search
        if query_to_check and needs_web_search(query_to_check):
            print(f"Web search triggered!")
            web_context = search_web(query_to_check)
            if web_context:
                print("Web search successful")
            else:
                print("Web search returned nothing")
        else:
            print("Web search not needed")
    except Exception as e:
        print(f"Search error: {e}")

    # Build context
    context_parts = []
    if document_context:
        context_parts.append(f"FROM USER DOCUMENTS:\n{document_context}")
    if web_context:
        context_parts.append(f"FROM WEB SEARCH (current live information):\n{web_context}")

    full_context = "\n\n".join(context_parts) if context_parts else None

    # Build system prompt
    if full_context:
        system_prompt = f"""You are COSMOAI, an intelligent private AI assistant.

{lang_instruction}

You have web search results below AND your own training knowledge. Use BOTH together.

{full_context}

CRITICAL RULES:
- For WEB SEARCH results: combine with training knowledge for complete answers
- For DOCUMENT results: ONLY use what is explicitly written in the document
- NEVER invent numbers, names, dates, or facts from documents
- NEVER confuse different people mentioned in the same document
- If document does not contain the answer say: This information is not found in the provided documents
- For web search: if info is missing use training knowledge to complete
- Always quote exact text when answering from documents
- Be direct, clear and professional"""

    else:
        system_prompt = f"""You are COSMOAI, an intelligent private AI assistant built for Bangladesh and the world.

{lang_instruction}

Guidelines:
- Be clear and well structured
- Use bullet points when listing items
- Give complete and detailed answers
- Use your full training knowledge confidently
- For historical questions give complete lists and details
- Always be respectful and professional"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            *messages
        ],
        temperature=0.7,
        max_tokens=2048,
    )

    response_time = time.time() - start_time
    content = response.choices[0].message.content
    tokens = response.usage.total_tokens

    return content, response_time, tokens
