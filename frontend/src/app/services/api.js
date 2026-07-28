// frontend/src/services/api.js
const BACKEND_URL = "http://127.0.0.1:8000";

// 1. Saare rooms ka live status fetch karne ke liye
export const fetchRooms = async () => {
  const res = await fetch(`${BACKEND_URL}/rooms`);
  if (!res.ok) throw new Error("Failed to fetch rooms");
  return res.json();
};

// 2. AI Agent ko text message/command bhejne ke liye
export const sendAgentPrompt = async (prompt) => {
  const res = await fetch(`${BACKEND_URL}/agent/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok) throw new Error("Agent communication failed");
  return res.json();
};

// 3. AI Agent ko Guest ka CV ya Document upload karne ke liye
export const uploadCVAndBook = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${BACKEND_URL}/agent/upload-cv`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("CV processing failed");
  return res.json();
};