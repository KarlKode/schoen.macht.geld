'use client';

import type { Stock } from '@/lib/types';
import { useMemo } from 'react';
import { useFirebase, useCollection, useMemoFirebase } from '@/firebase';
import { collection } from 'firebase/firestore';

/**
 * A component that displays a horizontally scrolling stock ticker.
 * It fetches real-time stock data from Firestore and animates the prices across the screen.
 * The color and arrow indicator are based on the change in the last minute.
 * @returns {JSX.Element} The rendered stock ticker component.
 */
const StockTicker = () => {
  const { firestore } = useFirebase();
  const titlesCollection = useMemoFirebase(() => firestore ? collection(firestore, 'titles') : null, [firestore]);
  const { data: stocks, isLoading } = useCollection<Stock>(titlesCollection);

  // The stock list is duplicated to create a seamless looping animation.
  const repeatedStocks = useMemo(() => {
    if (!stocks || stocks.length === 0) return [];
    // Ensure the list is long enough for a seamless loop by repeating it.
    const repeatCount = Math.max(2, Math.ceil(40 / stocks.length));
    return Array(repeatCount).fill(stocks).flat();
  }, [stocks]);


  if (isLoading || !stocks) {
    return (
      <div className="w-full bg-gray-900 text-white h-full flex items-center justify-center">
        <span className="text-2xl font-mono font-bold text-gray-400">
          Warte auf Marktdaten...
        </span>
      </div>
    );
  }

  // Calculate a dynamic animation duration based on the number of items
  // to maintain a relatively consistent speed.
  const animationDuration = (stocks?.length || 10) * 5;

  return (
    <div className="w-full bg-gray-900 text-white h-full flex items-center overflow-hidden">
      <div
        className="flex animate-marquee whitespace-nowrap"
        style={{ animationDuration: `${animationDuration}s` }}
      >
        {repeatedStocks.map((stock, index) => {
          const lastChangeIsPositive = stock.valueChangeLastMinute >= 0;
          return (
            <div
              key={`${stock.id}-${index}`}
              className="flex items-center mx-6"
            >
              <span className="text-2xl font-mono font-bold text-gray-400">
                {stock.nickname}
              </span>
              <span
                className={`text-2xl font-mono font-bold ml-3 ${
                  lastChangeIsPositive ? 'text-green-400' : 'text-red-400'
                }`}
              >
                {stock.currentValue.toFixed(2)} CHF
              </span>
              <span
                className={`ml-2 text-lg ${
                  lastChangeIsPositive ? 'text-green-400' : 'text-red-400'
                }`}
              >
                {stock.valueChangeLastMinute > 0 ? '▲' : stock.valueChangeLastMinute < 0 ? '▼' : ''}
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
 * @returns {JSX.Element} The rendered display ticker page.
 */
export default function DisplayTickerPage() {
  return (
    <div className="h-full w-full">
      <StockTicker />
    </div>
  );
}
