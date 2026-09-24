'use client';
import { useState, type FormEvent } from 'react';
import { ArrowRight, LoaderCircle, ShoppingBag } from 'lucide-react';
import { api, setSession, type User } from '@/lib/api';
export default function AuthForm({ onSuccess }: { onSuccess: (user: User) => void }) {
  const [register, setRegister] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError('');
    const values = Object.fromEntries(new FormData(event.currentTarget));
    try {
      if (register) await api('auth/register/', { method: 'POST', body: JSON.stringify(values) });
      const tokens = await api<{ access: string; refresh: string }>('auth/login/', { method: 'POST', body: JSON.stringify({ username: values.username, password: values.password }) });
      setSession(tokens);
      onSuccess(await api<User>('auth/me/'));
    } catch (e) { setError(e instanceof Error ? e.message : 'Please try again.'); }
    finally { setBusy(false); }
  }
  return <>
    <div className="auth-intro">
      <span className="auth-symbol"><ShoppingBag size={30}/></span>
      <h3>{register ? 'Your next chapter starts here.' : 'Good to have you back.'}</h3>
      <p>{register ? 'Join a community that gives good things a second life.' : 'Sign in to save your finds and meet your next favorite thing.'}</p>
    </div>
    <form onSubmit={submit} className="form-stack" key={String(register)}>
      <label>Username<input name="username" autoComplete="username" required maxLength={150} placeholder="Your username"/></label>
      {register && <>
        <div className="form-row">
          <label>First name<input name="first_name" type="text" autoComplete="given-name" required maxLength={150} placeholder="First name"/></label>
          <label>Last name<input name="last_name" type="text" autoComplete="family-name" required maxLength={150} placeholder="Last name"/></label>
        </div>
        <label>Email address<input name="email" type="email" autoComplete="email" required maxLength={254} placeholder="you@university.edu"/></label>
      </>}
      <label>Password<input name="password" type="password" autoComplete={register ? 'new-password' : 'current-password'} minLength={register ? 8 : 1} required placeholder={register ? 'At least 8 characters' : 'Your password'}/></label>
      {error && <p className="form-error" role="alert">{error}</p>}
      <button className="button primary full" disabled={busy}>{busy ? <LoaderCircle className="spin" size={18}/> : <>{register ? 'Create account' : 'Sign in'}<ArrowRight size={17}/></>}</button>
    </form>
    <p className="auth-switch">{register ? 'Already part of UniMart?' : 'New around here?'} <button type="button" onClick={() => { setRegister(!register); setError(''); }}>{register ? 'Sign in' : 'Create an account'}</button></p>
  </>;
}
