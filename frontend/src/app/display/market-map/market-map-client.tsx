'use client';

import { useMemo } from 'react';
import { ResponsiveContainer, Tooltip, Treemap } from 'recharts';
import { useStocks } from '@/hooks/use-stocks';
import type { StockResponse } from '@/lib/api/client';

/**
 * A custom content renderer for the Treemap component from recharts.
 * It renders each cell of the treemap, styling it based on the stock's performance.
 */
const CustomizedContent = (props: any) => {
  const { x, y, width, height, name, percent_change, ticker } = props;

  // Don't render cells that are too small to be readable
  if (width < 50 || height < 40) {
    return null;
  }

  const isPositive = percent_change >= 0;

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
          <div
            style={{
              fontSize: '0.8rem',
              opacity: 0.8,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {name}
          </div>
          <div style={{ marginTop: 'auto', fontSize: '1.2rem', fontWeight: 'bold' }}>
            {isPositive ? '+' : ''}
            {(percent_change ?? 0).toFixed(2)}%
          </div>
        </div>
      </foreignObject>
    </g>
  );
};

/**
 * The client component for the Market Map page.
 * It fetches real-time stock data and visualizes it as a treemap.
 * The size of each rectangle represents the stock's current value,
 * and the color indicates whether its value has increased (green) or decreased (red).
 */
export default function MarketMapClient() {
  const { stocks, isLoading } = useStocks();

  // Memoize the data formatted for the treemap
  const treemapData = useMemo(() => {
    return stocks.map((stock) => ({
      ...stock,
      name: stock.title,
      // The size key for the treemap must be a positive number
      size: Math.max(stock.price, 1),
    }));
  }, [stocks]);

  if (isLoading && stocks.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-black text-white">
        Lade Market Map...
      </div>
    );
  }

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
          formatter={(value: number, name: string, props: any) => {
            if (!props.payload?.payload) return null;

            const stockData = props.payload.payload as StockResponse;
            const isPositive = stockData.change >= 0;

            return [
              `${stockData.price.toFixed(2)} CHF`,
              <span key="change" className={isPositive ? 'text-green-400' : 'text-red-500'}>
                {isPositive ? '+' : ''}
                {stockData.change.toFixed(2)} ({stockData.percent_change.toFixed(2)}%)
              </span>,
            ];
          }}
          labelFormatter={(label) => <span className="font-bold text-lg">{label}</span>}
        />
      </Treemap>
    </ResponsiveContainer>
  );
}
