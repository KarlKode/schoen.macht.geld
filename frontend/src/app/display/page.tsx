'use client';

import { useMemo } from 'react';
import { useStocks } from '@/hooks/use-stocks';

/**
 * A component that displays a horizontally scrolling stock ticker.
 * It fetches real-time stock data and animates the prices across the screen.
 */
const StockTicker = () => {
  const { stocks, isLoading } = useStocks();

  // The stock list is duplicated to create a seamless looping animation
  const repeatedStocks = useMemo(() => {
    if (!stocks || stocks.length === 0) return [];
    const repeatCount = Math.max(2, Math.ceil(40 / stocks.length));
    return Array(repeatCount).fill(stocks).flat();
  }, [stocks]);

  if (isLoading && stocks.length === 0) {
    return (
      <div className="w-full bg-gray-900 text-white h-full flex items-center justify-center">
        <span className="text-2xl font-mono font-bold text-gray-400">
          Warte auf Marktdaten...
        </span>
      </div>
    );
  }

  // Calculate a dynamic animation duration based on the number of items
  const animationDuration = (stocks?.length || 10) * 5;

  return (
    <div className="w-full bg-gray-900 text-white h-full flex items-center overflow-hidden">
      <div
        className="flex animate-marquee whitespace-nowrap"
        style={{ animationDuration: `${animationDuration}s` }}
      >
        {repeatedStocks.map((stock, index) => {
          const isPositive = stock.change >= 0;
          return (
            <div key={`${stock.ticker}-${index}`} className="flex items-center mx-6">
              <span className="text-2xl font-mono font-bold text-gray-400">{stock.title}</span>
              <span
                className={`text-2xl font-mono font-bold ml-3 ${
                  isPositive ? 'text-green-400' : 'text-red-400'
                }`}
              >
                {stock.price.toFixed(2)} CHF
              </span>
              <span className={`ml-2 text-lg ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                {stock.change > 0 ? '▲' : stock.change < 0 ? '▼' : ''}
              </span>
            </div>
          );
        })}
      </div>
      <style jsx>{`
        @keyframes marquee {
          from {
            transform: translateX(0%);
          }
          to {
            transform: translateX(-50%);
          }
        }
        .animate-marquee {
          animation: marquee linear infinite;
        }
      `}</style>
    </div>
  );
};

/**
 * The main page for the stock ticker display.
 */
export default function DisplayTickerPage() {
  return (
    <div className="h-full w-full">
      <StockTicker />
    </div>
  );
}
