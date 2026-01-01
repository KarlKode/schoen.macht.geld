'use client';

import { VT323 } from 'next/font/google';
import './globals.css';
import { Toaster } from '@/components/ui/toaster';
import { cn } from '@/lib/utils';
import { SWRConfig } from 'swr';
import { EffectsProvider, useEffects } from '@/contexts/effects-context';
import { EventsProvider } from '@/contexts/events-context';
import { MarketProvider } from '@/contexts/market-context';
import { WebSocketProvider } from '@/contexts/websocket-context';
import { EffectsLayer } from '@/components/effects';
import { EventsLayer } from '@/components/events';
import { HotkeysProvider } from '@/hooks/use-hotkeys';

const vt323 = VT323({
  subsets: ['latin'],
  weight: ['400'],
  variable: '--font-body',
});

function AppContent({ children }: { children: React.ReactNode }) {
  const { resetEffects } = useEffects();

  return (
    <SWRConfig
      value={{
        revalidateOnFocus: false,
        dedupingInterval: 1000,
        onError: (error) => {
          // Check for 500 errors
          if (
            error?.status === 500 ||
            error?.message?.includes('500') ||
            error?.message?.includes('Internal Server Error')
          ) {
            resetEffects();
          }
        },
      }}
    >
      <WebSocketProvider>
        <MarketProvider>
          <EventsProvider>
            <HotkeysProvider>
              {children}
              <EffectsLayer />
              <EventsLayer />
              <Toaster />
            </HotkeysProvider>
          </EventsProvider>
        </MarketProvider>
      </WebSocketProvider>
    </SWRConfig>
  );
}

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
        <meta name="google" content="notranslate" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className={cn('font-body antialiased', vt323.variable)}>
        <EffectsProvider>
          <AppContent>{children}</AppContent>
        </EffectsProvider>
      </body>
    </html>
  );
}
