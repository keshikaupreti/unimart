import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'UniMart — Good finds. New beginnings.', description: 'Buy and sell pre-loved essentials with your campus community. A little more possibility, a little less waste.' };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }
