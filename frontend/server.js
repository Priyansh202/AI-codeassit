const express = require("express");
const path = require("path");
require("dotenv").config();

const app = express();
const PORT = process.env.PORT || 3000;
const API_BASE_URL = process.env.API_BASE_URL || "http://localhost:8000";

app.use(express.json({ limit: "1mb" }));
app.use(express.static(path.join(__dirname, "public")));

async function proxyToApi(endpoint, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });

  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  return { status: response.status, body };
}

app.get("/api/health", async (_req, res) => {
  try {
    const { status, body } = await proxyToApi("/health");
    res.status(status).json(body);
  } catch (error) {
    res.status(503).json({
      status: "error",
      message: "Cannot reach the FastAPI backend. Start it with uvicorn app.main:app --reload",
      detail: error.message,
    });
  }
});

app.post("/api/ask", async (req, res) => {
  const question = String(req.body?.question || "").trim();
  if (question.length < 3) {
    return res.status(400).json({ detail: "Question must be at least 3 characters." });
  }

  try {
    const { status, body } = await proxyToApi("/ask", {
      method: "POST",
      body: JSON.stringify({ question }),
    });
    res.status(status).json(body);
  } catch (error) {
    res.status(503).json({
      detail: "Cannot reach the FastAPI backend.",
      message: error.message,
    });
  }
});

app.get("*", (_req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
});

app.listen(PORT, () => {
  console.log(`Frontend running at http://localhost:${PORT}`);
  console.log(`Proxying API requests to ${API_BASE_URL}`);
});
