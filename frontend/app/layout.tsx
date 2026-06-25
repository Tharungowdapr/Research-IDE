import type { Metadata } from 'next';
import { Crimson_Pro, Atkinson_Hyperlegible, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';

const crimsonPro = Crimson_Pro({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-heading',
  weight: ['400', '500', '600', '700'],
});

const atkinson = Atkinson_Hyperlegible({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-body',
  weight: ['400', '700'],
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-mono',
});

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
    <html lang="en" suppressHydrationWarning className={`${crimsonPro.variable} ${atkinson.variable} ${jetbrainsMono.variable}`}>
      <body className="antialiased" style={{ fontFamily: 'var(--font-body), system-ui, sans-serif' }}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
