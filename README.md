# MultiDocRAG (Multi-User Multi-Document RAG)

## Overview
MultiDocRAG is a full-stack Retrieval-Augmented Generation (RAG) system designed for multi-user document QA workflows. Each user can upload multiple PDF documents, create per-user retrieval collections, and query the document content with natural-language questions. The system provides secure user management, user-specific document isolation, and vectorstore cleanup/deletion support.

## Problem Statement
Most RAG demos assume a single, global corpus and do not enforce user boundaries. In real-world applications, teams or individuals need:
- multi-user login/signup support
- per-user document isolation and query context
- ability to upload multiple PDF files per user
- retrieval based on document metadata (file name, ID, user)
- safe deletion of documents without affecting others

## Proposed Solution
Implement a FastAPI backend with:
1. user authentication (signup/login with JWT)
2. per-user file upload and metadata stored in SQLite
3. per-user Chroma vectorstore collections to separate embeddings by user
4. RAG query endpoint wired through Langchain + LLM backend (Ollama/Groq)
5. deletion API to remove documents and vectorstore embeddings safely
6. React frontend with user-focused UI ideal for doc navigation and querying

## Features
- JWT-based authentication (signup/login).
- File upload (PDF) for authenticated users.
- File listing per user.
- Query-specific PDF (per file_id) across user's documents.
- Per-user RAG chain and metadata-driven source attribution.
- Delete file endpoint removing disk file, DB record, and vectorstore entries.

## Tech Stack
- Backend: Python, FastAPI
- Database: SQLite (SQLAlchemy ORM)
- Authentication: bcrypt (password hashing), JWT (PyJWT)
- RAG pipeline: Langchain, Chroma, Ollama embeddings, Groq LLM
- PDF loader: PyPDFLoader (langchain-community)
- Frontend: React (Vite)
- Storage: file system (`storage/` folder), per-user directories
- Dev tooling: Uvicorn, Node.js/Yarn or npm

## API Endpoints
### Auth
- `POST /auth/signup`
  - body: `{ "email": "...", "password": "...", "confirm_password": "..." }`
  - returns: access_token + user info

- `POST /auth/login`
  - body: `{ "email": "...", "password": "..." }`
  - returns: access_token + user info

- `POST /auth/verify`
  - body: `{ "token": "..." }`
  - returns: token validity

### Files
- `GET /files`
  - auth: Bearer token
  - returns: list of user files with metadata (`file_id`, `filename`, `created_at`)

- `POST /upload`
  - auth: Bearer token
  - multipart form data: `file` (PDF)
  - returns: created file_id and filename

- `DELETE /files/{file_id}`
  - auth: Bearer token
  - removes file, metadata, and vectorstore entries for an authenticated user

### Query
- `POST /query`
  - auth: Bearer token
  - body: `{ "question": "...", "file_id": "..." }`
  - returns: answer JSON + sources


## Usage
1. Copy env files:
   - `Backend/.env` from `Backend/.env.example`
   - `Frontend/.env` from `Frontend/.env.example` (optional for local dev)
2. Required backend keys:
   - `SECRET_KEY` (secure random string)
   - `GROQ_API_KEY` (from [console.groq.com](https://console.groq.com))
   - `DATABASE_URL=sqlite:///./app.db`
   - `CORS_ORIGINS` (comma-separated frontend URLs)
3. Install [Ollama](https://ollama.com) locally and run: `ollama pull nomic-embed-text`
4. Install backend deps: `pip install -r Backend/requirements.txt`
5. Start backend: `cd Backend && uvicorn app.main:app --reload`
6. Start frontend: `cd Frontend && npm install && npm run dev`
7. Open browser at `http://localhost:5173`

## Deployment
See **[deploy/DEPLOYMENT.md](deploy/DEPLOYMENT.md)** for the full AWS EC2 + Vercel guide (dashboard steps, PowerShell, and SSH commands).

## Future Directions
- Add rich user profile settings and enterprise role-based access (RBAC).
- Upgrade vector index persistence for horizontal scaling (Redis + Chroma/FAISS hybrid).
- Add multi-file search across all user documents (`/query` could accept a user-scoped “all docs” request).
- Add versioned document management (revisions, history, rollback).
- Add API rate limiting and quotas per user.
- Support more file types (DOCX/CSV/TXT) and improved PDF extraction metadata.
- Integrate a production-grade LLM provider with optional prompt templates and RAG paging.
- Add browser message history + 1-click source citation download.


