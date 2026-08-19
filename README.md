# 📚 PDF AI — RAG PDF Chatbot

An AI-powered PDF chatbot that allows users to upload their PDF documents and ask questions about them using Retrieval-Augmented Generation (RAG).

The application uses a React frontend, FastAPI backend, vector embeddings, ChromaDB, and OpenRouter-powered LLMs to provide contextual answers with PDF citations.

---

## 🚀 Features

### 🔐 Authentication

- User registration and login
- Secure password hashing using bcrypt
- JWT-based authentication
- User-specific accounts
- Google OAuth login integration
- Email-based user identification
- User profile information stored in the database

### 📄 PDF Management

- Upload PDF documents
- Multiple PDF uploads
- PDF size validation
- User-specific PDF library
- Secure file naming using UUIDs
- PDF storage separated by user

### 🤖 AI & RAG

- Retrieval-Augmented Generation (RAG)
- PDF text extraction
- Document chunking
- HuggingFace embeddings
- ChromaDB vector search
- Semantic document retrieval
- OpenRouter LLM integration
- Context-aware answers
- Source citations and excerpts

### 💬 Chat

- Ask questions about selected PDFs
- Chat history storage
- Multiple conversations
- Chat sessions associated with users
- PDF-specific conversations
- Source citations for generated answers

### 🎨 Frontend

- Modern dark UI
- React-based interface
- Login and Signup pages
- Dashboard
- Sidebar navigation
- PDF upload interface
- Chat interface
- Responsive authentication pages

---

## 🏗️ Architecture

```text
                         ┌─────────────────────┐
                         │      React UI       │
                         │     Vite Frontend   │
                         └──────────┬──────────┘
                                    │
                                    │ REST API
                                    ▼
                         ┌─────────────────────┐
                         │    FastAPI Backend  │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
              Authentication    PDF Processing   Chat API
                    │               │               │
                    ▼               ▼               ▼
                  JWT          Text Extraction    RAG Pipeline
                    │               │               │
                    │               ▼               ▼
                    │          Chunking        Vector Search
                    │               │               │
                    │               ▼               ▼
                    │          Embeddings      ChromaDB
                    │                               │
                    │                               ▼
                    │                         OpenRouter
                    │                               │
                    └───────────────────────────────┘
