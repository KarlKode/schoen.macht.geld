import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Presentation, Smartphone, UserPlus } from 'lucide-react';
import Link from 'next/link';
import { Logo } from '@/components/icons';

/**
 * The home page of the application.
 * It serves as a splash screen and entry point to the three main parts of the app:
 * Registration, Stock Swipe, and Market Display.
 * @returns {JSX.Element} The rendered home page.
 */
export default function Home() {
  const features = [
    {
      title: 'Registrierungsstation',
      description:
        'Vor-Ort-Registrierung mit Spitznamen und Live-Fotoaufnahme. Werde eine neue Aktie auf dem Markt.',
      href: '/register',
      icon: <UserPlus className="h-10 w-10" />,
    },
    {
      title: 'Stock Swipe',
      description:
        'Kiosk-App zum Swipen von Aktien (Profilen) nach links oder rechts, um den Aktienwert in Echtzeit zu beeinflussen.',
      href: '/swipe',
      icon: <Smartphone className="h-10 w-10" />,
    },
    {
      title: 'Markt-Display',
      description:
        'Live-Visualisierung der Marktdaten. Umfasst Börsenticker, Marktkarten und ein Terminal im Bloomberg-Stil.',
      href: '/display',
      icon: <Presentation className="h-10 w-10" />,
    },
  ];

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-background text-foreground p-4 sm:p-8">
      <div className="flex flex-col items-center justify-center space-y-8 text-center">
        <div className="flex items-center gap-4">
          <Logo className="h-16 w-16 text-primary" />
          <h1 className="text-5xl sm:text-6xl md:text-7xl font-headline font-bold tracking-tighter">
            Schön. <span className="text-primary">Macht.</span> Geld.
          </h1>
        </div>
        <p className="max-w-2xl text-lg text-muted-foreground sm:text-xl font-body">
          Eine Initiative vom Verein für ambitionierten Konsum & Amphitheater.
          Registriere dich, lass dich swipen und sieh zu, wie dein Wert steigt (oder fällt).
        </p>
      </div>

      <div className="mt-16 grid grid-cols-1 gap-8 md:grid-cols-3 md:gap-6 lg:gap-8">
        {features.map((feature) => (
          <Link href={feature.href} key={feature.title} className="group">
            <Card className="h-full transform transition-all duration-300 ease-in-out group-hover:scale-105 group-hover:shadow-2xl group-hover:shadow-primary/20 group-hover:border-primary">
              <CardHeader className="flex flex-col items-center justify-center text-center">
                <div className="mb-4 rounded-full bg-primary/10 p-4 text-primary transition-colors duration-300 group-hover:bg-primary group-hover:text-primary-foreground">
                  {feature.icon}
                </div>
                <CardTitle className="text-2xl font-headline">
                  {feature.title}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-center text-base">
                  {feature.description}
                </CardDescription>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </main>
  );
}
