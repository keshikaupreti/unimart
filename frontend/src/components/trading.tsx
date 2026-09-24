'use client';

import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { allPages, api, type Conversation, type Listing, type Person, type User } from '@/lib/api';

type Location = { id: string; name: string; description: string };
type Sale = { id: string; listing: string; listing_title: string; buyer: Person; seller: Person; status: string; meetup_time: string; meetup_location_detail: Location };
type Review = { id: string; transaction: string; reviewer: Person; rating: number; comment: string };
type Case = { id: string; transaction?: string; listing_title?: string; reason: string; description: string; status: string; admin_note: string };
const errorMessage = (error: unknown) => error instanceof Error ? error.message : 'Something went wrong. Please try again.';
const label = (value: string) => value.replaceAll('_', ' ');
const disputeReasons = ['item_not_as_described', 'buyer_no_show', 'seller_no_show', 'damaged_item', 'payment', 'harassment', 'other'];
const reportReasons = ['illegal', 'scam', 'spam', 'harassment', 'misleading', 'other'];

export function PurchaseForm({ listing, onSuccess }: { listing: Listing; onSuccess: () => void }) {
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try { setLocations(await allPages<Location>('meetup-locations/')); }
    catch (error) { setError(errorMessage(error)); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setBusy(true);
    const form = new FormData(event.currentTarget);
    try {
      const date = new Date(String(form.get('meetup_time')));
      if (!Number.isFinite(date.getTime()) || date.getTime() <= Date.now()) throw new Error('Choose a meetup time in the future.');
      await api('transactions/', { method: 'POST', body: JSON.stringify({ listing: listing.id, meetup_location: form.get('meetup_location'), meetup_time: date.toISOString() }) });
      onSuccess();
    } catch (error) { setError(errorMessage(error)); }
    finally { setBusy(false); }
  }
  return <form className="form-stack" onSubmit={submit}>
    <p>Request to buy <strong>{listing.title}</strong>. The seller will confirm your meetup. Pay the seller when you meet.</p>
    {loading ? <p role="status">Loading meetup locations…</p> : <>
      <label>Meetup location<select name="meetup_location" required defaultValue=""><option value="" disabled>Choose a public meeting place</option>{locations.map(location => <option key={location.id} value={location.id}>{location.name}{location.description ? ` — ${location.description}` : ''}</option>)}</select></label>
      {!locations.length && !error && <p>No meetup locations are available yet. Please contact the marketplace administrator.</p>}
      <label>Meetup time (your local time)<input name="meetup_time" type="datetime-local" required/></label>
    </>}
    {error && <div><p className="form-error" role="alert">{error}</p><button type="button" className="text-button" onClick={load}>Reload locations</button></div>}
    <button className="button primary full" disabled={busy || loading || !locations.length}>{busy ? 'Sending…' : 'Send purchase request'}</button>
  </form>;
}

export function ReportForm({ listing, onSuccess }: { listing: Listing; onSuccess: () => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError('');
    const form = new FormData(event.currentTarget);
    const target = form.get('target') === 'seller' ? { reported_user: listing.seller.id } : { listing: listing.id };
    try { await api('reports/', { method: 'POST', body: JSON.stringify({ ...target, reason: form.get('reason'), description: form.get('description') }) }); onSuccess(); }
    catch (error) { setError(errorMessage(error)); }
    finally { setBusy(false); }
  }
  return <form className="form-stack" onSubmit={submit}>
    <label>Report<select name="target"><option value="listing">Listing: {listing.title}</option><option value="seller">Seller: {listing.seller.username}</option></select></label>
    <label>Reason<select name="reason">{reportReasons.map(reason => <option key={reason} value={reason}>{label(reason)}</option>)}</select></label>
    <label>What happened?<textarea name="description" required rows={4}/></label>
    {error && <p className="form-error" role="alert">{error}</p>}
    <button className="button primary" disabled={busy}>{busy ? 'Sending…' : 'Submit report'}</button>
  </form>;
}

export function SellerReviews({ seller }: { seller: Person }) {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true;
    setLoading(true); setError('');
    allPages<Review>(`reviews/?reviewed_user=${seller.id}`).then(rows => { if (active) setReviews(rows); }).catch(error => { if (active) setError(errorMessage(error)); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [seller.id]);
  return <section className="trade-section" aria-label="Seller reviews"><h4>Seller reviews</h4>
    {loading ? <p>Loading reviews…</p> : error ? <p role="alert">{error}</p> : reviews.length ? <>
      <p>{(reviews.reduce((sum, review) => sum + review.rating, 0) / reviews.length).toFixed(1)} / 5 · {reviews.length} reviews</p>
      {reviews.map(review => <blockquote key={review.id}><strong>{review.reviewer.username} · {review.rating}/5</strong><p>{review.comment || 'No comment provided.'}</p></blockquote>)}
    </> : <p>No reviews yet.</p>}
  </section>;
}

export function Activity({ user, onChange, onConversation }: { user: User; onChange: () => void; onConversation: (conversation: Conversation) => void }) {
  const [sales, setSales] = useState<Sale[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [disputes, setDisputes] = useState<Case[]>([]);
  const [reports, setReports] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState<{ id: string; kind: 'review' | 'dispute' } | null>(null);
  const load = useCallback(async () => {
    const [sales, reviews, disputes, reports] = await Promise.all([
      allPages<Sale>('transactions/'), allPages<Review>(`reviews/?reviewer=${user.id}`), allPages<Case>('disputes/'), allPages<Case>('reports/'),
    ]);
    setSales(sales); setReviews(reviews); setDisputes(disputes); setReports(reports);
  }, [user.id]);
  const reload = useCallback(async () => {
    setLoading(true); setError('');
    try { await load(); } catch (error) { setError(errorMessage(error)); }
    finally { setLoading(false); }
  }, [load]);
  useEffect(() => { void reload(); }, [reload]);
  async function act(path: string, body: Record<string, unknown> = {}) {
    setBusy(true); setError(''); setNotice('');
    try {
      await api(path, { method: 'POST', body: JSON.stringify(body) });
      setForm(null); setNotice('Saved successfully.'); onChange();
      try { await load(); } catch { setError('Your change was saved, but the activity could not refresh. Refresh before making another change.'); }
    } catch (error) { setError(errorMessage(error)); }
    finally { setBusy(false); }
  }
  async function openConversation(sale: Sale) {
    setBusy(true); setError('');
    try { onConversation(await api<Conversation>(`transactions/${sale.id}/conversation/`, { method: 'POST' })); }
    catch (error) { setError(errorMessage(error)); }
    finally { setBusy(false); }
  }
  function submit(event: FormEvent<HTMLFormElement>, sale: Sale) {
    event.preventDefault(); const data = new FormData(event.currentTarget);
    if (form?.kind === 'review') void act('reviews/', { transaction: sale.id, rating: Number(data.get('rating')), comment: data.get('comment') });
    else void act('disputes/', { transaction: sale.id, reason: data.get('reason'), description: data.get('description') });
  }
  return <div className="form-stack">
    <button className="text-button" onClick={reload} disabled={busy || loading}>Refresh activity</button>
    {error && <p role="alert" className="form-error">{error}</p>}{notice && <p role="status">{notice}</p>}
    {loading ? <p role="status">Loading your activity…</p> : <>
      <h3>Purchases and sales</h3>{!sales.length && <p>No purchase requests yet. Open a listing to request a meetup.</p>}
      {sales.map(sale => {
        const seller = sale.seller.id === user.id;
        const reviewed = reviews.some(review => review.transaction === sale.id);
        const activeDispute = disputes.some(dispute => dispute.transaction === sale.id && ['open', 'under_review'].includes(dispute.status));
        return <article key={sale.id} className="trade-card">
          <h4>{sale.listing_title}</h4><p>{seller ? `Selling to ${sale.buyer.username}` : `Buying from ${sale.seller.username}`} · <strong>{label(sale.status)}</strong></p>
          <p>{sale.meetup_location_detail.name} · {new Date(sale.meetup_time).toLocaleString()}</p>
          <div className="trade-actions">
            {['accepted', 'completed'].includes(sale.status) && (seller || sale.buyer.id === user.id) && <button className="button secondary" disabled={busy} onClick={() => openConversation(sale)}>Message {seller ? 'buyer' : 'seller'}</button>}
            {sale.status === 'requested' && seller && <><button className="button primary" disabled={busy} onClick={() => act(`transactions/${sale.id}/accept/`)}>Accept request</button><button className="button secondary" disabled={busy} onClick={() => act(`transactions/${sale.id}/reject/`)}>Reject request</button></>}
            {((sale.status === 'requested' && !seller) || sale.status === 'accepted') && <button className="button secondary" disabled={busy} onClick={() => act(`transactions/${sale.id}/cancel/`)}>Cancel request</button>}
            {sale.status === 'accepted' && seller && <button className="button primary" disabled={busy} onClick={() => act(`transactions/${sale.id}/complete/`)}>Confirm handover complete</button>}
            {sale.status === 'completed' && !reviewed && <button className="button secondary" disabled={busy} onClick={() => setForm({ id: sale.id, kind: 'review' })}>Leave a review</button>}
            {reviewed && <span>Review submitted</span>}
            {['accepted', 'completed'].includes(sale.status) && !activeDispute && <button className="text-button" disabled={busy} onClick={() => setForm({ id: sale.id, kind: 'dispute' })}>Open a dispute</button>}
            {activeDispute && <span>Dispute submitted.</span>}
          </div>
          {form?.id === sale.id && <form className="form-stack trade-section" onSubmit={event => submit(event, sale)}>
            {form.kind === 'review' ? <><label>Rating<select name="rating" defaultValue="5">{[5, 4, 3, 2, 1].map(value => <option key={value} value={value}>{value} / 5</option>)}</select></label><label>Comment<textarea name="comment" rows={3}/></label></> : <><label>Reason<select name="reason">{disputeReasons.map(reason => <option key={reason} value={reason}>{label(reason)}</option>)}</select></label><label>Describe the issue<textarea name="description" rows={3} required/></label></>}
            <button className="button primary" disabled={busy}>{busy ? 'Saving…' : form.kind === 'review' ? 'Submit review' : 'Submit dispute'}</button><button className="text-button" type="button" disabled={busy} onClick={() => setForm(null)}>Cancel</button>
          </form>}
        </article>;
      })}
      <h3>Disputes</h3>{!disputes.length && <p>No disputes.</p>}{disputes.map(item => <CaseCard key={item.id} item={item}/>)}
      <h3>Your reports</h3>{!reports.length && <p>No reports.</p>}{reports.map(item => <CaseCard key={item.id} item={item}/>)}
    </>}
  </div>;
}
function CaseCard({ item }: { item: Case }) {
  return <article className="trade-card"><h4>{item.listing_title || label(item.reason)}</h4><p>{label(item.reason)} · <strong>{label(item.status)}</strong></p><p>{item.description}</p>{item.admin_note && <p><strong>Moderator response:</strong> {item.admin_note}</p>}</article>;
}
