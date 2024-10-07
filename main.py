from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
import google.generativeai as genai
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# Loading environment variables
load_dotenv()

# Configure the logging
logging.basicConfig(
    handlers=[RotatingFileHandler('app.log', maxBytes=100000, backupCount=5)],
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initializing FastAPI app
app = FastAPI(title="PDF Chat API")

# Adding CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Gemini module
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize embeddings model
embedding_function = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}
)

# Creating vector store
vectorstore = None

# Store PDF metadata
pdf_metadata = {}

class ChatMessage(BaseModel):
    message: str

@app.post("/v1/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        # Generating unique ID for the PDF
        pdf_id = str(uuid.uuid4())
        
        # Save the uploaded file temporarily
        temp_path = f"temp_{pdf_id}.pdf"
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Process the PDF
        loader = PyPDFLoader(temp_path)
        documents = loader.load()
        
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        texts = text_splitter.split_documents(documents)
        
        # Store in vector database
        global vectorstore
        vectorstore = Chroma.from_documents(texts, embedding_function)
        
        # Store the metadata
        pdf_metadata[pdf_id] = {
            "filename": file.filename,
            "page_count": len(documents)
        }
        
        # Clean up temporary files
        os.remove(temp_path)
        
        logger.info(f"Successfully processed PDF with ID: {pdf_id}")
        return {"pdf_id": pdf_id}
    
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/chat/{pdf_id}")
async def chat_with_pdf(pdf_id: str, message: ChatMessage):
    try:
        if pdf_id not in pdf_metadata:
            raise HTTPException(status_code=404, detail="PDF not found")
        
        if not vectorstore:
            raise HTTPException(status_code=500, detail="Vector store not initialized")
        
        # Retrieve relevant context
        relevant_chunks = vectorstore.similarity_search(message.message, k=5)
        context = " ".join([chunk.page_content for chunk in relevant_chunks])
        
        # Generate response using Gemini with giving it a promot in order not to contain unwanted extra info
        prompt = f"""
        Based on the following context from a PDF document, please answer the question.
        
        Context: {context}
        
        Question: {message.message}
        
        Please provide a comprehensive answer based solely on the information provided in the context.
        """
        
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        
        logger.info(f"Generated response for PDF {pdf_id}")
        return {"response": response.text}
    
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)