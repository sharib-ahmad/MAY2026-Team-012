import { useState, useRef, useEffect } from "react";
import { Bot, X, Send, AlertCircle } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { chatbotMessage } from "../lib/api";
import { formatMarkdown } from "../lib/ecobot";

const SUGGESTIONS = [
  "Show my recent pickups",
  "How many credits do I have?",
  "Segregation guide & rates",
  "What is my ticket status?",
];

export default function EcoBotWidget() {
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: `Hello ${user?.name?.split(" ")[0] || "there"}! I'm EcoBot, your Verdeza assistant. Ask me anything about waste management, your pickups, tickets, eco-credits, or reuse listings.`,
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState("");
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping, isOpen]);

  const handleSend = async (textToSend) => {
    const text = (textToSend || input).trim();
    if (!text) return;

    setError("");
    // Add user message
    const userMsg = { role: "user", text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    try {
      // Build history excluding the latest user message
      const historyPayload = messages.map((m) => ({
        role: m.role,
        text: m.text,
      }));

      const res = await chatbotMessage(text, historyPayload);
      setMessages((prev) => [...prev, { role: "bot", text: res.reply }]);
    } catch (err) {
      console.error("EcoBot API error:", err);
      setError("Failed to get response from EcoBot. Please try again.");
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <>
      {/* Floating Action Button (FAB) */}
      {!isOpen && (
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-30 w-14 h-14 rounded-full bg-[#0b362f] text-white shadow-lg flex items-center justify-center hover:bg-[#145047] active:scale-95 transition-all duration-200 group hover:ring-4 hover:ring-amber-400/30"
          title="Ask EcoBot"
        >
          <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-amber-400/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          <Bot size={24} className="group-hover:rotate-12 transition-transform duration-200" />
          <span className="absolute -top-1 -right-1 flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-amber-400"></span>
          </span>
        </button>
      )}

      {/* Chat Popover */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 z-40 w-[360px] sm:w-[400px] h-[550px] max-h-[85vh] bg-[#FBF7EE] rounded-3xl border border-gray-200 shadow-2xl flex flex-col overflow-hidden animate-slide-up">
          {/* Header */}
          <div className="bg-[#0b362f] text-white p-4 flex items-center justify-between shrink-0 shadow-md">
            <div className="flex items-center gap-2.5">
              <div className="w-10 h-10 rounded-full bg-amber-400 text-[#0B2F2C] flex items-center justify-center shrink-0">
                <Bot size={20} />
              </div>
              <div>
                <h3 className="font-display font-semibold text-base leading-tight">EcoBot</h3>
                <p className="text-[10px] text-emerald-300 font-mono tracking-wider">
                  Verdeza Assistant
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-white/80 hover:text-white hover:bg-white/20 transition-all active:scale-95"
              aria-label="Close chatbot"
            >
              <X size={18} />
            </button>
          </div>

          {/* Messages list */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`flex ${m.role === "user" ? "justify-end" : "justify-start"} animate-fade-in`}
              >
                {m.role === "bot" && (
                  <div className="w-8 h-8 rounded-full bg-amber-400 text-[#0B2F2C] flex items-center justify-center mr-2 shrink-0 shadow-sm">
                    <Bot size={14} />
                  </div>
                )}
                {m.role === "user" ? (
                  <div className="max-w-[78%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed bg-[#0b362f] text-white rounded-br-sm shadow-sm whitespace-pre-wrap">
                    {m.text}
                  </div>
                ) : (
                  <div
                    className="max-w-[78%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed bg-[#F3EEE1] text-gray-800 rounded-bl-sm border border-gray-150 shadow-sm markdown-content"
                    dangerouslySetInnerHTML={{ __html: formatMarkdown(m.text) }}
                  />
                )}
                {m.role === "user" && (
                  <div className="w-8 h-8 rounded-full bg-[#0b362f] text-white flex items-center justify-center ml-2 shrink-0 text-xs font-semibold shadow-sm border border-white/10">
                    {user?.name?.[0]?.toUpperCase() || "C"}
                  </div>
                )}
              </div>
            ))}

            {isTyping && (
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-amber-400 text-[#0B2F2C] flex items-center justify-center shrink-0 shadow-sm">
                  <Bot size={14} />
                </div>
                <div className="bg-[#F3EEE1] rounded-2xl rounded-bl-sm px-4 py-3 flex items-center gap-1.5 border border-gray-150">
                  <span className="w-1.5 h-1.5 rounded-full bg-gray-500 animate-bounce" />
                  <span className="w-1.5 h-1.5 rounded-full bg-gray-500 animate-bounce [animation-delay:0.2s]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-gray-500 animate-bounce [animation-delay:0.4s]" />
                </div>
              </div>
            )}

            {error && (
              <div className="flex items-center gap-1.5 text-xs text-red-600 bg-red-50 p-2.5 rounded-xl border border-red-100">
                <AlertCircle size={14} />
                <span>{error}</span>
              </div>
            )}
          </div>

          {/* Quick Suggestions */}
          <div className="px-4 py-2 border-t border-gray-100 bg-[#FBF7EE] flex gap-2 overflow-x-auto shrink-0 scrollbar-none">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => handleSend(s)}
                className="whitespace-nowrap text-xs text-gray-600 bg-white hover:bg-amber-50 hover:text-amber-700 hover:border-amber-300 border border-gray-200 rounded-full px-3 py-1.5 transition active:scale-95 shrink-0"
              >
                {s}
              </button>
            ))}
          </div>

          {/* Input Panel */}
          <div className="p-3 border-t border-gray-200 bg-white flex gap-2 shrink-0 items-center">
            <input
              className="flex-1 border border-gray-200 rounded-full px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
              placeholder="Ask EcoBot about your recycling..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              disabled={isTyping}
            />
            <button
              type="button"
              onClick={() => handleSend()}
              disabled={!input.trim() || isTyping}
              className="bg-amber-400 hover:bg-amber-300 text-[#0B2F2C] w-10 h-10 rounded-full flex items-center justify-center disabled:opacity-40 transition-all active:scale-95 shrink-0 shadow-sm"
            >
              <Send size={15} />
            </button>
          </div>
        </div>
      )}
    </>
  );
}
