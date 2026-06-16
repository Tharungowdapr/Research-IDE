import type { Metadata } from 'next';
import './globals.css';
import { Providers } from './providers';

export const metadata: Metadata = {
  title: 'ResearchIDE — AI-Powered Research Platform',
  description:
    'From idea to research paper. ResearchIDE helps students and researchers automate literature review, gap analysis, idea generation, and paper writing with AI.',
  keywords: ['research', 'AI', 'academic', 'paper writing', 'literature review', 'gap analysis'],
  openGraph: {
    title: 'ResearchIDE — AI-Powered Research Platform',
    description: 'From idea to research paper with AI-powered workflow automation.',
    type: 'website',
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
