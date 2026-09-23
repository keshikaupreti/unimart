import type { Category, Listing } from './api';
export const demoCategories: Category[] = ['Electronics', 'Books', 'Fashion', 'Home & Living', 'Sports', 'Other'].map((name, i) => ({ id: `demo-category-${i}`, name, slug: name.toLowerCase().replaceAll(' ', '-') }));
const items = [
  ['MacBook Air M2', 'Light on your desk. Big on possibility.', '78000', 'like_new', 0, 'macbook', 'Aarav'],
  ['Sony WH-1000XM4', 'Your own little world of sound.', '18500', 'like_new', 0, 'headphones', 'Sarina'],
  ['A little library of ideas', 'Good stories deserve another chapter.', '1200', 'good', 1, 'books', 'Pratik'],
  ['The everyday backpack', 'For campus days and everything after.', '1850', 'new', 2, 'backpack', 'Anisha'],
  ['Fujifilm X-T30', 'See the everyday a little differently.', '62000', 'like_new', 0, 'camera', 'Rohan'],
  ['A greener little corner', 'A fresh start for your favorite space.', '650', 'good', 3, 'plant', 'Sneha'],
  ['Nike everyday sneakers', 'Ready for wherever the day takes you.', '3200', 'like_new', 2, 'sneakers', 'Bishal'],
  ['Take the long way home', 'Two wheels. Endless possibilities.', '14500', 'good', 4, 'bike', 'Nisha'],
];
export const demoListings: Listing[] = items.map((item, i) => ({ id: `demo-${i}`, title: String(item[0]), description: `${item[1]} Carefully looked after and ready for a new home. This is a sample listing to help you explore UniMart. Connect to the marketplace to discover real items from the community.`, price: String(item[2]), condition: String(item[3]), status: 'available', category: demoCategories[Number(item[4])].id, category_name: demoCategories[Number(item[4])].name, images: [{ id: `image-${i}`, image: `/images/${item[5]}.jpg` }], seller: { id: `seller-${i}`, username: String(item[6]) }, created_at: new Date(Date.UTC(2026, 8, 15 - i)).toISOString() }));
