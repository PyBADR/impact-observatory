'use client'
import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Terminal, Send, Bot, ChevronRight } from 'lucide-react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
}

const presetQueries = [
  'Why did sentiment drop at t2?',
  'Who influenced the spread most?',
  'What if the government responds earlier?',
]

const mockResponses: Record<string, string> = {
  'default': 'Based on the simulation data, the primary driver was social media amplification by high-influence accounts. The negative sentiment spread rapidly through Twitter, peaking at t3 before government intervention at t4 began stabilizing public opinion.',
  'why': 'The sentiment drop at t2 was triggered by influencer amplification. When high-influence accounts engaged with the topic, their reach multiplied the negative signal by approximately 3.2x, causing the hashtag to trend nationally.',
  'who': 'The top influencer in this simulation was @gcc_analyst with an influence score of 0.85, followed by @saudi_voice (0.75). Together, they accounted for roughly 40% of the amplification during the peak phase.',
  'what if': 'If the government had responded at t2 instead of t4, our model predicts the peak visibility would have been 35% lower and sentiment recovery would have occurred approximately 18 hours earlier, reducing the overall spread level from "high" to "medium".',
}

interface ChatPanelProps {
  initialMessages?: Message[]
  scenarioId?: string
}

export default function ChatPanel({ initialMessages = [] }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, isTyping])

  const handleSend = (text?: string) => {
    const question = text || input
    if (!question.trim()) return

    const userMsg: Message = { id: `msg_${Date.now()}`, role: 'user', content: question }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsTyping(true)

    setTimeout(() => {
      const lowerQ = question.toLowerCase()
      let responseKey = 'default'
      if (lowerQ.includes('why') || lowerQ.includes('drop') || lowerQ.includes('sentiment')) responseKey = 'why'
      else if (lowerQ.includes('who') || lowerQ.includes('influenc')) responseKey = 'who'
      else if (lowerQ.includes('what if') || lowerQ.includes('earlier') || lowerQ.includes('government')) responseKey = 'what if'

      const assistantMsg: Message = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: mockResponses[responseKey],
      }
      setMessages(prev => [...prev, assistantMsg])
      setIsTyping(false)
    }, 1400)
  }

  return (
    <div className="bg-ds-surface rounded-ds-xl border border-ds-border overflow-hidden flex flex-col" style={{ maxHeight: '420px' }}>
      <div className="ds-panel-header flex-shrink-0">
        <div className="ds-panel-header-title">
          <Terminal size={14} className="text-ds-accent" />
          <span className="text-caption font-semibold text-ds-text tracking-tight">Analyst</span>
        </div>
        <span className="text-nano font-mono text-ds-text-dim uppercase tracking-wider">Query</span>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
        {messages.length === 0 && (
          <div className="py-4">
            <p className="text-nano text-ds-text-dim uppercase tracking-wider font-semibold mb-3">Suggested queries</p>
            <div className="space-y-1.5">
              {presetQueries.map((q, i) => (
                <button key={i} onClick={() => handleSend(q)} className="w-full text-left px-3.5 py-2.5 text-micro text-ds-text-secondary bg-ds-card border border-ds-border rounded-ds-lg hover:bg-ds-card-hover hover:border-ds-border-hover transition-all duration-200 flex items-center gap-2 group">
                  <ChevronRight size={12} className="text-ds-text-dim group-hover:text-ds-accent transition-colors flex-shrink-0" />
                  <span>{q}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <motion.div key={msg.id} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className={`flex gap-2.5 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'assistant' && (
              <div className="w-6 h-6 rounded-md bg-ds-accent/12 border border-ds-accent/20 flex items-center justify-center shrink-0 mt-0.5">
                <Bot size={11} className="text-ds-accent" />
              </div>
            )}
            <div className={`max-w-[85%] px-3.5 py-2.5 text-caption leading-relaxed ${
              msg.role === 'user'
                ? 'bg-ds-accent/10 text-ds-text border border-ds-accent/15 rounded-ds-lg rounded-br-md'
                : 'bg-ds-card text-ds-text-secondary border border-ds-border rounded-ds-lg rounded-bl-md'
            }`}>
              {msg.role === 'assistant' && (
                <span className="text-[9px] font-mono text-ds-accent/60 uppercase tracking-wider block mb-1">Analysis</span>
              )}
              {msg.content}
            </div>
          </motion.div>
        ))}

        {isTyping && (
          <div className="flex gap-2.5 items-start">
            <div className="w-6 h-6 rounded-md bg-ds-accent/12 border border-ds-accent/20 flex items-center justify-center">
              <Bot size={11} className="text-ds-accent" />
            </div>
            <div className="flex items-center gap-1.5 px-3.5 py-2.5 bg-ds-card border border-ds-border rounded-ds-lg rounded-bl-md">
              <span className="text-[9px] font-mono text-ds-accent/60 uppercase tracking-wider mr-1">Processing</span>
              <span className="w-1 h-1 rounded-full bg-ds-accent/50 animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1 h-1 rounded-full bg-ds-accent/50 animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1 h-1 rounded-full bg-ds-accent/50 animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-ds-border p-3 flex-shrink-0">
        <div className="flex items-center gap-2">
          <div className="flex-1 relative">
            <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-ds-accent/40 text-micro font-mono">{'>'}</span>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Query the simulation..."
              className="w-full bg-ds-card border border-ds-border rounded-ds-lg pl-7 pr-3.5 py-2.5 text-caption text-ds-text placeholder:text-ds-text-dim outline-none transition-all duration-200 focus:border-ds-accent/30 focus:shadow-[0_0_0_3px_rgba(91,123,248,0.06)] font-mono"
            />
          </div>
          <button
            onClick={() => handleSend()}
            disabled={!input.trim()}
            className="p-2.5 bg-ds-accent/12 text-ds-accent rounded-ds-lg border border-ds-accent/15 hover:bg-ds-accent/20 hover:border-ds-accent/25 transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <Send size={14} />
          </button>
        </div>
      </div>
    </div>
  )
    }
