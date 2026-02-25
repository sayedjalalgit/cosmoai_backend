import sys
sys.path.append('.')

from app.services.search_service import search_web, needs_web_search

print("Testing web search...")
print()

# Test needs_search detection
tests = [
    "Who is the PM of Bangladesh?",
    "What is 2+2?",
    "Latest news today",
    "বর্তমান প্রধানমন্ত্রী কে?",
    "Tell me about history",
]

print("Search detection test:")
for t in tests:
    result = needs_web_search(t)
    print(f"  '{t[:40]}' → Search: {result}")

print()
print("Live search test...")
result = search_web("Prime Minister of Bangladesh 2025")
if result:
    print("✅ Search working!")
    print(result[:400])
else:
    print("❌ Search failed")

