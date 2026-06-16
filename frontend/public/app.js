const examples = [
  "How do I read a CSV file in pandas?",
  "What is the difference between a list and a tuple?",
  "How can I handle missing values in a DataFrame?",
  "Explain Python list comprehensions with an example.",
  "How do I merge two DataFrames on a common key?",
];

const messagesEl = document.getElementById("messages");
const askForm = document.getElementById("askForm");
const questionInput = document.getElementById("questionInput");
const sendBtn = document.getElementById("sendBtn");
const clearBtn = document.getElementById("clearBtn");
const exampleList = document.getElementById("exampleList");
const messageTemplate = document.getElementById("messageTemplate");

const statusApi = document.getElementById("statusApi");
const statusIndex = document.getElementById("statusIndex");
const statusLlm = document.getElementById("statusLlm");
const statusDocs = document.getElementById("statusDocs");

function setStatus(el, text, tone = "") {
  el.textContent = text;
  el.className = tone;
}

function createMessage({ role, text, sources = [], meta = "" }) {
  const node = messageTemplate.content.cloneNode(true);
  const article = node.querySelector(".message");
  const avatar = node.querySelector(".avatar");
  const messageText = node.querySelector(".message-text");
  const sourcesWrap = node.querySelector(".sources");
  const metaEl = node.querySelector(".meta");

  article.classList.add(role);
  avatar.textContent = role === "user" ? "You" : "Py";
  messageText.textContent = text;

  if (sources.length > 0) {
    sourcesWrap.classList.remove("hidden");
    sourcesWrap.innerHTML = "<h3>Sources</h3>";
    sources.forEach((source) => {
      const card = document.createElement("div");
      card.className = "source-card";
      card.innerHTML = `
        <strong>${escapeHtml(source.title)}</strong>
        <p>${escapeHtml(source.excerpt)}</p>
        ${
          source.score != null
            ? `<span class="source-score">relevance ${Number(source.score).toFixed(3)}</span>`
            : ""
        }
      `;
      sourcesWrap.appendChild(card);
    });
  }

  if (meta) {
    metaEl.classList.remove("hidden");
    metaEl.textContent = meta;
  }

  messagesEl.appendChild(node);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return article;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function createTypingMessage() {
  const node = messageTemplate.content.cloneNode(true);
  const article = node.querySelector(".message");
  const avatar = node.querySelector(".avatar");
  const messageText = node.querySelector(".message-text");

  article.classList.add("assistant");
  avatar.textContent = "Py";
  messageText.innerHTML =
    '<span class="typing" aria-label="Assistant is typing"><span></span><span></span><span></span></span>';

  messagesEl.appendChild(node);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return article;
}

async function loadHealth() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Health check failed");
    }

    setStatus(statusApi, "Online", "ok");
    setStatus(statusIndex, data.index_ready ? "Ready" : "Building", data.index_ready ? "ok" : "warn");
    setStatus(statusLlm, data.llm_configured ? "Configured" : "Retrieval only", data.llm_configured ? "ok" : "warn");
    setStatus(statusDocs, String(data.document_count ?? 0), "ok");
  } catch (error) {
    setStatus(statusApi, "Offline", "bad");
    setStatus(statusIndex, "—", "bad");
    setStatus(statusLlm, "—", "bad");
    setStatus(statusDocs, "—", "bad");
    console.error(error);
  }
}

async function askQuestion(question) {
  const typing = createTypingMessage();
  sendBtn.disabled = true;

  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await response.json();
    typing.remove();

    if (!response.ok) {
      createMessage({
        role: "assistant",
        text: data.detail || data.message || "Something went wrong while answering your question.",
      });
      return;
    }

    createMessage({
      role: "assistant",
      text: data.answer,
      sources: data.sources || [],
      meta: `Mode: ${data.mode === "generation" ? "LLM + retrieval" : "Retrieval only"}`,
    });
  } catch (error) {
    typing.remove();
    createMessage({
      role: "assistant",
      text: "Could not reach the backend. Make sure the FastAPI server is running on port 8000.",
    });
    console.error(error);
  } finally {
    sendBtn.disabled = false;
  }
}

askForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (question.length < 3) {
    return;
  }

  createMessage({ role: "user", text: question });
  questionInput.value = "";
  await askQuestion(question);
});

clearBtn.addEventListener("click", () => {
  messagesEl.innerHTML = "";
  createMessage({
    role: "assistant",
    text: "Chat cleared. Ask another Python question whenever you're ready.",
  });
});

questionInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    askForm.requestSubmit();
  }
});

examples.forEach((question) => {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "example-btn";
  button.textContent = question;
  button.addEventListener("click", () => {
    questionInput.value = question;
    questionInput.focus();
  });
  exampleList.appendChild(button);
});

loadHealth();
