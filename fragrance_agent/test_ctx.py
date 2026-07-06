import sys
sys.path.insert(0, ".")
from knowledge.knowledge_base import FragranceKnowledgeBase
kb = FragranceKnowledgeBase()
kb.load()
try:
    ctx = kb.get_context_for_agent("floral", max_tokens=4000)
    print(f"Context length: {len(ctx)}")
    print(ctx[:2000])
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
