// frontend/src/app/page.js
"use client";
import { useEffect, useState } from "react";
// page.js ki line 4 ko is se replace karo agar services folder 'src' ke andar ha:
// Line number 5 ko is se replace karo:
import { fetchRooms, sendAgentPrompt, uploadCVAndBook } from "./services/api";export default function Home() {
  const [rooms, setRooms] = useState([]);
  const [prompt, setPrompt] = useState("");
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  // Database se live rooms data fetch karna
  const loadData = async () => {
    try {
      const data = await fetchRooms();
      setRooms(data);
    } catch (err) {
      console.error("Error loading rooms:", err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // AI Agent ko Text input command bhejna
  const handleAgentSubmit = async (e) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setLoading(true);
    setLogs((prev) => [`User: ${prompt}`, ...prev]);
    
    try {
      const response = await sendAgentPrompt(prompt);
      
      if (response.result) {
        setLogs((prev) => [`AI Tool Action Result: ${response.result}`, ...prev]);
      }
      setLogs((prev) => [`AI Agent: ${response.agent_response}`, ...prev]);
      
      setPrompt("");
      await loadData(); // Booking ke baad grid reload karna
    } catch (err) {
      setLogs((prev) => ["Error: Could not communicate with AI Agent.", ...prev]);
    } finally {
      setLoading(false);
    }
  };

  // CV/ID Card Document Upload Handle karna
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setLoading(true);
    setLogs((prev) => [`System: Uploading ${file.name} for AI Analysis...`, ...prev]);

    try {
      const response = await uploadCVAndBook(file);
      
      if (response.result) {
        setLogs((prev) => [`AI Tool Action Result: ${response.result}`, ...prev]);
      }
      setLogs((prev) => [`AI Agent: ${response.agent_response}`, ...prev]);
      
      await loadData(); // Grid refresh
    } catch (err) {
      setLogs((prev) => ["Error: Document parsing failed.", ...prev]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-900 text-white p-8">
      {/* Header */}
      <header className="mb-8 border-b border-gray-800 pb-4">
        <h1 className="text-3xl font-bold text-teal-400">🏨 AI Hotel Management Dashboard</h1>
        <p className="text-gray-400 text-sm mt-1">Autonomous Front-Desk Agent & Multi-Modal Document Extraction</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left/Middle Column: 100 Rooms Grid */}
        <div className="lg:col-span-2 bg-gray-800 p-6 rounded-xl shadow-lg">
          <h2 className="text-xl font-semibold mb-4 text-gray-200">Live Room Status Matrix (100 Rooms)</h2>
          <div className="grid grid-cols-10 gap-2">
            {rooms.map((room) => (
              <div
                key={room.id}
                className={`p-2.5 rounded-lg text-center font-bold text-xs transition-all duration-200 ${
                  room.status === "Available"
                    ? "bg-emerald-600 hover:bg-emerald-500 shadow-emerald-900/30"
                    : "bg-rose-600 hover:bg-rose-500 shadow-rose-900/30"
                } shadow-md cursor-pointer`}
                title={`Category: ${room.category} | Price: $${room.price_per_night}`}
              >
                {room.room_number}
                <span className="block text-[9px] font-normal opacity-75">${room.price_per_night}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: AI Automation Controls & Logs */}
        <div className="flex flex-col gap-6">
          
          {/* Talk to AI Box */}
          <div className="bg-gray-800 p-6 rounded-xl shadow-lg">
            <h2 className="text-lg font-semibold mb-3 text-teal-400">Talk to AI Agent</h2>
            <form onSubmit={handleAgentSubmit} className="space-y-3">
              <input
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="e.g., Check if room 5 is available..."
                className="w-full p-3 bg-gray-700 rounded-lg border border-gray-600 focus:outline-none focus:border-teal-400 text-sm text-white"
              />
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-teal-500 hover:bg-teal-600 text-gray-900 font-bold p-2.5 rounded-lg transition-all text-sm disabled:opacity-50"
              >
                {loading ? "Processing..." : "Send Command"}
              </button>
            </form>

            {/* Document Ingestion / CV Upload Widget */}
            <div className="pt-4 border-t border-gray-700 mt-4">
              <label className="block text-xs font-medium text-purple-400 mb-2">
                Or Drop Guest CV / ID Card Scan
              </label>
              <input
                type="file"
                onChange={handleFileUpload}
                disabled={loading}
                className="w-full text-xs text-gray-400 file:mr-4 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-purple-600 file:text-white hover:file:bg-purple-700 cursor-pointer disabled:opacity-50"
              />
            </div>
          </div>

          {/* Real-time Agent Logs Console */}
          <div className="bg-gray-800 p-6 rounded-xl shadow-lg flex-1 flex flex-col min-h-[300px]">
            <h2 className="text-lg font-semibold mb-3 text-purple-400">Agent Action Execution Logs</h2>
            <div className="bg-black/40 p-4 rounded-lg flex-1 font-mono text-xs overflow-y-auto space-y-2 max-h-[320px]">
              {logs.length === 0 && <p className="text-gray-600 italic">No autonomous actions triggered yet...</p>}
              {logs.map((log, index) => (
                <div
                  key={index}
                  className={`p-1.5 rounded ${
                    log.startsWith("User:")
                      ? "text-blue-400"
                      : log.startsWith("AI Tool")
                      ? "text-yellow-400 bg-yellow-950/20"
                      : "text-green-400"
                  }`}
                >
                  {log}
                </div>
              ))}
            </div>
          </div>

        </div>

      </div>
    </main>
  );
}