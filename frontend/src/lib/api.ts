export type Category = { id: string; name: string; slug: string };
export type Person = { id: string; username: string; avatar?: string };
export type User = Person & { first_name: string; email: string };
export type Listing = { id: string; title: string; description: string; price: string; condition: string; status: string; category: string; category_name: string; seller: Person; images: { id: string; image: string }[]; created_at: string };
export type Saved = { id: string; listing: string; listing_detail: Listing };
export type Conversation = { archived: boolean; id: string; listing: string; listing_title: string; buyer: Person; seller: Person };
export type Message = { id: string; sender: Person; content: string; created_at: string };
const token = () => typeof window !== 'undefined' ? sessionStorage.getItem('unimart-access') : null;
export function setSession(tokens?: { access: string; refresh: string }) {
  if (tokens) { sessionStorage.setItem('unimart-access', tokens.access); sessionStorage.setItem('unimart-refresh', tokens.refresh); }
  else { sessionStorage.removeItem('unimart-access'); sessionStorage.removeItem('unimart-refresh'); }
}
let refreshing: Promise<boolean> | null = null;
async function refreshSession() {
  if (!refreshing) refreshing = (async () => {
    const refresh = sessionStorage.getItem('unimart-refresh');
    if (!refresh) return false;
    try {
      const response = await fetch('/api/auth/refresh/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh }), signal: AbortSignal.timeout(10000) });
      if (!response.ok) return false;
      const data = await response.json();
      setSession({ access: data.access, refresh: data.refresh || refresh });
      return true;
    } catch { return false; }
  })().finally(() => { refreshing = null; });
  return refreshing;
}
export async function api<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  if (token()) headers.set('Authorization', `Bearer ${token()}`);
  const response = await fetch(`/api/${path}`, { ...options, headers, signal: options.signal ?? AbortSignal.timeout(12000) });
  if (response.status === 401 && token() && retry) {
    if (await refreshSession()) return api<T>(path, options, false);
    setSession(); window.dispatchEvent(new Event('unimart-session-expired'));
  }
  if (response.status === 204) return undefined as T;
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(data?.detail || (data ? Object.entries(data).map(([key, value]) => `${key.replaceAll('_', ' ')}: ${Array.isArray(value) ? value.join(' ') : value}`).join(' ') : 'UniMart could not connect. Please try again.'));
  return data as T;
}
export async function allPages<T>(path: string): Promise<T[]> {
  const rows: T[] = [];
  let next: string | null = path;
  while (next) {
    const data: T[] | { results: T[]; next: string | null } = await api(next);
    if (Array.isArray(data)) return [...rows, ...data];
    rows.push(...data.results);
    next = data.next ? data.next.split('/api/')[1] : null;
  }
  return rows;
}
export const money = (price: string | number) => `Rs. ${Number(price).toLocaleString('en-NP', { maximumFractionDigits: 0 })}`;
export const conditionName = (condition: string) => ({ new: 'Brand new', like_new: 'Like new', good: 'Good', fair: 'Fair', poor: 'Well loved' }[condition] || condition);
export function imageUrl(url?: string) { if (!url) return '/images/placeholder.svg'; if (url.includes('/media/')) return `/media/${url.split('/media/')[1]}`; return url; }
