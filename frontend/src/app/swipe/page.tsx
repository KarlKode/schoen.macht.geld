import SwipeClient from './swipe-client';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

/**
 * The server component for the Swipe Kiosk page.
 * It provides the basic layout and renders the `SwipeClient`, which
 * contains all the interactive logic for swiping.
 * @returns {JSX.Element} The rendered swipe page.
 */
export default function SwipePage() {
  return (
    <div className="h-screen w-screen overflow-hidden bg-background flex flex-col items-center justify-center relative">
       <Link
        href="/"
        className="absolute top-4 left-4 z-20 flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Zurück zur Startseite
      </Link>
      <SwipeClient />
    </div>
  );
}

    
