# Gdrive link
https://drive.google.com/file/d/13gMUwHyHveKVqjHbpYKjUJtc_LsqqzLc/view?usp=sharing

# sales-bot-prediction
FinanceHub AI Sales Bot
Project 3: Sales Page Quick-Answer & Lead Bot (Engage → Inform → Identify)
Project Overview
A lightweight AI-powered sales bot that transforms passive website visitors into qualified leads through intelligent engagement, instant answers, and natural lead capture.
Problem Solved

Before: Visitors bounce without engaging, sales team handles repetitive questions
After: Instant AI responses, smart nudging, qualified lead capture with zero sales team overhead

#### Core Features
Instant FAQ System

#### Keyword-based matching for common questions
Sub-second response times
Source attribution for trust

#### RAG-Powered Intelligence

FAISS vector database for document search
OpenAI embeddings for semantic understanding
Conversational memory across sessions

#### Smart Lead Capture

Intent scoring based on question types
Progressive disclosure (2+ questions trigger form)
Automatic lead quality classification

#### Intelligent Nudging

Time-based nudges (15 seconds)
Context-aware prompts
Dismissible with session persistence

Sales Team Control

Configurable FAQs via config.json
Adjustable nudge timing and messages
Lead capture field customization


# Environment Setup
Clone repository
git clone <repo-url>
cd sales-bot

# Install dependencies  
pip install -r requirements.txt

# Set environment variables
echo "OPENAI_API_KEY=your_key_here" > .env

Terminal 1: Start FastAPI server
uvicorn app:app --reload --host 0.0.0.0 --port 8000

Server will start on http://localhost:8000
API docs available at http://localhost:8000/docs

Terminal 2: Start Streamlit app
streamlit run main.py

App will open at http://localhost:8501

TechStack
Streamlit
FastAPI
FAISS
OpenAI GPT-3.5 + Embeddings
Langchain
JSON