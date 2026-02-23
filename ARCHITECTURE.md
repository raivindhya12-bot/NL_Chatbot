# RAG Chatbot Architecture for NextLeap.app

## Overview
This document outlines the architecture for building a Retrieval-Augmented Generation (RAG) chatbot for nextleap.app. The system will scrape content from the website, convert it into embeddings, and provide intelligent responses using Groq LLM.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         RAG Chatbot System                      │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   Phase 1     │    │   Phase 2     │    │   Phase 3     │
│ Data Scraping │───▶│  Embeddings   │───▶│   Query &     │
│ & Preprocess  │    │   & Storage   │    │   Response    │
└───────────────┘    └───────────────┘    └───────────────┘
```

## Phase 1: Data Scraping & Preprocessing

### Objectives
- Scrape all relevant content from nextleap.app
- Clean and preprocess the scraped data
- Structure data for embedding generation

### Components

#### 1.1 Web Scraper Module
**Technology**: `BeautifulSoup4`, `Selenium` (if needed for JS-rendered content), `requests`

**Responsibilities**:
- Crawl nextleap.app website systematically
- Extract text content from:
  - Blog posts (`/blog/`)
  - Course descriptions
  - Reviews (`/reviews`)
  - Company pages (`/for-companies`)
  - Main page content
- Handle pagination and dynamic content
- Respect robots.txt and rate limiting

**Output**: Raw HTML/text files or structured JSON

#### 1.2 Data Preprocessor Module
**Technology**: `pandas`, `nltk`/`spaCy`, custom text cleaning utilities

**Responsibilities**:
- Clean HTML tags and artifacts
- Remove noise (navigation, footers, headers)
- Text normalization (lowercase, remove special chars)
- Chunk text into manageable segments (500-1000 tokens per chunk)
- Extract metadata (URL, title, date, content type)
- Deduplicate content

**Output**: Clean, chunked text data with metadata

### Data Flow
```
nextleap.app → Scraper → Raw Data → Preprocessor → Clean Chunks → JSON/Parquet
```

### Storage Format
```json
{
  "chunk_id": "unique_id",
  "source_url": "https://nextleap.app/blog/...",
  "title": "Blog Post Title",
  "content": "chunked text content",
  "content_type": "blog|course|review|page",
  "chunk_index": 0,
  "metadata": {
    "date": "2024-01-01",
    "author": "..."
  }
}
```

---

## Phase 2: Embeddings & Vector Storage

### Objectives
- Convert preprocessed text chunks into vector embeddings
- Store embeddings in a vector database
- Enable efficient similarity search

### Components

#### 2.1 Embedding Generator Module
**Technology**: `sentence-transformers` or `OpenAI embeddings` API

**Model Options**:
- `all-MiniLM-L6-v2` (lightweight, fast)
- `all-mpnet-base-v2` (better quality)
- `BAAI/bge-small-en-v1.5` (state-of-the-art)

**Responsibilities**:
- Load embedding model
- Generate embeddings for each text chunk
- Batch processing for efficiency
- Handle errors and retries

**Output**: Vector embeddings (384 or 768 dimensions typically)

#### 2.2 Vector Database Module
**Technology**: `ChromaDB` (recommended) or `FAISS` or `Pinecone` (cloud)

**Why ChromaDB**:
- Lightweight and easy to set up
- Persistent storage
- Built-in similarity search
- Good for local development

**Responsibilities**:
- Initialize vector database
- Store embeddings with metadata
- Create collections for different content types (optional)
- Index embeddings for fast retrieval

**Storage Structure**:
```
Collection: nextleap_content
├── IDs: chunk_ids
├── Embeddings: vector arrays
├── Documents: original text chunks
└── Metadata: source_url, title, content_type, etc.
```

### Data Flow
```
Clean Chunks → Embedding Model → Vectors → Vector DB → Indexed & Searchable
```

### Configuration
- Chunk size: 500-1000 tokens
- Overlap: 50-100 tokens (for context preservation)
- Embedding dimension: 384 or 768
- Similarity metric: Cosine similarity

---

## Phase 3: Query & Response Generation

### Objectives
- Accept user queries
- Retrieve relevant context from vector database
- Generate responses using Groq LLM
- Provide source citations

### Components

#### 3.1 Query Processing Module
**Technology**: Custom query handler

**Responsibilities**:
- Accept user query
- Optional: Query expansion/rewriting
- Generate query embedding
- Perform similarity search in vector DB
- Retrieve top-k relevant chunks (k=3-5)

**Output**: Ranked list of relevant text chunks with similarity scores

#### 3.2 RAG Pipeline Module
**Technology**: `langchain` or custom implementation, `groq` SDK

**Responsibilities**:
- Combine retrieved chunks into context
- Format prompt with:
  - System instructions
  - Retrieved context
  - User query
- Call Groq LLM API
- Handle API errors and rate limits
- Stream responses (optional)

**Groq Models**:
- `llama-3.1-70b-versatile` (recommended)
- `mixtral-8x7b-32768`
- `llama-3.1-8b-instant` (faster, lighter)

#### 3.3 Response Formatter Module
**Technology**: Custom formatting utilities

**Responsibilities**:
- Format LLM response
- Add source citations (links to original content)
- Handle markdown formatting
- Error message formatting

### Data Flow
```
User Query → Query Embedding → Vector Search → Top-k Chunks → 
RAG Prompt → Groq LLM → Formatted Response → User
```

### Prompt Template
```
System: You are a helpful assistant for NextLeap.app. Answer questions based on the provided context.

Context:
{retrieved_chunks}

User Question: {user_query}

Answer:
```

---

## Technical Stack Summary

### Core Technologies
- **Python 3.9+**
- **Web Scraping**: BeautifulSoup4, Selenium (if needed)
- **Text Processing**: pandas, nltk/spaCy
- **Embeddings**: sentence-transformers
- **Vector DB**: ChromaDB
- **LLM**: Groq API (llama-3.1-70b-versatile)
- **Framework**: langchain (optional, for RAG pipeline)

### Project Structure
```
RAG_Chatbot_v1/
├── phase1_scraping/
│   ├── scraper.py
│   ├── preprocessor.py
│   └── config.py
├── phase2_embeddings/
│   ├── embedding_generator.py
│   ├── vector_store.py
│   └── config.py
├── phase3_query/
│   ├── query_processor.py
│   ├── rag_pipeline.py
│   ├── response_formatter.py
│   └── config.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── embeddings/
├── config/
│   ├── scraping_config.yaml
│   ├── embedding_config.yaml
│   └── llm_config.yaml
├── utils/
│   ├── text_utils.py
│   └── db_utils.py
├── requirements.txt
├── ARCHITECTURE.md
└── README.md
```

---

## Phase-wise Implementation Plan

### Phase 1 Implementation Steps
1. ✅ Set up project structure
2. ✅ Install dependencies
3. ✅ Build web scraper for nextleap.app
4. ✅ Implement data preprocessing pipeline
5. ✅ Test scraping on sample pages
6. ✅ Save processed data

### Phase 2 Implementation Steps
1. ✅ Set up embedding model
2. ✅ Generate embeddings for all chunks
3. ✅ Initialize ChromaDB
4. ✅ Store embeddings with metadata
5. ✅ Test similarity search
6. ✅ Validate retrieval quality

### Phase 3 Implementation Steps
1. ✅ Set up Groq API client
2. ✅ Build query processing module
3. ✅ Implement RAG pipeline
4. ✅ Create response formatter
5. ✅ Build simple CLI/API interface
6. ✅ Test end-to-end flow
7. ✅ Add error handling and logging

---

## Configuration Files

### Scraping Config
```yaml
target_urls:
  - https://nextleap.app
  - https://nextleap.app/blog
  - https://nextleap.app/reviews
  - https://nextleap.app/for-companies

scraping:
  delay_seconds: 1
  max_pages: 1000
  respect_robots_txt: true

chunking:
  chunk_size: 1000
  chunk_overlap: 100
```

### Embedding Config
```yaml
model_name: "sentence-transformers/all-MiniLM-L6-v2"
batch_size: 32
device: "cpu"  # or "cuda"

vector_db:
  type: "chromadb"
  persist_directory: "./data/embeddings/chroma_db"
  collection_name: "nextleap_content"
```

### LLM Config
```yaml
provider: "groq"
model: "llama-3.1-70b-versatile"
api_key: "${GROQ_API_KEY}"  # from environment
temperature: 0.7
max_tokens: 1000

retrieval:
  top_k: 5
  similarity_threshold: 0.5
```

---

## Performance Considerations

### Phase 1
- Rate limiting to avoid being blocked
- Parallel scraping (with limits)
- Incremental scraping (resume capability)

### Phase 2
- Batch processing for embeddings
- GPU acceleration if available
- Incremental updates (only new content)

### Phase 3
- Caching frequent queries
- Async API calls for Groq
- Response streaming for better UX
- Timeout handling

---

## Future Enhancements (Post-MVP)

1. **Multi-modal support**: Images, videos
2. **Conversation memory**: Chat history
3. **Fine-tuning**: Domain-specific model fine-tuning
4. **Evaluation metrics**: RAG quality assessment
5. **Web interface**: Streamlit/Gradio UI
6. **API endpoints**: REST/GraphQL API
7. **Monitoring**: Logging, analytics, error tracking
8. **Incremental updates**: Auto-refresh embeddings

---

## Dependencies

```txt
# Web Scraping
beautifulsoup4>=4.12.0
selenium>=4.15.0
requests>=2.31.0
lxml>=4.9.0

# Data Processing
pandas>=2.0.0
numpy>=1.24.0
nltk>=3.8.0

# Embeddings
sentence-transformers>=2.2.0
torch>=2.0.0

# Vector Database
chromadb>=0.4.0

# LLM
groq>=0.4.0
langchain>=0.1.0
langchain-community>=0.0.10

# Utilities
python-dotenv>=1.0.0
pyyaml>=6.0
tqdm>=4.66.0
```

---

## Environment Variables

```bash
GROQ_API_KEY=your_groq_api_key_here
```

---

## Notes

- No deployment step required for now (local development only)
- Focus on getting the core RAG pipeline working
- Can iterate on each phase independently
- Test with small datasets first before full scraping
