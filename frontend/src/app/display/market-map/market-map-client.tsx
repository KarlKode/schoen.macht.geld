'use client';

import type { Stock } from '@/lib/types';
import { useMemo } from 'react';
import { ResponsiveContainer, Tooltip, Treemap } from 'recharts';
import { useFirebase, useCollection, useMemoFirebase } from '@/firebase';
import { collection } from 'firebase/firestore';

/**
 * A custom content renderer for the Treemap component from recharts.
 * It renders each cell of the treemap, styling it based on the stock's performance.
 * Tiny boxes are not rendered to avoid visual clutter.
 * @param {any} props - The props provided by the Treemap component.
 * @returns {JSX.Element | null} The rendered treemap cell or null if the cell is too small.
 */
const CustomizedContent = (props: any) => {
  const { x, y, width, height, name, percentChange, ticker } = props;

  // Don't render cells that are too small to be readable.
  if (width < 50 || height < 40) {
    return null;
  }

  const isPositive = percentChange >= 0;

  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        style={{
          fill: isPositive ? 'hsl(142.1 76.2% 36.3%)' : 'hsl(0 72.2% 50.6%)',
          stroke: '#1f2937',
          strokeWidth: 2,
          opacity: 0.8,
        }}
      />
      <foreignObject x={x + 4} y={y + 4} width={width - 8} height={height - 8}>
        <div
          style={{
            width: '100%',
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'flex-start',
            color: 'white',
            padding: '4px',
          }}
        >
          <div style={{ fontWeight: 'bold', fontSize: '1.25rem' }}>{ticker}</div>
          <div style={{ fontSize: '0.8rem', opacity: 0.8, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{name}</div>
          <div style={{ marginTop: 'auto', fontSize: '1.2rem', fontWeight: 'bold' }}>
              {isPositive ? '+' : ''}
              {(percentChange ?? 0).toFixed(2)}%
          </div>
        </div>
      </foreignObject>
    </g>
  );
};

/**
 * The client component for the Market Map page.
 * It fetches real-time stock data from Firestore and visualizes it as a treemap.
 * The size of each rectangle in the treemap represents the stock's current value,
 * and the color indicates whether its value has increased (green) or decreased (red).
 * @returns {JSX.Element} The rendered market map client component.
 */
export default function MarketMapClient() {
  const { firestore } = useFirebase();
  const titlesCollection = useMemoFirebase(() => firestore ? collection(firestore, 'titles') : null, [firestore]);
  const { data: stocks } = useCollection<Stock>(titlesCollection);
  
  // Memoize the data formatted for the treemap to prevent unnecessary re-renders.
  const treemapData = useMemo(() => {
    if (!stocks) return [];
    return stocks.map(stock => ({
      ...stock,
      name: stock.nickname,
      // The size key for the treemap must be a positive number.
      size: Math.max(stock.currentValue, 1), // Ensure size is at least 1
    }));
  }, [stocks]);

  return (
    <ResponsiveContainer width="100%" height="100%">
      <Treemap
        data={treemapData}
        dataKey="size"
        nameKey="name"
        aspectRatio={16 / 9}
        content={<CustomizedContent />}
        isAnimationActive={false}
      >
        <Tooltip
          contentStyle={{
            background: '#1f2937',
            border: '1px solid #374151',
            borderRadius: '0.5rem',
          }}
          labelStyle={{ color: 'white' }}
          formatter={(value: number, name: string, props) => {
              if (!props.payload?.payload) return null;
              
              const stockData = props.payload.payload as Stock;
              const isPositive = stockData.change >= 0;

              return [
                   `${stockData.currentValue.toFixed(2)} CHF`,
                   <span key="change" className={isPositive ? 'text-green-400' : 'text-red-500'}>
                    {isPositive ? '+' : ''}{stockData.change.toFixed(2)} ({stockData.percentChange.toFixed(2)}%)
                   </span>
              ]
          }}
          labelFormatter={(label) => <span className="font-bold text-lg">{label}</span>}
        />
      </Treemap>
    </ResponsiveContainer>
  );
}
