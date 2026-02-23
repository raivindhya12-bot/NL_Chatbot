import streamlit as st
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Optional: Load local .env if it exists (for local testing)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from phase3_query.rag_pipeline import RAGPipeline

# Page Config
st.set_page_config(
    page_title="NextLeap Chatbot",
    page_icon="🤖",
    layout="centered"
)

# Custom Styling
st.markdown("""
<style>
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .main {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# App Title
st.title("🤖 NextLeap RAG Chatbot")
st.markdown("Ask anything about NextLeap's courses, fellowships, and mentorship programs.")

# Handle Secrets for Groq API
if 'GROQ_API_KEY' not in os.environ:
    if 'GROQ_API_KEY' in st.secrets:
        os.environ['GROQ_API_KEY'] = st.secrets['GROQ_API_KEY']
    else:
        st.error("Please set the GROQ_API_KEY in Streamlit Secrets or environment variables.")
        st.stop()

# Initialize Pipeline
@st.cache_resource
def get_pipeline():
    return RAGPipeline()

pipeline = get_pipeline()

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("📚 View Sources"):
                for src in message["sources"]:
                    st.markdown(f"- **{src['title']}** ([Link]({src['url']}))")

# Chat Input
if prompt := st.chat_input("How can I help you today?"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("🤖 Thinking..."):
            result = pipeline.generate_response(prompt)
            response = result['response']
            sources = result.get('sources', [])
            
            st.markdown(response)
            
            # Show sources if available and not the "Sorry" response
            if sources and "Sorry, I can't help you with that" not in response:
                with st.expander("📚 View Sources"):
                    for src in sources:
                        st.markdown(f"- **{src['title']}** ([Link]({src['url']}))")
            
            # Add assistant message to history
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response,
                "sources": sources if "Sorry" not in response else []
            })
