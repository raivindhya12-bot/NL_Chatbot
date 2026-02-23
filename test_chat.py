import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from phase3_query.rag_pipeline import RAGPipeline

def main():
    print("\n" + "="*60)
    print("🚀 NextLeap RAG Chatbot - Interactive Test Mode")
    print("Type 'exit' or 'quit' to end the session.")
    print("="*60)

    try:
        pipeline = RAGPipeline()
    except Exception as e:
        print(f"❌ Error initializing pipeline: {e}")
        return

    while True:
        try:
            query = input("\n👤 You: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Goodbye!")
                break

            print("🤖 Thinking...")
            result = pipeline.generate_response(query)
            
            print("\n" + "-"*60)
            print(f"🤖 Bot: {result['response']}")
            
            if result.get('sources'):
                print("\n📚 Sources:")
                for source in result['sources']:
                    print(f"  - {source['title']} ({source['url']})")
            print("-"*60)

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
