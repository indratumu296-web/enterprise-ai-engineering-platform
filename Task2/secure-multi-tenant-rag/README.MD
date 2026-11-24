# Enterprise Multi-Tenant RAG with RBAC

A secure AI question-answering system enforcing multi-tenancy, Role-Based Access Control (RBAC), cross-encoder re-ranking, query rewriting, and verifiable page-level citations.

## Features
- **Multi-Tenancy & RBAC:** Enforces tenant isolation, department permissions, and clearance level bounds before retrieval.
- **Query Rewriting:** Clarifies ambiguous user questions using an LLM.
- **Cross-Encoder Reranking:** Reranks candidate vector results using `cross-encoder/ms-marco-MiniLM-L-6-v2`.
- **Verifiable Citations:** Tracks exact PDF source filenames and page numbers.

## Setup Instructions

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure OpenAI:**
   Create a `.env` file in this project folder and add your valid OpenAI API key:
   ```text
   OPENAI_API_KEY=your_valid_openai_api_key
   ```
   Replace the placeholder with your own key. Do not share or commit the key.

3. **Run the app from the `project2` folder (PowerShell):**
   ```powershell
   python -m streamlit run .\Task2\secure-multi-tenant-rag\app.py
   ```

   Alternatively, from this project folder:
   ```powershell
   cd .\Task2\secure-multi-tenant-rag
   streamlit run app.py