'use client';
import { useState, type FormEvent } from 'react';
import { ArrowRight, ImagePlus, LoaderCircle } from 'lucide-react';
import { api, type Category, type Listing } from '@/lib/api';
export default function SellForm({ categories, onSuccess }: { categories: Category[]; onSuccess: (listing: Listing, warning?: string) => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [fileName, setFileName] = useState('Add a photo');
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError('');
    const form = new FormData(event.currentTarget);
    try {
      let listing = await api<Listing>('listings/', { method: 'POST', body: JSON.stringify({ title: form.get('title'), description: form.get('description'), price: form.get('price'), category: form.get('category'), condition: form.get('condition') }) });
      const photo = form.get('photo') as File;
      if (photo?.size) {
        try { const upload = new FormData(); upload.set('listing', listing.id); upload.set('image', photo); const image = await api<Listing['images'][number]>('listing-images/', { method: 'POST', body: upload }); listing = { ...listing, images: [image] }; }
        catch { onSuccess(listing, 'Your listing is published, but its photo could not upload.'); return; }
      }
      onSuccess(listing);
    } catch (e) { setError(e instanceof Error ? e.message : 'Could not publish your listing.'); }
    finally { setBusy(false); }
  }
  return <form className="form-stack" onSubmit={submit}><label className="upload-zone"><ImagePlus size={29}/><strong>{fileName}</strong><span>Choose a JPG, PNG, or WebP · up to 10 MB</span><input type="file" name="photo" accept="image/jpeg,image/png,image/webp" onChange={e => { const file = e.target.files?.[0]; if (file && file.size > 10 * 1024 * 1024) { e.target.value = ''; setError('Please choose an image smaller than 10 MB.'); setFileName('Add a photo'); } else { setFileName(file?.name || 'Add a photo'); setError(''); } }}/></label><label>Give it a name<input name="title" required maxLength={150} placeholder="e.g. MacBook Air M2, midnight"/></label><div className="form-row"><label>Category<select name="category" required defaultValue=""><option value="" disabled>Choose a category</option>{categories.map(category => <option key={category.id} value={category.id}>{category.name}</option>)}</select></label><label>Condition<select name="condition" defaultValue="like_new"><option value="new">Brand new</option><option value="like_new">Like new</option><option value="good">Good</option><option value="fair">Fair</option><option value="poor">Well loved</option></select></label></div><label>Price (NPR)<input name="price" type="number" min="0" max="99999999.99" step="0.01" required placeholder="0.00"/></label><label>Tell its story<textarea name="description" required rows={4} placeholder="Specs, condition, and the little things a buyer should know…"/></label>{!categories.length && <p className="form-error">No categories are available yet. Add a category in the Django admin before listing an item.</p>}{error && <p className="form-error" role="alert">{error}</p>}<button className="button primary full" disabled={busy || !categories.length}>{busy ? <LoaderCircle size={18} className="spin"/> : <>Publish listing<ArrowRight size={17}/></>}</button><p className="fine-print">A good photo and an honest description go a long way.</p></form>;
}
