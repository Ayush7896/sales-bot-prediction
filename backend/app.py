from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import BotResponse, UserQuery
from dotenv import load_dotenv
import os
from embeddings import create_faiss_index
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate  
from typing import Dict
from config import config, check_quick_faq
import json
from datetime import datetime

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session-based storage
session_memories: Dict[str, ConversationBufferMemory] = {}
session_chains: Dict[str, ConversationalRetrievalChain] = {}
session_question_counts: Dict[str, int] = {}  # Track questions per session

PDF_PATH = "/home/ayush/Projects_1/sales-bot/sales-bot-prediction/backend/finance_company_pricing.pdf"
INDEX_PATH = "/home/ayush/Projects_1/sales-bot/sales-bot-prediction/backend/faiss_index_pricing"

if not os.path.exists(INDEX_PATH):
    vectorstore, embeddings = create_faiss_index(PDF_PATH, INDEX_PATH)
else:
    print("[INFO] Loading existing FAISS index...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large", dimensions=300)
    vectorstore = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)

retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})

# LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.2, api_key=OPENAI_API_KEY)

custom_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful assistant for a finance company. Use the conversation history to maintain context about the user and their previous questions.

Instructions:
1. Always refer to the chat history to remember user details (like their name, previous questions, etc.)
2. Use the document context to answer questions about finance products and pricing
3. Be conversational and remember what the user has told you
4. If asked about previous questions or conversations, refer to the chat history
5. If the user has asked more than 2 questions and hasn't provided contact details yet, politely suggest they share their email for personalized assistance."""),
    ("human", """Chat History:
{chat_history}

Context from documents:
{context}

Current Question: {question}""")
])

def get_or_create_chain(session_id: str) -> ConversationalRetrievalChain:
    if session_id not in session_chains:
        memory = ConversationBufferMemory(
            memory_key="chat_history", 
            k=10, 
            return_messages=True,
            output_key="answer"
        )
        session_memories[session_id] = memory
        session_chains[session_id] = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory,
            return_source_documents=False,
            combine_docs_chain_kwargs={"prompt": custom_prompt}
        )
        session_question_counts[session_id] = 0
    return session_chains[session_id]

@app.post("/ask", response_model=BotResponse)
async def ask(request: UserQuery):
    try:
        # Track question count
        if request.session_id not in session_question_counts:
            session_question_counts[request.session_id] = 0
        session_question_counts[request.session_id] += 1
        
        # Check for quick FAQ match first
        faq_result = check_quick_faq(request.user_query)
        
        if faq_result["found"]:
            # Return instant FAQ answer
            nudge = ""
            # Add nudge based on FAQ category
            if faq_result.get("category") == "eligibility":
                nudge = config.get("nudges", {}).get("application_ready", "")
            elif faq_result.get("category") == "documents_required":
                nudge = config.get("nudges", {}).get("document_help", "")
            elif faq_result.get("category") == "contact":
                nudge = "Feel free to call us or visit our office!"
            
            return BotResponse(
                bot_response=faq_result["answer"],
                sources=[faq_result["source"]],
                is_instant_faq=True,
                nudge=nudge if nudge else None
            )
        
        # Get or create chain for this session
        qa_chain = get_or_create_chain(request.session_id)
        
        # Run the query through RAG
        response = qa_chain.invoke({"question": request.user_query})
        answer = response.get("answer", "Sorry, I could not generate an answer.")

        sources = ["finance_company_pricing.pdf"] 
        
        # Check if we should prompt for lead capture
        nudge = None
        if session_question_counts[request.session_id] == 2:
            nudge = "I notice you have several questions. Would you like to share your contact details so our team can provide personalized assistance?"
        
        return BotResponse(
            bot_response=answer,
            sources=sources,
            nudge=nudge
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))