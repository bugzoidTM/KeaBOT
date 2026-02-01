import React, { useState, useRef, useEffect, useCallback } from 'react';
import { createChatSession, sendMessageStream } from '../services/geminiService';
import { Message } from '../types';
import { Chat } from '@google/genai';

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'init-1',
      role: 'model',
      text: 'KeaBOT is ready. Model: Gemini Flash configured. How can I help you today?',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [chatSession, setChatSession] = useState<Chat | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Initialize Chat
  useEffect(() => {
    const session = createChatSession();
    setChatSession(session);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle Textarea Auto-resize
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 192)}px`;
    }
  }, [inputValue]);

  const handleSendMessage = useCallback(async () => {
    if (!inputValue.trim() || !chatSession || isLoading) return;

    const userText = inputValue;
    setInputValue('');
    
    // Reset height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    const newUserMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      text: userText,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newUserMsg]);
    setIsLoading(true);

    const modelMsgId = (Date.now() + 1).toString();
    const newModelMsg: Message = {
      id: modelMsgId,
      role: 'model',
      text: '',
      timestamp: new Date(),
      isStreaming: true
    };

    setMessages(prev => [...prev, newModelMsg]);

    try {
      await sendMessageStream(chatSession, userText, (streamedText) => {
        setMessages(prev => prev.map(msg => 
          msg.id === modelMsgId ? { ...msg, text: streamedText } : msg
        ));
      });
    } catch (error) {
      setMessages(prev => prev.map(msg => 
        msg.id === modelMsgId ? { ...msg, text: "Sorry, I encountered an error processing your request." } : msg
      ));
    } finally {
      setMessages(prev => prev.map(msg => 
        msg.id === modelMsgId ? { ...msg, isStreaming: false } : msg
      ));
      setIsLoading(false);
    }
  }, [chatSession, inputValue, isLoading]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <main className="flex-1 flex flex-col h-full relative bg-[#101922]">
      {/* Sticky Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-[#233648] bg-[#101922]/80 backdrop-blur-md sticky top-0 z-10">
        <div className="flex items-center gap-3 text-white">
          <div className="size-8 rounded-lg bg-[#233648] flex items-center justify-center text-primary">
            <span className="material-symbols-outlined text-[20px]">smart_toy</span>
          </div>
          <div>
            <h2 className="text-base font-bold leading-tight tracking-tight flex items-center gap-2">
              KeaBOT v4
              <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-500 ring-1 ring-inset ring-emerald-500/20">Online</span>
            </h2>
            <p className="text-xs text-[#92adc9]">Gemini Flash • Context Window: 128k</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => setMessages([])}
            className="flex items-center justify-center gap-2 h-9 px-4 rounded-lg bg-[#1c2a38] hover:bg-[#233648] text-[#92adc9] hover:text-white text-sm font-medium transition-colors border border-transparent hover:border-[#354f68]"
          >
            <span className="material-symbols-outlined text-[18px]">delete</span>
            <span className="hidden sm:inline">Clear Chat</span>
          </button>
          <button className="flex items-center justify-center size-9 rounded-lg bg-[#1c2a38] hover:bg-[#233648] text-[#92adc9] hover:text-white transition-colors">
            <span className="material-symbols-outlined text-[20px]">more_vert</span>
          </button>
        </div>
      </header>

      {/* Chat Stream */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-10 md:px-20 lg:px-40 py-8 scroll-smooth" id="chat-container">
        <div className="max-w-[800px] mx-auto flex flex-col gap-8 pb-32">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex gap-4 group ${msg.role === 'user' ? 'flex-row-reverse items-end' : ''}`}>
              {/* Avatar */}
              <div 
                className={`bg-center bg-no-repeat aspect-square bg-cover rounded-full ${msg.role === 'model' ? 'size-10 mt-1 shadow-md' : 'size-8 mb-1 border border-[#233648]'} shrink-0`}
                style={{ 
                  backgroundImage: msg.role === 'model' 
                    ? 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuCT2sWcAUEJjkUR6NX3tFZ-ed8I1Rs2wIh_zO5a6RSPC9kJpfFXR5LNlwW0CeZ2TtESsg1Slr0putetOoe3Mme1-P_LwkOmN25A5EX3gIDlcYvwbhIZ1YTcR7MPO9IPkLyoS9HGX1Pc2B6ipdFGTv_uj_H_gflSnfNSrBCiUICnOwVr8Bhn1AfhJUc_vwD8lLQSnXNJIdamHd_MaEfchHBunnZ6enAkrQSdHMjFliCTvU3lYnqQRduY0OYig0pzQfoeEPOFfgNz2n4")'
                    : 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuDoYLYTrxvgzwySszGkaY9JmzSgsk_k5FwiIS1JOqDistG1AB6SUm3d_DIzGxXYbpt_YApu3MeHlyqLBqSr0xeRYr4wdKuB_JwtDq7FsSpKymDhjxKai6lO3dXwyE0N4WtLHte803ociwW2cC9s2aPwverTBs1A8F5r_v1V-kv7hNkmoFYJbpmoN2yD-azL_EizqPPmd7Pw7yTwXsSe6k1ZhSzlbGpQp1bLUCrMyHFhmiSwirtWByYKiiXeWfgUlk9FGzLqWtS0nAA")'
                }}
              ></div>

              {/* Content */}
              <div className={`flex flex-col gap-1 ${msg.role === 'user' ? 'items-end max-w-[85%]' : 'flex-1 max-w-[90%]'}`}>
                {msg.role === 'model' && (
                  <div className="flex items-baseline gap-3">
                    <span className="text-white text-sm font-bold">KeaBOT</span>
                    <span className="text-[#5a7690] text-xs">
                      {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                )}
                
                <div className={`
                  ${msg.role === 'user' 
                    ? 'px-5 py-3.5 bg-primary/90 text-white rounded-2xl rounded-tr-sm shadow-md' 
                    : 'text-[#e2e8f0]'} 
                  text-[15px] leading-relaxed whitespace-pre-wrap
                `}>
                  {msg.text}
                </div>
                
                {msg.role === 'user' && (
                   <span className="text-[#5a7690] text-[11px] pr-1 opacity-0 group-hover:opacity-100 transition-opacity">
                     {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                   </span>
                )}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex gap-4">
               <div 
                className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10 shadow-md shrink-0 mt-1"
                style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuCepE3x7iPHwFw1dAeyf9Iu5AImqijIArheIyZPmtbJRcsvjKOg7u8XkZC6-ENyxoXRgrwM-lXLwDeEliPaTcGeBEG9z_6ePLDVFMneXRlVwA9IuZC_x_n8YENi9nC041HCakiEancgrrN5L8EUIImmcKLcVnncQaJTHfbzDkkFjryaECdTCpyBC-knyWrr5260gB9dYnYlg17m-fXTjMPQJ2pXMWMFVWh6Hbznp5MZjMjfpNB1jnuPwNwNQUH04EP7z4MKRPOtjEk")' }}
               ></div>
               <div className="flex flex-col justify-center h-10">
                <div className="flex gap-1">
                  <div className="w-2 h-2 rounded-full bg-[#5a7690] animate-bounce"></div>
                  <div className="w-2 h-2 rounded-full bg-[#5a7690] animate-bounce [animation-delay:-0.15s]"></div>
                  <div className="w-2 h-2 rounded-full bg-[#5a7690] animate-bounce [animation-delay:-0.3s]"></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-[#101922] via-[#101922] to-transparent pointer-events-none z-20">
        <div className="max-w-[800px] mx-auto pointer-events-auto">
          <div className="relative bg-[#1c2a38]/80 backdrop-blur-xl border border-[#233648] rounded-xl shadow-2xl flex flex-col gap-2 p-3 transition-all focus-within:ring-2 focus-within:ring-primary/50 focus-within:border-primary/50">
            <textarea 
              ref={textareaRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              className="w-full bg-transparent text-white placeholder:text-[#5a7690] border-0 focus:ring-0 p-3 resize-none max-h-48 text-[15px] leading-relaxed scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-transparent"
              placeholder="Ask KeaBOT anything..."
              rows={1}
              style={{ minHeight: '52px' }}
            />
            <div className="flex items-center justify-between px-2 pb-1">
              <div className="flex items-center gap-1">
                <button className="size-8 flex items-center justify-center rounded-lg text-[#92adc9] hover:text-white hover:bg-[#233648] transition-colors" title="Attach file">
                  <span className="material-symbols-outlined text-[20px]">attach_file</span>
                </button>
                <button className="size-8 flex items-center justify-center rounded-lg text-[#92adc9] hover:text-white hover:bg-[#233648] transition-colors" title="Voice command">
                  <span className="material-symbols-outlined text-[20px]">mic</span>
                </button>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-[10px] text-[#5a7690] hidden sm:inline-block">Use <kbd className="font-sans px-1 py-0.5 rounded bg-[#233648] text-gray-300">Shift</kbd> + <kbd className="font-sans px-1 py-0.5 rounded bg-[#233648] text-gray-300">Enter</kbd> for new line</span>
                <button 
                  onClick={handleSendMessage}
                  disabled={isLoading || !inputValue.trim()}
                  className={`size-9 flex items-center justify-center rounded-lg bg-primary hover:bg-blue-600 text-white shadow-lg shadow-primary/20 transition-all hover:scale-105 active:scale-95 ${isLoading || !inputValue.trim() ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <span className="material-symbols-outlined text-[20px] ml-0.5">send</span>
                </button>
              </div>
            </div>
          </div>
          <div className="text-center mt-3">
            <p className="text-[10px] text-[#5a7690]">KeaBOT can make mistakes. Consider checking important information.</p>
          </div>
        </div>
      </div>
    </main>
  );
};

export default ChatPage;