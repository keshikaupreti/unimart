import { test, expect, type Page } from '@playwright/test';

const buyer = { id: 'buyer', username: 'buyer', first_name: 'Buyer', email: 'buyer@example.com' };
const seller = { id: 'seller', username: 'seller', first_name: 'Seller', email: 'seller@example.com' };
const category = { id: 'books', name: 'Books', slug: 'books' };
const listing = { id: 'listing', title: 'Calculus textbook', description: 'A useful book.', price: '250', condition: 'good', status: 'available', category: category.id, category_name: category.name, seller, images: [], created_at: '2026-01-01T00:00:00Z' };
const location = { id: 'library', name: 'Library Gate', description: 'Main entrance' };
const sale = { id: 'sale', listing: listing.id, listing_title: listing.title, buyer, seller, status: 'requested', meetup_time: '2099-01-01T12:00:00Z', meetup_location_detail: location };

async function setup(page: Page, role: 'buyer' | 'seller', initialStatus?: string) {
  const calls: { path: string; data: Record<string, unknown> }[] = [];
  let transactions = initialStatus ? [{ ...sale, status: initialStatus }] : [];
  const reviews: Record<string, unknown>[] = [];
  const disputes: Record<string, unknown>[] = [];
  const reports: Record<string, unknown>[] = [];
  await page.addInitScript(() => { sessionStorage.setItem('unimart-access', 'test-access'); sessionStorage.setItem('unimart-refresh', 'test-refresh'); });
  await page.route('**/api/**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname.replace('/api/', '');
    const post = request.method() === 'POST';
    const data = post ? request.postDataJSON() : {};
    if (post) calls.push({ path, data });
    let result: unknown;
    if (path === 'auth/me/') result = role === 'buyer' ? buyer : seller;
    else if (path === 'categories/') result = [category];
    else if (path === 'listings/') result = [listing];
    else if (path === 'saved-listings/') result = [];
    else if (path === 'meetup-locations/') result = [location];
    else if (path === 'transactions/') {
      if (post) { transactions = [{ ...sale, meetup_time: data.meetup_time }]; result = transactions[0]; }
      else result = transactions;
    } else if (path.startsWith('transactions/sale/')) {
      const action = path.split('/')[2];
      const status = ({ accept: 'accepted', reject: 'rejected', cancel: 'cancelled', complete: 'completed' } as Record<string, string>)[action];
      transactions = transactions.map(transaction => ({ ...transaction, status })); result = transactions[0];
    } else if (path === 'reviews/') {
      if (post) { const review = { ...data, id: 'review', reviewer: role === 'buyer' ? buyer : seller }; reviews.push(review); result = review; }
      else result = reviews;
    } else if (path === 'disputes/') {
      if (post) { const dispute = { ...data, id: 'dispute', status: 'open', admin_note: '', listing_title: listing.title }; disputes.push(dispute); result = dispute; }
      else result = disputes;
    } else if (path === 'reports/') {
      if (post) { const report = { ...data, id: 'report', status: 'open', admin_note: '' }; reports.push(report); result = report; }
      else result = reports;
    } else { await route.fulfill({ status: 404, json: { detail: `Unexpected request: ${path}` } }); return; }
    await route.fulfill({ status: post ? 201 : 200, json: Array.isArray(result) ? { results: result, next: null, count: result.length } : result });
  });
  await page.goto('/');
  await expect(page.getByRole('button', { name: role === 'buyer' ? 'Buyer' : 'Seller', exact: true })).toBeVisible();
  return calls;
}
async function openActivity(page: Page, name: string) {
  await page.getByRole('button', { name, exact: true }).click();
  await page.getByRole('button', { name: 'Purchases, sales & reports' }).click();
  await expect(page.getByRole('heading', { name: 'Purchases and sales' })).toBeVisible();
}

test('buyer requests a meetup and can cancel the request', async ({ page }) => {
  const calls = await setup(page, 'buyer');
  await page.getByRole('button', { name: 'View Calculus textbook', exact: true }).click();
  await page.getByRole('button', { name: 'Request to buy', exact: true }).click();
  await page.getByLabel('Meetup location').selectOption('library');
  await page.getByLabel('Meetup time (your local time)').fill('2099-01-01T12:00');
  await page.getByRole('button', { name: 'Send purchase request' }).click();
  await expect(page.getByText('requested', { exact: true })).toBeVisible();
  expect(calls.find(call => call.path === 'transactions/')?.data).toMatchObject({ listing: 'listing', meetup_location: 'library' });
  await expect(page.getByRole('button', { name: 'Accept request' })).toHaveCount(0);
  await page.getByRole('button', { name: 'Cancel request' }).click();
  await expect(page.getByText('cancelled', { exact: true })).toBeVisible();
});

test('seller accepts and completes a sale, then submits a review', async ({ page }) => {
  const calls = await setup(page, 'seller', 'requested');
  await openActivity(page, 'Seller');
  await page.getByRole('button', { name: 'Accept request' }).click();
  await expect(page.getByText('accepted', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Confirm handover complete' }).click();
  await expect(page.getByText('completed', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Leave a review' }).click();
  await page.getByLabel('Rating').selectOption('4');
  await page.getByLabel('Comment', { exact: true }).fill('On time and friendly.');
  await page.getByRole('button', { name: 'Submit review' }).click();
  await expect(page.getByText('Review submitted', { exact: true })).toBeVisible();
  expect(calls.find(call => call.path === 'reviews/')?.data).toEqual({ transaction: 'sale', rating: 4, comment: 'On time and friendly.' });
  await expect(page.getByRole('button', { name: 'Leave a review' })).toHaveCount(0);
});

test('buyer opens a dispute and reports a listing', async ({ page }) => {
  const calls = await setup(page, 'buyer', 'accepted');
  await openActivity(page, 'Buyer');
  await page.getByRole('button', { name: 'Open a dispute' }).click();
  await page.getByRole('combobox', { name: 'Reason', exact: true }).selectOption('payment');
  await page.getByLabel('Describe the issue').fill('The agreed price was changed.');
  await page.getByRole('button', { name: 'Submit dispute' }).click();
  await expect(page.getByText('The agreed price was changed.')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Open a dispute' })).toHaveCount(0);
  await page.getByRole('button', { name: 'Close dialog' }).click();
  await page.getByRole('button', { name: 'View Calculus textbook', exact: true }).click();
  await page.getByRole('button', { name: 'Report listing or seller' }).click();
  await page.getByRole('combobox', { name: 'Reason', exact: true }).selectOption('misleading');
  await page.getByLabel('What happened?').fill('The description is inaccurate.');
  await page.getByRole('button', { name: 'Submit report' }).click();
  await expect(page.getByText('The description is inaccurate.')).toBeVisible();
  expect(calls.find(call => call.path === 'reports/')?.data).toMatchObject({ listing: 'listing', reason: 'misleading' });
});

test('purchase errors keep the form available for correction', async ({ page }) => {
  await setup(page, 'buyer');
  await page.route('**/api/transactions/', route => route.request().method() === 'POST' ? route.fulfill({ status: 400, json: { detail: 'This listing is no longer available.' } }) : route.fallback());
  await page.getByRole('button', { name: 'View Calculus textbook', exact: true }).click();
  await page.getByRole('button', { name: 'Request to buy', exact: true }).click();
  await page.getByLabel('Meetup location').selectOption('library');
  await page.getByLabel('Meetup time (your local time)').fill('2099-01-01T12:00');
  await page.getByRole('button', { name: 'Send purchase request' }).click();
  await expect(page.getByRole('dialog').getByRole('alert')).toHaveText('This listing is no longer available.');
  await expect(page.getByRole('button', { name: 'Send purchase request' })).toBeEnabled();
});
