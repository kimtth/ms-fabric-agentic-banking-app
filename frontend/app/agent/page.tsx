'use client'

import { useState, useRef, useEffect } from 'react'
import useSWR from 'swr'
import { Shell } from '@/components/shell'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

const API = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
const USER_ID = 'demo_user'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function AgentPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string>('')
  const [selectedSession, setSelectedSession] = useState<string>('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const fetcher = async <T,>(url: string) => {
    const res = await fetch(url)
    if (!res.ok) throw new Error(await res.text())
    return (await res.json()) as T
  }

  // Sessions list
  const { data: sessions, mutate: refreshSessions, isValidating: sessionsLoading } = useSWR<{ sessions: { session_id: string; user_id: string; updated_at: string }[] }>(
    `${API}/agent/sessions?user_id=${encodeURIComponent(USER_ID)}`,
    fetcher,
    { refreshInterval: 30000, revalidateOnFocus: false }
  )

  useEffect(() => {
    const id = `s_${Date.now().toString(36)}`
    setSessionId(id)
    setSelectedSession(id)
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const res = await fetch(`${API}/agent/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, user_id: USER_ID, message: userMessage })
      })
      const data = await res.json()
      setMessages((prev) => [...prev, { role: 'assistant', content: data.response || data.error || 'No response' }])
      await refreshSessions()
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Connection error' }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const newSession = () => {
    setMessages([])
    const id = `s_${Date.now().toString(36)}`
    setSessionId(id)
    setSelectedSession(id)
  }

  const loadSession = async (sid: string) => {
    setSelectedSession(sid)
    setSessionId(sid)
    try {
      const res = await fetch(`${API}/agent/history/${encodeURIComponent(sid)}`)
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json() as { messages: Message[] }
      setMessages(data.messages)
    } catch {
      // ignore
    }
  }

  const deleteSession = async (sid: string) => {
    if (!confirm('Delete this session and its messages?')) return
    try {
      const res = await fetch(`${API}/agent/session/${encodeURIComponent(sid)}`, { method: 'DELETE' })
      if (!res.ok) throw new Error(await res.text())
      await refreshSessions()
      if (sid === sessionId) newSession()
    } catch {
      // ignore
    }
  }

  return (
    <Shell activeHref="/agent">
      <Card className="flex h-[calc(100vh-180px)] flex-col border-l-4 border-l-blue-500 bg-blue-50/40">
        <CardHeader className="flex-row items-center justify-between border-b border-blue-100 py-3">
          <CardTitle className="text-base text-blue-700">Banking Agent</CardTitle>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={newSession} className="border-blue-200 text-blue-800 bg-blue-50 hover:bg-blue-100">New Chat</Button>
            <Button variant="secondary" onClick={() => refreshSessions()} className="border-blue-200 text-blue-800 bg-blue-50 hover:bg-blue-100">Refresh</Button>
          </div>
        </CardHeader>
        <CardContent className="flex flex-1 overflow-hidden p-0">
          {/* Sidebar: Sessions */}
          <div className="hidden w-72 shrink-0 border-r border-blue-100 p-3 md:block">
            <div className="mb-2 text-xs font-semibold text-blue-800">Sessions</div>
            <div className="flex flex-col gap-2 overflow-y-auto pr-1" style={{ maxHeight: 'calc(100vh - 240px)' }}>
              {sessionsLoading && <div className="text-xs text-blue-600">Loading...</div>}
              {(sessions?.sessions ?? []).map((s) => (
                <div key={s.session_id} className={`flex items-center justify-between rounded-md border p-2 text-sm ${selectedSession === s.session_id ? 'bg-blue-100 border-blue-300' : 'bg-white'}`}>
                  <button onClick={() => loadSession(s.session_id)} className="truncate text-left text-blue-900 hover:underline">
                    {s.session_id}
                    <div className="text-[10px] text-blue-700/70">{new Date(s.updated_at).toLocaleString()}</div>
                  </button>
                  <button onClick={() => deleteSession(s.session_id)} className="text-xs text-red-600 hover:underline">Delete</button>
                </div>
              ))}
              {(sessions?.sessions?.length ?? 0) === 0 && <div className="text-xs text-blue-700/70">No sessions yet</div>}
            </div>
          </div>

          {/* Chat panel */}
          <div className="flex flex-1 flex-col overflow-hidden">
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.length === 0 && (
              <div className="mt-8 text-center text-blue-600/70">
                <p className="text-sm">Ask me about your banking data</p>
                <p className="mt-1 text-xs">e.g., &quot;Show my accounts&quot; or &quot;What are my recent transactions?&quot;</p>
              </div>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
                  msg.role === 'user' ? 'bg-blue-700 text-white' : 'bg-white text-blue-900 border border-blue-100'
                }`}>
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="rounded-lg bg-white px-3 py-2 text-sm text-blue-600">Thinking...</div>
              </div>
            )}
            <div ref={messagesEndRef} />
            </div>
            <div className="flex gap-2 border-t border-blue-100 p-3">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={`Session: ${sessionId} — Type your message...`}
                disabled={loading}
                className="flex-1"
              />
              <Button onClick={sendMessage} disabled={loading || !input.trim()} className="bg-blue-700 hover:bg-blue-800">
                Send
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </Shell>
  )
}
