"use client";

import React, { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Message {
  id: string;
  sender: 'user' | 'bot';
  text: string;
}

export const ChatWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', sender: 'bot', text: 'Hello! I am AlgoTrade AI. How can I assist you with your portfolio or navigation today?' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMsg: Message = { id: Date.now().toString(), sender: 'user', text: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://206.189.129.232:8000';
      const response = await fetch(`${baseUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input })
      });

      const data = await response.json();
      
      if (data.type === 'action') {
        const action = data.data;
        if (action.action === 'NAVIGATE') {
          const target = action.target.toLowerCase();
          setMessages(prev => [...prev, { id: Date.now().toString(), sender: 'bot', text: `Navigating you to ${target}...` }]);
          if (target === 'holdings' || target === 'portfolio') {
            router.push('/holdings');
          } else if (target === 'dashboard' || target === 'home') {
            router.push('/');
          } else if (target === 'profile' || target === 'settings') {
            router.push('/profile');
          }
        }
      } else {
        setMessages(prev => [...prev, { id: Date.now().toString(), sender: 'bot', text: data.message || "Sorry, I didn't understand." }]);
      }
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { id: Date.now().toString(), sender: 'bot', text: "Error connecting to AI backend." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <style>{`
        .markdown-body p { margin-bottom: 8px; }
        .markdown-body p:last-child { margin-bottom: 0; }
        .markdown-body strong { font-weight: 600; color: #60A5FA; }
        .markdown-body em { font-style: italic; }
        .markdown-body ul { padding-left: 20px; margin-bottom: 8px; list-style-type: disc; }
        .markdown-body ol { padding-left: 20px; margin-bottom: 8px; list-style-type: decimal; }
        .markdown-body li { margin-bottom: 4px; }
        .markdown-body h1, .markdown-body h2, .markdown-body h3 { font-weight: 600; margin-bottom: 8px; margin-top: 12px; }
        .markdown-body code { background: rgba(0,0,0,0.3); padding: 2px 4px; border-radius: 4px; font-family: monospace; font-size: 12px; }
        .markdown-body pre { background: rgba(0,0,0,0.3); padding: 8px; border-radius: 6px; overflow-x: auto; margin-bottom: 8px; }
        .markdown-body pre code { background: transparent; padding: 0; }
      `}</style>
      {isOpen ? (
        <div style={{
          position: 'fixed', 
          bottom: '85px', 
          right: '16px', 
          zIndex: 9999,
          width: '350px',
          height: '500px',
          backgroundColor: 'rgba(15, 23, 42, 0.85)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          borderRadius: '16px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}>
          {/* Header */}
          <div style={{
            padding: '16px',
            borderBottom: '1px solid rgba(255,255,255,0.1)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: 'linear-gradient(to right, rgba(59, 130, 246, 0.2), rgba(147, 51, 234, 0.2))'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#10B981', boxShadow: '0 0 8px #10B981' }}></div>
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: '#fff' }}>AlgoTrade AI Copilot</h3>
            </div>
            <button 
              onClick={() => setIsOpen(false)}
              style={{ background: 'none', border: 'none', color: '#9CA3AF', cursor: 'pointer', fontSize: '20px' }}
            >
              &times;
            </button>
          </div>

          {/* Chat Messages */}
          <div style={{ flex: 1, padding: '16px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {messages.map((msg) => (
              <div key={msg.id} style={{ display: 'flex', justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start' }}>
                <div style={{
                  maxWidth: '85%',
                  padding: '10px 14px',
                  borderRadius: msg.sender === 'user' ? '16px 16px 0 16px' : '16px 16px 16px 0',
                  backgroundColor: msg.sender === 'user' ? '#3B82F6' : 'rgba(255, 255, 255, 0.05)',
                  color: '#fff',
                  fontSize: '14px',
                  lineHeight: '1.6'
                }}>
                  {msg.sender === 'user' ? (
                    msg.text
                  ) : (
                    <div className="markdown-body">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.text}
                      </ReactMarkdown>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div style={{
                  padding: '10px 14px',
                  borderRadius: '16px 16px 16px 0',
                  backgroundColor: 'rgba(255, 255, 255, 0.05)',
                  color: '#9CA3AF',
                  fontSize: '14px'
                }}>
                  Thinking...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div style={{ padding: '16px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input 
                type="text" 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Ask me anything..."
                style={{
                  flex: 1,
                  backgroundColor: 'rgba(0,0,0,0.2)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  padding: '10px 12px',
                  color: '#fff',
                  outline: 'none',
                  fontSize: '14px'
                }}
              />
              <button 
                onClick={handleSend}
                disabled={isLoading}
                style={{
                  backgroundColor: '#3B82F6',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '0 16px',
                  cursor: 'pointer',
                  fontWeight: 600
                }}
              >
                Send
              </button>
            </div>
          </div>
        </div>
      ) : (
        <motion.div
          initial={{ x: 20 }}
          animate={{ x: 0 }}
          whileHover={{ x: -2, background: 'rgba(30, 41, 59, 0.8)' }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setIsOpen(true)}
          style={{
            position: 'fixed',
            right: 0,
            bottom: '25%',
            width: '28px',
            height: '56px',
            background: 'rgba(15, 23, 42, 0.5)',
            backdropFilter: 'blur(8px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRight: 'none',
            borderRadius: '28px 0 0 28px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            boxShadow: '-2px 0 8px rgba(0, 0, 0, 0.2)',
            zIndex: 9999,
            transition: 'background 0.3s ease'
          }}
        >
          <span style={{
            fontSize: '14px',
            color: '#60A5FA',
            textShadow: '0 0 8px rgba(96, 165, 250, 0.8)'
          }}>
            ✦
          </span>
        </motion.div>
      )}
    </>
  );
};
