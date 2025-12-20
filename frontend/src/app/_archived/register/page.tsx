import RegistrationClient from './registration-client';
import { Logo } from '@/components/icons';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

/**
 * The server component for the registration and admin page.
 * It provides the layout and renders the `RegistrationClient` component,
 * which handles the interactive parts of user registration and stock management.
 * @returns {JSX.Element} The rendered registration page.
 */
export default function RegisterPage() {
  return (
    <div className="relative min-h-screen w-full bg-background flex flex-col items-center p-4 sm:py-8">
      <Link
        href="/"
        className="absolute top-4 left-4 flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Zurück zur Startseite
      </Link>
      <div className="w-full max-w-4xl mx-auto">
        <div className="flex flex-col items-center space-y-4 text-center mb-8">
          <Logo className="h-12 w-12 text-primary" />
          <h1 className="text-4xl font-bold font-headline">Tritt dem Markt bei</h1>
          <p className="text-muted-foreground text-lg">
            Erstelle dein Profil, um eine öffentlich gehandelte Entität bei Schön. Macht. Geld. zu werden.
          </p>
        </div>
        <RegistrationClient />
      </div>
    </div>
  );
}
