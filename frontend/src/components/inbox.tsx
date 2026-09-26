'use client';
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { ArrowLeft, LoaderCircle, MessageCircle, Send } from 'lucide-react';
import { allPages, api, type Conversation, type Message, type User } from '@/lib/api';
export default function Inbox({ user, initial }: { user: User; initial?: Conversation }) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [active, setActive] = useState<Conversation | undefined>(initial);
  const [messages, setMessages] = useState<Message[]>([]);
  const [showArchived, setShowArchived] = useState(false);
  const visibleConversations = conversations.filter(item => Boolean(item.archived) === showArchived);
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const bottom = useRef<HTMLDivElement>(null);
  useEffect(() => { let cancelled = false; allPages<Conversation>('conversations/').then(data => { if (!cancelled) setConversations(data); }).catch(e => { if (!cancelled) setError(e.message); }).finally(() => { if (!cancelled) setLoading(false); }); return () => { cancelled = true; }; }, []);
  useEffect(() => {
    if (!active) return;
    let cancelled = false;
    setMessages([]); setError('');
    const load = () => allPages<Message>(`conversations/${active.id}/messages/`).then(data => { if (!cancelled) { setMessages(data.sort((a, b) => a.created_at.localeCompare(b.created_at))); setError(''); } }).catch(e => { if (!cancelled) setError(e.message); });
    void load(); const timer = setInterval(load, 5000);
    return () => { cancelled = true; clearInterval(timer); };
  }, [active]);
  useEffect(() => { bottom.current?.scrollIntoView({ block: 'nearest' }); }, [messages.length]);
  async function toggleArchive() {
    if (!active) return;
    setBusy(true); setError('');
    try {
      const updated = await api<Conversation>(`conversations/${active.id}/archive/`, { method: active.archived ? 'DELETE' : 'POST' });
      setConversations(previous => [...previous.filter(item => item.id !== updated.id), updated]);
      setActive(undefined);
    } catch (e) { setError(e instanceof Error ? e.message : 'Could not update conversation.'); }
    finally { setBusy(false); }
  }
  async function send(event: FormEvent) {
    event.preventDefault(); if (!active || !text.trim()) return; setBusy(true); setError('');
    try { const message = await api<Message>(`conversations/${active.id}/messages/`, { method: 'POST', body: JSON.stringify({ content: text.trim() }) }); setMessages(previous => previous.some(m => m.id === message.id) ? previous : [...previous, message]); setText(''); }
    catch (e) { setError(e instanceof Error ? e.message : 'Could not send message.'); }
    finally { setBusy(false); }
  }
  return <div className="inbox">{!active && <div className="trade-actions"><button className="text-button" aria-pressed={!showArchived} onClick={() => setShowArchived(false)}>Inbox</button><button className="text-button" aria-pressed={showArchived} onClick={() => setShowArchived(true)}>Archived</button></div>}{error && <p className="form-error" role="alert">{error}</p>}{active ? <><button className="text-button chat-back" onClick={() => setActive(undefined)}><ArrowLeft size={16}/>All conversations</button><div className="chat-title"><span className="avatar">{(active.buyer.id === user.id ? active.seller : active.buyer).username[0].toUpperCase()}</span><div><strong>{(active.buyer.id === user.id ? active.seller : active.buyer).username}</strong><p>{active.listing_title}</p></div></div><button className="text-button" disabled={busy} onClick={toggleArchive}>{active.archived ? 'Restore to inbox' : 'Archive conversation'}</button><p className="fine-print">Archiving hides this chat only for you. Your message history is preserved.</p><div className="messages">{!messages.length && <p className="chat-hint">Start with a hello. Ask about the item or arrange a pickup.</p>}{messages.map(message => <div key={message.id} className={`message ${message.sender.id === user.id ? 'mine' : ''}`}><p>{message.content}</p><time>{new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</time></div>)}<div ref={bottom}/></div><form onSubmit={send} className="message-compose"><input aria-label="Message" value={text} onChange={e => setText(e.target.value)} maxLength={2000} placeholder="Write a message…" required/><button className="icon-button primary" aria-label="Send message" disabled={busy || !text.trim()}>{busy ? <LoaderCircle size={19} className="spin"/> : <Send size={19}/>}</button></form></> : loading ? <div className="empty-state"><LoaderCircle className="spin"/></div> : visibleConversations.length ? <div className="conversation-list">{visibleConversations.map(conversation => <button key={conversation.id} onClick={() => setActive(conversation)}><span className="avatar">{(conversation.buyer.id === user.id ? conversation.seller : conversation.buyer).username[0].toUpperCase()}</span><span><strong>{(conversation.buyer.id === user.id ? conversation.seller : conversation.buyer).username}</strong><small>{conversation.listing_title}</small></span><MessageCircle size={19}/></button>)}</div> : <div className="empty-state"><MessageCircle size={35}/><h3>{showArchived ? 'No archived conversations.' : 'Your next connection starts here.'}</h3><p>{showArchived ? 'Conversations you archive will appear here.' : 'Open an item and message its seller to start a conversation.'}</p></div>}</div>;
}
