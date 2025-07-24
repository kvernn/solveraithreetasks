# Submission for the Solver AI Technical Assessment

### Introduction

This repository contains my submission for the technical assessment from Solver AI. I found it to be an engaging challenge and approached the three tasks by building them out as end-to-end, deployed web applications. My attempt at the requirements resulted in a RAG-powered AI avatar coach with a cloud CRM; a meta-agent that generates automation workflows from natural language; and an emotionally-aware product recommender that uses vector search. Throughout these projects, I prioritized the recommended cost-efficient stack, utilizing tools like Streamlit, DeepSeek, Pinecone, and Turso. The live demos and detailed documentation for each task are linked in the showcase below.

---

## 🚀 Project Showcase

| Project | Description | Key Technologies | Live Demo & Docs |
| :--- | :--- | :--- | :--- |
| **Task 1: AI Avatar Coach** | A voice-enabled, RAG-powered conversational AI with a talking D-ID avatar, grounded in a custom knowledge base about personal development. | `Streamlit`, `D-ID`, `ElevenLabs`, `Pinecone`, `Turso (SQLite)`, `RAG` | [▶️ Live Demo](https://task1avatarcoach.streamlit.app/) - [📄 View README](https://github.com/kvernn/solveraithreetasks/blob/main/task%201%20avatar%20coach/README.md) |
| **Task 2: Agentic AI Flow Builder** | A meta-agent that translates natural language requests into structured, executable n8n-style automation workflows with visual previews. | `Streamlit`, `DeepSeek`, `n8n JSON`, `Regex`, `Agentic Logic` | [▶️ Live Demo](https://task2metaagent.streamlit.app/) - [📄 View README](https://github.com/kvernn/solveraithreetasks/blob/main/task%202%20meta%20agent/README.md) |
| **Task 3: AI-Personalized Shoe Recommender** | An emotionally-aware RAG chatbot that provides personalized product recommendations based on user mood, budget, and context. | `Streamlit`, `Pinecone`, `RAG`, `DeepSeek`, `Turso (SQLite)` | [▶️ Live Demo](https://task3chatbotshoerecommender.streamlit.app/) - [📄 View README](https://github.com/kvernn/solveraithreetasks/tree/main/task%203%20recommender) |

---

## 🛠️ Overall Technical Stack

This portfolio demonstrates proficiency across the full AI application stack:

- **Frontend:** Streamlit
- **Backend & Orchestration:** Python, Asyncio
- **AI/LLMs:** DeepSeek (via OpenRouter), Prompt Engineering, RAG Architecture
- **Vector DB & Embeddings:** Pinecone, SentenceTransformers
- **Cloud Database (CRM):** Turso (SQLite)
- **Multi-Modal APIs:** D-ID (Video), ElevenLabs (Voice)
- **Deployment:** Streamlit Cloud, Git