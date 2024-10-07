import pytest
from fastapi.testclient import TestClient
from main import app
import os

client = TestClient(app)

def test_upload_pdf():
    # Create a small test PDF file
    with open("test.pdf", "wb") as f:
        f.write(b"%PDF-1.0\n%\xe2\xe3\xcf\xd3\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 3 3]>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000018 00000 n\n0000000077 00000 n\n0000000178 00000 n\n\ntrailer\n<</Size 4/Root 1 0 R>>\nstartxref\n457\n%%EOF\n")

    # Test uploading the PDF
    with open("test.pdf", "rb") as f:
        response = client.post("/v1/pdf", files={"file": ("test.pdf", f, "application/pdf")})
    
    assert response.status_code == 200
    assert "pdf_id" in response.json()
    
    # Clean up
    os.remove("test.pdf")
    return response.json()["pdf_id"]

def test_chat_with_pdf():
    # First upload a PDF
    pdf_id = test_upload_pdf()
    
    # Test chatting with the PDF
    response = client.post(
        f"/v1/chat/{pdf_id}",
        json={"message": "What is this document about?"}
    )
    
    assert response.status_code == 200
    assert "response" in response.json()

def test_chat_with_invalid_pdf_id():
    response = client.post(
        "/v1/chat/invalid_id",
        json={"message": "What is this document about?"}
    )
    
    assert response.status_code == 404

def test_upload_invalid_file():
    with open("test.txt", "w") as f:
        f.write("This is not a PDF")

    with open("test.txt", "rb") as f:
        response = client.post("/v1/pdf", files={"file": ("test.txt", f, "text/plain")})
    
    assert response.status_code == 500
    
    # Clean up
    os.remove("test.txt")