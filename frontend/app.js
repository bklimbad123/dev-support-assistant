const API_URL = "http://localhost:8000/api/query/stream";

async function submitQuery() {
  const queryInput = document.getElementById("queryInput");
  const submitBtn = document.getElementById("submitBtn");
  const responseContainer = document.getElementById("responseContainer");
  const answerText = document.getElementById("answerText");
  const citationsList = document.getElementById("citationsList");
  const statusText = document.getElementById("statusText");
  const statusSpinner = document.getElementById("statusSpinner");

  const query = queryInput.value.trim();
  if (!query) return;

  submitBtn.disabled = true;
  submitBtn.innerText = "Working...";
  answerText.innerText = "";
  citationsList.innerHTML = "";
  statusText.innerText = "Connecting to assistant...";
  statusSpinner.classList.remove("hidden");
  responseContainer.classList.remove("hidden");

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });

    if (!res.ok) {
      const error = await res.json().catch(() => null);
      throw new Error(error?.detail || "Failed to process query.");
    }
    if (!res.body) throw new Error("Your browser does not support streamed responses.");

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let completed = false;

    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.trim()) continue;
        const event = JSON.parse(line);
        if (event.type === "progress") {
          statusText.innerText = event.message;
        } else if (event.type === "text") {
          answerText.innerText += event.text;
          statusText.innerText = "Writing your answer...";
        } else if (event.type === "done") {
          renderCitations(event.citations);
          statusText.innerText = "Answer complete.";
          statusSpinner.classList.add("hidden");
          completed = true;
        } else if (event.type === "error") {
          throw new Error(event.message);
        }
      }

      if (done) break;
    }

    if (buffer.trim()) {
      const event = JSON.parse(buffer);
      if (event.type === "error") throw new Error(event.message);
    }
    if (!completed) throw new Error("The response ended before the answer was complete.");
  } catch (err) {
    statusText.innerText = "Could not finish the answer.";
    statusSpinner.classList.add("hidden");
    answerText.innerText += answerText.innerText ? "\n\n" : "";
    answerText.innerText += `Error: ${err.message}`;
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerText = "Ask Assistant";
  }
}

function renderCitations(citations) {
  const citationsList = document.getElementById("citationsList");
  citationsList.innerHTML = "";
  if (citations.length > 0) {
    citations.forEach((citation) => {
      const li = document.createElement("li");
      const link = document.createElement("a");
      link.href = citation.url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.innerText = citation.title;
      li.append(`[${citation.id}] `, link);
      citationsList.appendChild(li);
    });
  } else {
    citationsList.innerHTML = "<li>No specific sources referenced.</li>";
  }
}