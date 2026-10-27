import json
import os
import traceback
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Verify key is loaded (optional debug line)
print("API Key loaded:", bool(os.environ.get("GEMINI_API_KEY")))

from google import genai
from google.genai import types
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from knowledge_base import seed_knowledge_base, get_relevant_docs

app = FastAPI(title="Developer Support Assistant")

# Allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    seed_knowledge_base()


class QueryRequest(BaseModel):
    query: str


class Citation(BaseModel):
    id: int
    title: str
    url: str


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]


def build_prompt_and_citations(query: str) -> tuple[str, list[Citation]]:
    retrieved_docs = get_relevant_docs(query, top_k=2)
    citations = [
        Citation(id=idx, title=doc["title"], url=doc["source"])
        for idx, doc in enumerate(retrieved_docs, start=1)
    ]
    context_str = "".join(
        f"--- Source [{idx}]: {doc['title']} ---\n{doc['content']}\n\n"
        for idx, doc in enumerate(retrieved_docs, start=1)
    )
    prompt = f"""
You are an expert Developer Support Assistant. Answer the user's technical question using ONLY the provided documentation context below.

Rules:
- Include inline citations like [1], [2] when stating facts from the sources.
- Be concise, direct, and code-oriented.
- If the answer cannot be found in the context, explicitly reply: "I do not have enough information in the developer knowledge base to answer this question."

Documentation Context:
{context_str}

User Question: {query}
"""
    return prompt, citations


def stream_event(event_type: str, **data: object) -> str:
    return json.dumps({"type": event_type, **data}) + "\n"


# Initialize Gemini client using environment variable GEMINI_API_KEY
gemini_client = genai.Client()
gemini_model = os.getenv("GEMINI_MODEL") or "gemini-3.8-flash"


@app.post("/api/query", response_model=QueryResponse)
async def handle_query(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    prompt, citations = build_prompt_and_citations(req.query)

    try:
        response = gemini_client.interactions.create(
            model=gemini_model,
            input=prompt,
        )

        return QueryResponse(answer=response.output_text, citations=citations)
    except Exception as e:
        import traceback

        traceback.print_exc()  # This prints the exact error in your terminal
        raise HTTPException(
            status_code=500, detail=f"Error generating AI response: {str(e)}"
        )


@app.post("/api/query/stream")
def handle_query_stream(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    def generate():
        try:
            yield stream_event("progress", message="Searching the knowledge base...")
            prompt, citations = build_prompt_and_citations(req.query)
            yield stream_event(
                "progress",
                message=f"Found {len(citations)} sources. Waiting for Gemini...",
            )

            response_stream = gemini_client.interactions.create(
                model=gemini_model,
                input=prompt,
                stream=True,
            )
            for event in response_stream:
                if event.event_type == "step.delta" and event.delta.type == "text":
                    yield stream_event("text", text=event.delta.text)

            yield stream_event(
                "done",
                citations=[citation.model_dump() for citation in citations],
            )
        except Exception as exc:
            traceback.print_exc()
            yield stream_event(
                "error",
                message=f"Error generating AI response: {exc}",
            )

    return StreamingResponse(generate(), media_type="application/x-ndjson")