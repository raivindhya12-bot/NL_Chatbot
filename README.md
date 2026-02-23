# RAG Chatbot for NextLeap.app

A Retrieval-Augmented Generation (RAG) chatbot that provides intelligent responses about NextLeap.app content using Groq LLM.

## Project Overview

This project implements a 3-phase RAG system:
1. **Phase 1**: Scrape and preprocess data from nextleap.app
2. **Phase 2**: Convert text into embeddings and store in vector database
3. **Phase 3**: Retrieve relevant context and generate responses using Groq LLM

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed architecture documentation.

## Quick Start

### Prerequisites

- Python 3.9+
- Groq API key ([Get one here](https://console.groq.com/))

### Installation

```bash
# Clone or navigate to project directory
cd RAG_Chatbot_v1

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
echo "GROQ_API_KEY=your_api_key_here" > .env
```

### Usage

#### Phase 1: Scrape and Preprocess
```bash
python phase1_scraping/scraper.py
python phase1_scraping/preprocessor.py
```

#### Phase 2: Generate Embeddings
```bash
python phase2_embeddings/embedding_generator.py
python phase2_embeddings/vector_store.py
```

#### Phase 3: Query and Response
```bash
python phase3_query/rag_pipeline.py --query "What courses does NextLeap offer?"
```

## Project Structure

```
RAG_Chatbot_v1/
├── phase1_scraping/      # Data scraping and preprocessing
├── phase2_embeddings/    # Embedding generation and storage
├── phase3_query/         # Query processing and RAG pipeline
├── data/                 # Data storage (raw, processed, embeddings)
├── config/               # Configuration files
├── utils/                # Utility functions
├── ARCHITECTURE.md       # Detailed architecture documentation
└── README.md            # This file
```

## Development Status

- [ ] Phase 1: Data Scraping & Preprocessing
- [ ] Phase 2: Embeddings & Vector Storage
- [ ] Phase 3: Query & Response Generation

## License

MIT
