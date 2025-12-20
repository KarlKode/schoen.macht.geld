'use client';

import { useEffect, useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import Image from 'next/image';
import { cn } from '@/lib/utils';
import { ArrowDown, ArrowUp } from 'lucide-react';
import { useStocks, useStockSnapshots } from '@/hooks/use-stocks';

/**
 * A client component that displays a full-screen, auto-playing chart for each stock.
 * It cycles through stocks every 20 seconds, showing a detailed history graph,
 * the stock's photo, and key performance indicators.
 */
export default function StockChartClient() {
  const { stocks, isLoading } = useStocks();
  const [currentIndex, setCurrentIndex] = useState(0);

  // Get the current stock
  const activeStock = useMemo(() => {
    if (!stocks || stocks.length === 0) return null;
    return stocks[currentIndex % stocks.length];
  }, [stocks, currentIndex]);

  // Fetch snapshots for the active stock
  const { snapshots } = useStockSnapshots(activeStock?.ticker ?? null, 100);

  // Effect to cycle through the stocks every 20 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentIndex((prevIndex) => {
        if (!stocks || stocks.length === 0) return 0;
        return (prevIndex + 1) % stocks.length;
      });
    }, 20000);

    return () => clearInterval(timer);
  }, [stocks]);

  if (isLoading || !activeStock) {
    return (
      <div className="flex items-center justify-center h-full text-white bg-black">
        Lade Chart-Daten...
      </div>
    );
  }

  // Format snapshots for the chart
  const chartData = snapshots.map((snapshot) => ({
    value: snapshot.price,
    timestamp: new Date(snapshot.created_at).toLocaleTimeString('de-DE', {
      hour: '2-digit',
      minute: '2-digit',
    }),
  }));

  const isPositive = activeStock.percent_change >= 0;
  const imageUrl = activeStock.image || '/placeholder.png';

  return (
    <div className="w-full h-full p-6 flex flex-col bg-black text-white">
      <AnimatePresence mode="wait">
        <motion.div
          key={activeStock.ticker}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1, transition: { duration: 1 } }}
          exit={{ opacity: 0, transition: { duration: 1 } }}
          className="flex-1 flex flex-col"
        >
          {/* Header */}
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-6">
              <div className="relative w-32 h-32 rounded-full overflow-hidden border-4 border-gray-700">
                <Image
                  src={imageUrl}
                  alt={activeStock.title}
                  fill
                  className="object-cover"
                />
              </div>
              <div>
                <h1 className="text-6xl font-bold">{activeStock.title}</h1>
                <p className="text-3xl text-gray-400 font-mono">{activeStock.ticker}</p>
              </div>
            </div>
            <div className="flex flex-col items-end">
              <span
                className={cn(
                  'text-7xl font-mono font-bold',
                  isPositive ? 'text-green-400' : 'text-red-500'
                )}
              >
                {activeStock.price.toFixed(2)} <span className="text-5xl">CHF</span>
              </span>
              <div
                className={cn(
                  'flex items-center justify-end gap-3 text-4xl font-bold mt-1',
                  isPositive ? 'text-green-400' : 'text-red-500'
                )}
              >
                {isPositive ? <ArrowUp size={36} /> : <ArrowDown size={36} />}
                <span>
                  {isPositive ? '+' : ''}
                  {activeStock.change.toFixed(2)} ({activeStock.percent_change.toFixed(2)}%)
                </span>
              </div>
            </div>
          </div>

          {/* Chart */}
          <div className="flex-1 mt-6">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                <defs>
                  <linearGradient id={`color-${isPositive}`} x1="0" y1="0" x2="0" y2="1">
                    <stop
                      offset="5%"
                      stopColor={isPositive ? 'hsl(142.1 76.2% 36.3%)' : 'hsl(0 72.2% 50.6%)'}
                      stopOpacity={0.8}
                    />
                    <stop
                      offset="95%"
                      stopColor={isPositive ? 'hsl(142.1 76.2% 36.3%)' : 'hsl(0 72.2% 50.6%)'}
                      stopOpacity={0}
                    />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
                <XAxis dataKey="timestamp" tick={{ fill: 'white' }} tickLine={{ stroke: 'white' }} />
                <YAxis
                  domain={['dataMin - 1', 'dataMax + 1']}
                  tick={{ fill: 'white' }}
                  tickLine={{ stroke: 'white' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    border: '1px solid #555',
                    color: 'white',
                  }}
                  labelStyle={{ fontWeight: 'bold' }}
                  formatter={(value: number) => [`${value.toFixed(2)} CHF`, 'Wert']}
                />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke={isPositive ? 'hsl(142.1 76.2% 36.3%)' : 'hsl(0 72.2% 50.6%)'}
                  strokeWidth={3}
                  fillOpacity={1}
                  fill={`url(#color-${isPositive})`}
                  isAnimationActive={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
