import { useEffect, useRef, useState } from "react";
import { Bot, Send, Sparkles, Lightbulb } from "lucide-react";
import { useAuth } from "../../../context/AuthContext";
import { ecoBotReply, ECOBOT_SUGGESTIONS } from "../../../lib/ecobot";

const PRO_TIPS = [
  "Rinse containers before putting them out — it keeps the whole batch cleaner and easier to recycle.",
  "Flatten cardboard boxes so pickups take less room and stack better on the collection route.",
  "Keep e-waste separate from daily waste — batteries and chargers need their own pickup.",
  "Compost wet kitchen waste at home if you can — it keeps the smelliest waste out of your bags entirely.",
];

export default function EcoBotChat() {
  const { user } = useAuth();
  const firstName = user?.name?.split(" ")[0] || "there";
  const hour = new Date().getHours();
  const greetingWord = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: `${greetingWord}, ${firstName}. I'm EcoBot — your recycling concierge. How can I help you today?`,
    },
  ]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const bottom = useRef(null);
  const [proTip] = useState(() => PRO_TIPS[Math.floor(Math.random() * PRO_TIPS.length)]);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  const send = (text) => {
    const msg = (text ?? input).trim();
    if (!msg) return;
    setMessages((p) => [...p, { role: "user", text: msg }]);
    setInput("");
    setTyping(true);
    setTimeout(() => {
      setMessages((p) => [...p, { role: "bot", text: ecoBotReply(msg) }]);
      setTyping(false);
    }, 550);
  };

  return (
    <div className="fade-in">
      {/* Page header */}
      <div className="mb-5">
        <p className="text-[10px] font-mono-civic uppercase tracking-widest text-gray-400">
          Concierge
        </p>
        <h1 className="font-display text-2xl font-medium text-[#14171F] mt-0.5">EcoBot chat</h1>
      </div>

      <div className="grid lg:grid-cols-[2fr_1fr] gap-4 items-start">
        {/* Chat panel */}
        <div className="bg-white rounded-3xl border border-gray-100 shadow-soft flex flex-col h-[65vh] min-h-[420px] overflow-hidden">
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`flex ${m.role === "user" ? "justify-end" : "justify-start"} rise-in`}
              >
                {m.role === "bot" && (
                  <div className="w-8 h-8 rounded-full bg-amber-400 text-[#0B2F2C] flex items-center justify-center mr-2 shrink-0">
                    <Bot size={15} />
                  </div>
                )}
                <div
                  className={`max-w-[75%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
                    m.role === "user"
                      ? "bg-[#0B2F2C] text-white rounded-br-sm"
                      : "bg-[#F3EEE1] text-gray-700 rounded-bl-sm"
                  }`}
                >
                  {m.text}
                </div>
                {m.role === "user" && (
                  <div className="w-8 h-8 rounded-full bg-[#0B2F2C] text-white flex items-center justify-center ml-2 shrink-0 text-xs font-semibold">
                    {user?.name?.[0]?.toUpperCase() || "R"}
                  </div>
                )}
              </div>
            ))}
            {typing && (
              <div className="flex items-center gap-2 rise-in">
                <div className="w-8 h-8 rounded-full bg-amber-400 text-[#0B2F2C] flex items-center justify-center shrink-0">
                  <Bot size={15} />
                </div>
                <div className="bg-[#F3EEE1] rounded-2xl rounded-bl-sm px-4 py-3 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-gray-300 animate-pulse-slow" />
                  <span
                    className="w-1.5 h-1.5 rounded-full bg-gray-300 animate-pulse-slow"
                    style={{ animationDelay: "0.2s" }}
                  />
                  <span
                    className="w-1.5 h-1.5 rounded-full bg-gray-300 animate-pulse-slow"
                    style={{ animationDelay: "0.4s" }}
                  />
                </div>
              </div>
            )}
            <div ref={bottom} />
          </div>

          <div className="border-t border-gray-100 p-4 flex gap-2">
            <input
              className="flex-1 border border-gray-200 rounded-full px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
              placeholder="Ask EcoBot anything about your recycling…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
            />
            <button
              type="button"
              onClick={() => send()}
              disabled={!input.trim()}
              className="bg-amber-400 hover:bg-amber-300 text-[#0B2F2C] w-11 h-11 rounded-full flex items-center justify-center disabled:opacity-40 transition shrink-0"
            >
              <Send size={16} />
            </button>
          </div>
        </div>

        {/* Sidebar: suggestions + tip */}
        <div className="space-y-4">
          <div className="bg-white rounded-3xl border border-gray-100 shadow-soft p-5">
            <p className="flex items-center gap-1.5 text-[10px] font-mono-civic uppercase tracking-widest text-gray-400 mb-3">
              <Sparkles size={11} className="text-amber-400" /> Try asking
            </p>
            <div className="space-y-2">
              {ECOBOT_SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => send(s)}
                  className="w-full text-left text-sm text-gray-600 bg-[#FBF7EE] hover:bg-[#F3EEE1] border border-gray-100 rounded-xl px-3.5 py-2.5 transition"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-3xl border border-gray-100 shadow-soft p-5">
            <p className="flex items-center gap-1.5 text-[10px] font-mono-civic uppercase tracking-widest text-amber-500 mb-2">
              <Lightbulb size={11} /> Pro tip
            </p>
            <p className="text-sm text-gray-600 leading-relaxed">{proTip}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
