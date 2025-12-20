'use client';

import { Logo } from '@/components/icons';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { BarChart2, CandlestickChart, LineChart, TrendingUp, Tv2 } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

/**
 * The main layout for all display screens.
 * It includes the header with the app title and the navigation tabs
 * to switch between different market views (Ticker, Market Map, Terminal, Leaderboard).
 * @param {object} props - The component props.
 * @param {React.ReactNode} props.children - The child components to be rendered within the layout.
 * @returns {JSX.Element} The rendered display layout component.
 */
export default function DisplayLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  // Determine the active tab from the URL path to highlight the correct tab.
  const activeTab = pathname.split('/').pop() || 'ticker';

  const navItems = [
    { id: 'display', label: 'Börsenticker', href: '/display', icon: CandlestickChart },
    { id: 'market-map', label: 'Marktübersicht', href: '/display/market-map', icon: BarChart2 },
    { id: 'terminal', label: 'Terminal', href: '/display/terminal', icon: Tv2 },
    { id: 'leaderboard', label: 'Rangliste', href: '/display/leaderboard', icon: TrendingUp },
    { id: 'stock-chart', label: 'Titel-Chart', href: '/display/stock-chart', icon: LineChart },
  ];

  return (
    <div className="flex h-screen w-screen flex-col bg-black text-gray-200">
      <header className="flex items-center justify-between border-b border-gray-700 px-4 py-2">
        <Link href="/" className="flex items-center gap-3">
          <Logo className="h-8 w-8 text-primary" />
          <h1 className="text-xl font-bold text-white font-headline tracking-wide">
          Schön. <span className="text-primary">Macht.</span> Geld.
          </h1>
        </Link>
        <Tabs value={activeTab === 'display' ? 'display' : activeTab} className="w-auto">
          <TabsList>
            {navItems.map((item) => (
              <TabsTrigger value={item.id} key={item.id} asChild>
                <Link href={item.href} className="gap-2">
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </Link>
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </header>
      <main className="flex-1 overflow-hidden">{children}</main>
    </div>
  );
}
