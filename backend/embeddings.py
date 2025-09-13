# vectorstore_builder.py
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from knowledge_base import load_and_split_pdf
import os

def create_faiss_index(pdf_path, index_path="faiss_index_pricing"):
    
    texts = load_and_split_pdf(pdf_path)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-large", dimensions=300)

    vectorstore = FAISS.from_documents(texts, embeddings)

    os.makedirs(index_path, exist_ok=True)
    vectorstore.save_local(index_path)
    print(f"[INFO] FAISS index saved to {index_path}")

    return vectorstore, embeddings
