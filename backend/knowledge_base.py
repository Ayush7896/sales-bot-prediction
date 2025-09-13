from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAI, OpenAIEmbeddings
from dotenv import load_dotenv


load_dotenv()
FILENAME = "filepath"
class DocumentLoader:

    def __init__(self):
        self.model = ''

    def pdf_loader(self, filename):
        loader = PyPDFLoader(filename)
        pages = []
        for page in loader.load():
            pages.append(page)
        return pages
    
    def splitting_text(self,documents):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size = 500, 
                                               chunk_overlap = 200,
                                               length_function = lambda text:len(text.split()))

        texts = text_splitter.split_documents(documents)
        return texts


def load_and_split_pdf(filename):
    loader = DocumentLoader()
    documents = loader.pdf_loader(filename)
    texts = loader.splitting_text(documents)
    print(f"[INFO] Total split documents: {len(texts)}")
    return texts

