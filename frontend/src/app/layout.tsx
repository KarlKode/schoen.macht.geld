'use client';

import { Poppins } from 'next/font/google';
import './globals.css';
import { Toaster } from '@/components/ui/toaster';
import { cn } from '@/lib/utils';
import { SWRConfig } from 'swr';

const poppins = Poppins({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  variable: '--font-body',
});

/**
 * The root layout component for the entire application.
 * Sets up the HTML structure, global fonts, and SWR provider.
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="de" className="dark">
      <head>
        <title>Schön. Macht. Geld.</title>
        <meta name="description" content="Das ultimative Börsensimulations-Partyspiel von VAK & Amphitheater." />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className={cn('font-body antialiased', poppins.variable)}>
        <SWRConfig
          value={{
            revalidateOnFocus: false,
            dedupingInterval: 1000,
          }}
        >
          {children}
          <Toaster />
        </SWRConfig>
      </body>
    </html>
  );
}
