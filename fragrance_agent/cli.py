"""
Epicure-Fragrance CLI
======================
Command-line interface for the fragrance expert agent.

Usage:
    python cli.py                          # Interactive mode
    python cli.py --query "What pairs with oud?"
    python cli.py --scrape-tgsc            # Run TGSC scraper
    python cli.py --scrape-fragrantica     # Run Fragrantica scraper
    python cli.py --process                # Run data processing pipeline
    python cli.py --capabilities           # Show agent capabilities
"""

import sys
import json
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import AGENT_NAME


def interactive_mode(agent):
    """Run the agent in interactive REPL mode."""
    print(f"\n{'='*60}")
    print(f"  {AGENT_NAME} — World-Expert Fragrance Agent")
    print(f"  Type your question or 'help' for capabilities, 'quit' to exit")
    print(f"{'='*60}\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\nGoodbye from {AGENT_NAME}!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print(f"Goodbye from {AGENT_NAME}!")
            break

        if user_input.lower() in ("help", "capabilities", "?"):
            print(agent.get_capabilities_summary())
            continue

        if user_input.lower() == "reset":
            agent.reset_conversation()
            print("Conversation reset.\n")
            continue

        # Process query through the agent
        result = agent.query(user_input)

        # Display retrieved context
        if result["context"]:
            print(f"\n--- Retrieved Context ---")
            print(result["context"][:2000])  # Show first 2000 chars
            if len(result["context"]) > 2000:
                print(f"... ({len(result['context'])} total chars)")
            print(f"--- End Context ---\n")

        # Display search results summary
        raw = result["raw_results"]
        print(f"Search results: "
              f"{len(raw.get('notes', []))} notes, "
              f"{len(raw.get('molecules', []))} molecules, "
              f"{len(raw.get('perfumes', []))} perfumes, "
              f"{len(raw.get('accords', []))} accords, "
              f"{len(raw.get('perfumers', []))} perfumers")

        # The full prompt is available for an external LLM call
        print(f"\nFull prompt generated ({len(result['prompt'])} chars) — ready for LLM")

        # In a real deployment, you would send the prompt to your LLM here
        # For now, display what the agent would send
        print(f"\nPrompt preview (first 1000 chars):")
        print(result["prompt"][:1000])
        if len(result["prompt"]) > 1000:
            print("...")


def main():
    parser = argparse.ArgumentParser(description=f"{AGENT_NAME} — Fragrance Expert Agent CLI")
    parser.add_argument("--query", "-q", type=str, default=None,
                        help="Single query to process (non-interactive)")
    parser.add_argument("--capabilities", action="store_true",
                        help="Show agent capabilities")
    parser.add_argument("--scrape-tgsc", action="store_true",
                        help="Run TGSC scraper")
    parser.add_argument("--scrape-fragrantica", action="store_true",
                        help="Run Fragrantica scraper")
    parser.add_argument("--scrape-basenotes", action="store_true",
                        help="Run Basenotes scraper")
    parser.add_argument("--process", action="store_true",
                        help="Run data processing pipeline")
    parser.add_argument("--build-kb", action="store_true",
                        help="Build the full knowledge base from processed data")
    parser.add_argument("--export-system-prompt", type=str, default=None,
                        help="Export the system prompt to a file")
    parser.add_argument("--json-output", action="store_true",
                        help="Output results as JSON")
    args = parser.parse_args()

    if args.scrape_tgsc:
        from scrapers.tgsc_scraper import TGSCScraper, save_odor_types
        scraper = TGSCScraper()
        odor_types = scraper.scrape_odor_type_list()
        from config import TGSC_ODOR_TYPES_FILE
        save_odor_types(odor_types, TGSC_ODOR_TYPES_FILE)
        print(f"Scraped {len(odor_types)} odor types. Run with --scrape-tgsc --scrape-molecules for full data.")
        return

    if args.scrape_fragrantica:
        from scrapers.fragrantica_scraper import FragranticaScraper
        scraper = FragranticaScraper()
        notes = scraper.scrape_notes_directory()
        from scrapers.fragrantica_scraper import save_notes
        from config import FRAGNANTICA_NOTES_FILE
        save_notes(notes, FRAGNANTICA_NOTES_FILE)
        print(f"Scraped {len(notes)} fragrance notes.")
        return

    if args.scrape_basenotes:
        print("Basenotes scraper — run with specific search terms for targeted scraping.")
        print("Example: python -m scrapers.basenotes_scraper --max-pages 5")
        return

    if args.process:
        from data_processor.processor import run_pipeline
        run_pipeline()
        print("Data processing pipeline complete.")
        return

    if args.build_kb:
        from knowledge.knowledge_base import FragranceKnowledgeBase
        kb = FragranceKnowledgeBase()
        kb.load()
        print(f"Knowledge base built: {len(kb.molecules)} molecules, "
              f"{len(kb.notes)} notes, {len(kb.perfumes)} perfumes")
        return

    # Load the agent
    from agent.expert_agent import FragranceExpertAgent
    agent = FragranceExpertAgent()

    if args.export_system_prompt:
        with open(args.export_system_prompt, "w", encoding="utf-8") as f:
            f.write(agent.get_system_prompt())
        print(f"System prompt exported to {args.export_system_prompt}")
        return

    if args.capabilities:
        print(agent.get_capabilities_summary())
        return

    if args.query:
        result = agent.query(args.query)
        if args.json_output:
            # JSON output for programmatic use
            output = {
                "query": args.query,
                "context": result["context"],
                "raw_results": result["raw_results"],
            }
            print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
        else:
            print(f"\n=== {AGENT_NAME} Response ===\n")
            print(f"Context retrieved: {len(result['context'])} chars")
            print(f"Search hits: {sum(len(v) if isinstance(v, list) else len(v) if isinstance(v, dict) else 0 for v in result['raw_results'].values())}")
            print(f"\nFull prompt ({len(result['prompt'])} chars) ready for LLM")
        return

    # Interactive mode
    interactive_mode(agent)


if __name__ == "__main__":
    main()
