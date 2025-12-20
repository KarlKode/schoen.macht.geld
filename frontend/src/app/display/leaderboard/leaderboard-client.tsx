'use client';

import { cn } from '@/lib/utils';
import { ArrowDown, ArrowUp } from 'lucide-react';
import { useStocks } from '@/hooks/use-stocks';

/**
 * The client component for the Leaderboard page.
 * It fetches all stock data from the API in real-time and displays them
 * in a static, alphabetized grid that fits on a single screen without scrolling.
 */
export default function LeaderboardClient() {
  const { stocks, isLoading } = useStocks();

  // Sort stocks alphabetically by title
  const sortedStocks = [...stocks].sort((a, b) => a.title.localeCompare(b.title));

  if (isLoading && stocks.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-black text-white">
        Lade Rangliste...
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col p-4 bg-black text-gray-200 overflow-hidden">
      <h1 className="text-3xl font-bold text-center mb-4 text-white">Rangliste</h1>
      <div className="flex-1 overflow-hidden">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2 h-full">
          {sortedStocks.map((stock) => {
            const isPositive = stock.percent_change >= 0;

            return (
              <div
                key={stock.ticker}
                className="grid grid-cols-[1fr_100px_80px] items-center gap-3 p-2 rounded-lg bg-gray-900/50 border border-gray-800 text-base"
              >
                <div className="flex flex-col overflow-hidden">
                  <span className="font-bold text-white truncate">{stock.title}</span>
                  <span className="text-xs font-mono text-gray-400">{stock.ticker}</span>
                </div>
                <span
                  className={cn(
                    'font-mono font-bold text-right',
                    isPositive ? 'text-green-400' : 'text-red-500'
                  )}
                >
                  {stock.price.toFixed(2)}
                </span>
                <div
                  className={cn(
                    'flex items-center justify-end gap-1 font-bold',
                    isPositive ? 'text-green-400' : 'text-red-500'
                  )}
                >
                  {stock.percent_change !== 0 && (
                    isPositive ? <ArrowUp size={16} /> : <ArrowDown size={16} />
                  )}
                  <span>
                    {isPositive ? '+' : ''}
                    {stock.percent_change.toFixed(2)}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
