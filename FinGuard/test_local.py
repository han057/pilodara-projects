# test_local.py
# Interactive console for testing the FinGuard multi-agent system locally.
# Run with: python test_local.py

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.graph import graph


def run_console():
    print("=" * 60)
    print("🤖  FINGUARD — MULTI-AGENT FINANCIAL RISK ANALYSIS")
    print("    Powered by LangGraph · Type 'exit' to quit")
    print("=" * 60)
    print()
    print("Example queries:")
    print("  · Analyze Tesla bankruptcy risk")
    print("  · Compare Tesla and Apple risk")
    print("  · Is Nvidia a safe investment?")
    print("  · Tell me about the iPhone company financial health")
    print()

    while True:
        print("─" * 60)
        query = input("👉  Your query: ").strip()

        if query.lower() in ["exit", "quit", "q"]:
            print("\n👋  Goodbye. Good luck with the presentation!")
            break

        if not query:
            print("⚠️   Please enter a valid query.")
            continue

        inputs      = {"query": query}
        final_state = {}

        print()
        print("⚙️   Running agent pipeline...")
        print()

        try:
            for output in graph.stream(inputs):
                for key, value in output.items():
                    print(f"    [{key.upper()}] completed.")
                    final_state.update(value)

            print()
            print("=" * 60)

            if "final_report" in final_state:
                print(final_state["final_report"])
            else:
                print("⚠️   Pipeline finished but no report was generated.")

            print("=" * 60)

        except Exception as e:
            print(f"\n❌  Pipeline error: {e}")
            print("    Check that Ollama is running and models are available.")


if __name__ == "__main__":
    run_console()
