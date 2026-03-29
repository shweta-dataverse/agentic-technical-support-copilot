# 🧠 Agentic Jira Support Co-Pilot

An end-to-end **Agentic AI system** that automates technical support resolution for Jira tickets using **RAG (Retrieval-Augmented Generation), Hybrid Search, and Multi-Agent orchestration**.

---

## 🚀 Overview

This project simulates a real-world **enterprise technical support assistant** for systems like **Siemens SIMATIC S7-1500 / ET 200MP**.

It can:
- Analyze incoming Jira tickets
- Retrieve similar historical tickets
- Retrieve knowledge from technical manuals
- Generate accurate, grounded resolutions using LLMs
- Store and track results for evaluation and improvement

---

## 🏗️ Architecture

PDF Manuals → Chunking → Embeddings → FAISS

Jira Tickets → PostgreSQL → Embeddings → FAISS

User Query / Ticket
↓
Hybrid Retrieval (FAISS + BM25)
↓
Knowledge Agent + Jira Agent
↓
Synthesis Agent (LLM)
↓
Final Resolution
↓
Evaluation + MLflow Tracking


---

## ⚙️ Tech Stack

### 🧠 AI / ML
- 🦙 LLaMA 3 (via Ollama)
- 🤗 Sentence Transformers
- 🔗 LangChain
- 🔄 LangGraph (Agent orchestration)

### 📚 Retrieval
- FAISS (Vector DB)
- BM25 (Keyword search)
- Hybrid Retrieval (Semantic + Keyword)

### 🗄️ Data & Storage
- PostgreSQL (Ticket storage)
- JSON datasets
- Pickle (metadata storage)

### 📊 Evaluation & Monitoring
- RAGAS (Evaluation metrics)
- MLflow (Experiment tracking)

### 🖥️ App Layer
- Streamlit (UI Dashboard)

---

## 🔁 Workflow

### Phase 1: RAG Pipeline

PDF → Text Extraction → Chunking → Embeddings → FAISS

User Query → Embedding → Retrieve Top-K Chunks → LLM → Answer

---

### Phase 2: Agentic Workflow

New Jira Ticket
↓
Jira Agent
├── Retrieves similar tickets (FAISS)
├── Calls Knowledge Agent (if needed)
↓
Synthesis Agent
↓
Final Resolution

---

### Phase 3: Hybrid Retrieval

Query
├─→ FAISS (semantic)
├─→ BM25 (keyword)
└─→ Merge + Re-rank

✅ Improves:
- Precision
- Page-level grounding
- Technical accuracy

---

### Phase 4: Database Integration

Jira API → PostgreSQL
↓
Embedding Generation
↓
FAISS Storage
↓
Retrieval + Resolution
↓
Store AI Output

---

## 📊 Evaluation Strategy

### 🔍 Retrieval Metrics
- Precision@K
- Recall@K

### 🧠 Generation Metrics
- Exact Match (EM)
- ROUGE-L
- BLEU
- LLM-as-Judge (future scope)

---

## ⚠️ Challenges Solved

### ❌ Semantic Drift
- Fixed using **Hybrid Retrieval (BM25 + FAISS)**

### ❌ FAISS Index Errors
- Handled `IndexError: list index out of range`
- Added validation for:
  - invalid indices (-1)
  - metadata mismatch
  - partial ingestion cases

### ❌ Poor Grounding
- Improved using:
  - context expansion
  - chunk-level citation control

---

## 📦 Project Structure

```bash

llm-technical-support-copilot/
│
├── data/
│   ├── raw/manuals
│   ├── processed/chunks
│
├── src/copilot/
│   ├── ingestion/
│   ├── vectorstore/
│   ├── llm/
│   ├── agents/
│   ├── workflows/
│   ├── evaluation/
│   └── app.py
│
├── scripts/
│   ├── ingest_docs.py
│   └── run_copilot.py
│
├── notebooks/
├── tests/

```

---
## 📦 How To Run

```code

# ----------------------------
# 1. clone repository
# ----------------------------
git clone <your-repo-url>
cd llm-technical-support-copilot

# ----------------------------
# 2. create virtual environment
# ----------------------------
python3 -m venv .venv

# activate environment (mac/linux)
source .venv/bin/activate

# activate environment (windows)
# .venv\Scripts\activate

# ----------------------------
# 3. install dependencies
# ----------------------------
pip install -e .

# OR (if using requirements.txt)
# pip install -r requirements.txt

# ----------------------------
# 4. verify installation (optional)
# ----------------------------
python -c "from sentence_transformers import SentenceTransformer; print('ok')"
python -c "from langchain_text_splitters import RecursiveCharacterTextSplitter; print('ok')"

# ----------------------------
# 5. ingest pdf manuals → faiss
# ----------------------------
python scripts/ingest_docs.py

# ----------------------------
# 6. run copilot workflow (test ticket)
# ----------------------------
python scripts/run_copilot.py

# ----------------------------
# 7. run streamlit app (ui)
# ----------------------------
streamlit run src/copilot/app.py

# ----------------------------
# 8. setup postgresql (optional - for phase 5)
# ----------------------------
brew update
brew install postgresql

# start postgres server
pg_ctl -D /opt/homebrew/var/postgresql@14 start

# check server status
pg_isready

# connect to postgres
psql -d postgres

# inside psql:
# \l                    # list databases
# create database jira_copilot;
# \c jira_copilot       # connect to database

```
---

## 🎯 Key Highlights

- Built **end-to-end Agentic AI system**
- Implemented **Hybrid Retrieval (FAISS + BM25)**
- Designed **multi-agent architecture (LangGraph)**
- Integrated **PostgreSQL + Vector DB pipeline**
- Added **evaluation + MLflow tracking**
- Developed **interactive Streamlit dashboard**

---

## 🚀 Future Improvements

- LLM-as-Judge evaluation
- Feedback loop (RLHF style)
- Real Jira API integration
- Production deployment (Docker + CI/CD)

---

## 💡 Impact

This project demonstrates:
- Real-world **AI system design**
- Strong understanding of **RAG + Agents**
- Ability to build **production-ready pipelines**

---

## 👩‍💻 Author

Shweta Bambal  
MSc Digital Engineering | AI/ML | Data Science  

---
