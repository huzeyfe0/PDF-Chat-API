# PDF Chat API

This FastAPI application enables users to upload PDF documents and chat with their content using Google's Gemini AI model.

## Features

- PDF upload and processing
- Conversational AI interface for PDF content
- Efficient text retrieval using vector embeddings
- Comprehensive error handling and logging

## Setup Instructions

1. Clone the repository:

```bash
git clone <repository-url>
cd pdf-chat-api
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your Gemini API key:

```
GEMINI_API_KEY=your_api_key_here
```

5. Run the application:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Upload PDF

- **URL**: `/v1/pdf`
- **Method**: POST
- **Content-Type**: multipart/form-data
- **Request Body**: PDF file
- **Response**: JSON containing the PDF ID

Example using curl:

```bash
curl -X POST "http://localhost:8000/v1/pdf" -F "file=@/path/to/your/document.pdf"
```

### Chat with PDF

- **URL**: `/v1/chat/{pdf_id}`
- **Method**: POST
- **Content-Type**: application/json
- **Request Body**: JSON containing the message
- **Response**: JSON containing the AI-generated response

Example using curl:

```bash
curl -X POST "http://localhost:8000/v1/chat/{pdf_id}" \
     -H "Content-Type: application/json" \
     -d '{"message":"What is the main topic of this PDF?"}'
```

## Implementation Details

### RAG Implementation

This solution uses Retrieval-Augmented Generation (RAG) to handle large documents efficiently:

1. Documents are split into chunks and embedded using sentence-transformers
2. Embeddings are stored in a Chroma vector store
3. User queries are used to retrieve relevant chunks
4. Retrieved context is sent to Gemini along with the user's question

### Error Handling

The application includes comprehensive error handling:

- Input validation for PDF files
- Proper HTTP status codes for different error scenarios
- Detailed logging of all operations

## Testing

To run the tests:

```bash
pytest tests/
```

## Limitations and Considerations

- The application currently stores documents in memory. For production use, consider implementing persistent storage.
- The Gemini API has rate limits. Implement appropriate rate limiting in a production environment.
