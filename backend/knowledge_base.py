import os
import chromadb
from chromadb.utils import embedding_functions

# Initialize local persistent ChromaDB instance
chroma_client = chromadb.PersistentClient(path="./chroma_db")
embedding_fn = embedding_functions.DefaultEmbeddingFunction()

collection = chroma_client.get_or_create_collection(
    name="developer_docs", embedding_function=embedding_fn
)


def seed_knowledge_base():
    """Populates the vector database with sample developer documentation."""
    if collection.count() > 0:
        print("Knowledge base already contains data. Skipping seed.")
        return

    docs = [
        {
            "id": "doc_1",
            "title": "API Authentication Guide",
            "source": "https://docs.devportal.com/auth/bearer-token",
            "content": "To authenticate with the API, include your API token in the HTTP Authorization header as 'Bearer <YOUR_KEY>'. API keys are managed in your dashboard under Developer Settings.",
        },
        {
            "id": "doc_2",
            "title": "Rate Limits and Quotas",
            "source": "https://docs.devportal.com/core/rate-limits",
            "content": "Free tier applications are limited to 60 requests per minute per IP address. Exceeding this limit results in a 429 Too Many Requests response code.",
        },
        {
            "id": "doc_3",
            "title": "Docker Deployment Guide",
            "source": "https://docs.devportal.com/deploy/docker",
            "content": "Deploy your API service using Docker by building an image with 'docker build -t app:latest .' and running it with environment variables for database URLs.",
        },
    ]

    for doc in docs:
        collection.add(
            ids=[doc["id"]],
            documents=[doc["content"]],
            metadatas=[{"title": doc["title"], "source": doc["source"]}],
        )
    print("Successfully seeded Knowledge Base!")


def get_relevant_docs(query: str, top_k: int = 2):
    """Retrieves top-k relevant documentation chunks based on semantic similarity."""
    results = collection.query(query_texts=[query], n_results=top_k)

    retrieved = []
    if results and "documents" in results and len(results["documents"]) > 0:
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        for doc_text, meta in zip(docs, metas):
            retrieved.append(
                {
                    "content": doc_text,
                    "title": meta.get("title", "Unknown Source"),
                    "source": meta.get("source", "#"),
                }
            )
    return retrieved