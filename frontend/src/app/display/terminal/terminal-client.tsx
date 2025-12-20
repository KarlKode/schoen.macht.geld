'use client';

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { cn } from '@/lib/utils';
import { ArrowDown, ArrowUp, Minus } from 'lucide-react';
import { useEffect, useState, useMemo } from 'react';
import { useStocks } from '@/hooks/use-stocks';
import type { StockResponse } from '@/lib/api/client';

/**
 * A component that displays a scrolling news ticker with stock updates.
 * It cycles through headlines about the top performing stocks.
 */
const NewsTicker = ({ stocks }: { stocks: StockResponse[] }) => {
  const [headlineIndex, setHeadlineIndex] = useState(0);

  // Generate headlines from top movers
  const headlines = useMemo(() => {
    if (!stocks || stocks.length === 0) {
      return ['Willkommen beim Schön. Macht. Geld. News Network.'];
    }

    // Find the top stocks with the largest absolute percentage change
    const topMovers = [...stocks]
      .sort((a, b) => Math.abs(b.percent_change) - Math.abs(a.percent_change))
      .slice(0, 5);

    return topMovers.map((stock) => {
      const direction = stock.percent_change >= 0 ? 'steigt' : 'fällt';
      const emoji = stock.percent_change >= 0 ? '📈' : '📉';
      return `${emoji} ${stock.title} (${stock.ticker}) ${direction} um ${Math.abs(stock.percent_change).toFixed(2)}%`;
    });
  }, [stocks]);

  // Cycle through headlines
  useEffect(() => {
    if (headlines.length > 1) {
      const interval = setInterval(() => {
        setHeadlineIndex((prev) => (prev + 1) % headlines.length);
      }, 8000);
      return () => clearInterval(interval);
    }
  }, [headlines]);

  const currentHeadline = headlines[headlineIndex];

  return (
    <div className="w-full bg-red-700 text-white h-10 flex items-center overflow-hidden">
      {currentHeadline && (
        <div
          key={currentHeadline}
          className="flex animate-marquee-fast whitespace-nowrap"
          style={{ animationDuration: '30s' }}
        >
          <span className="text-xl font-bold px-12">{currentHeadline}</span>
          <span className="text-xl font-bold px-12" aria-hidden="true">
            {currentHeadline}
          </span>
        </div>
      )}
      <style jsx>{`
        @keyframes marquee-fast {
          from {
            transform: translateX(0%);
          }
          to {
            transform: translateX(-50%);
          }
        }
        .animate-marquee-fast {
          animation: marquee-fast 30s linear infinite;
        }
      `}</style>
    </div>
  );
};

/**
 * The main client component for the Terminal display. It resembles a financial
 * terminal, showing a table of all stocks with their values and changes.
 * It also includes a NewsTicker at the bottom.
 */
export default function TerminalClient() {
  const { stocks, isLoading } = useStocks();

  const sortedStocks = useMemo(() => {
    return [...stocks].sort((a, b) => (a.rank ?? Infinity) - (b.rank ?? Infinity));
  }, [stocks]);

  if (isLoading && stocks.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-black text-green-400 font-mono">
        Lade Terminal...
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col p-2 bg-black text-green-400 font-mono overflow-hidden">
      <div className="flex justify-between items-center text-yellow-400 border-b-2 border-yellow-400 pb-1">
        <h1 className="text-2xl">SMG TERMINAL</h1>
      </div>
      <div className="flex-1 overflow-y-auto mt-1">
        <Table>
          <TableHeader>
            <TableRow className="border-gray-700 hover:bg-gray-900">
              <TableHead className="text-yellow-400 w-12 px-1 h-6 py-0"></TableHead>
              <TableHead className="text-yellow-400 px-1 h-6 py-0">TICKER</TableHead>
              <TableHead className="text-yellow-400 px-1 h-6 py-0">NAME</TableHead>
              <TableHead className="text-yellow-400 text-right px-1 h-6 py-0">WERT</TableHead>
              <TableHead className="text-yellow-400 text-right px-1 h-6 py-0">CHG</TableHead>
              <TableHead className="text-yellow-400 text-right px-1 h-6 py-0">% CHG</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedStocks.map((stock) => {
              const isPositive = stock.change >= 0;

              let RankIndicator;
              if (!stock.rank || !stock.previous_rank || stock.rank === stock.previous_rank) {
                RankIndicator = <Minus className="w-4 h-4 text-gray-600" />;
              } else if (stock.rank < stock.previous_rank) {
                RankIndicator = <ArrowUp className="w-4 h-4 text-green-400" />;
              } else {
                RankIndicator = <ArrowDown className="w-4 h-4 text-red-500" />;
              }

              return (
                <TableRow key={stock.ticker} className="border-gray-800 hover:bg-gray-900/50">
                  <TableCell className="w-12 px-1 py-0">{RankIndicator}</TableCell>
                  <TableCell className="font-bold px-1 py-0">{stock.ticker}</TableCell>
                  <TableCell className="px-1 py-0 truncate max-w-xs">{stock.title}</TableCell>
                  <TableCell
                    className={cn(
                      'text-right font-bold px-1 py-0',
                      isPositive ? 'text-green-400' : 'text-red-500'
                    )}
                  >
                    {stock.price.toFixed(2)} CHF
                  </TableCell>
                  <TableCell
                    className={cn(
                      'text-right px-1 py-0',
                      stock.change === 0
                        ? 'text-gray-500'
                        : isPositive
                          ? 'text-green-400'
                          : 'text-red-500'
                    )}
                  >
                    {stock.change >= 0 ? '+' : ''}
                    {stock.change.toFixed(2)}
                  </TableCell>
                  <TableCell
                    className={cn(
                      'text-right px-1 py-0',
                      stock.percent_change === 0
                        ? 'text-gray-500'
                        : isPositive
                          ? 'text-green-400'
                          : 'text-red-500'
                    )}
                  >
                    {stock.percent_change >= 0 ? '+' : ''}
                    {stock.percent_change.toFixed(2)}%
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
      <div className="mt-auto">
        <NewsTicker stocks={stocks} />
      </div>
    </div>
  );
}
