import useSWR from 'swr';
import {
  listStocksStocksGet,
  getStockStocksTickerGet,
  getStockSnapshotsStocksTickerSnapshotsGet,
  swipeSwipePost,
} from '@/lib/api';
import type { StockResponse, StockSnapshotResponse, SwipeDirection } from '@/lib/api/client';

// Fallback data for resilience
const FALLBACK_STOCKS: StockResponse[] = [];

export function useStocks(options?: { limit?: number; random?: boolean }) {
  const { data, error, isLoading, mutate } = useSWR(
    ['stocks', options?.limit, options?.random],
    async () => {
      const response = await listStocksStocksGet({
        query: { limit: options?.limit, random: options?.random },
      });
      return response.data;
    },
    {
      fallbackData: FALLBACK_STOCKS,
      refreshInterval: 2000,
      revalidateOnFocus: false,
      dedupingInterval: 1000,
    }
  );

  return {
    stocks: data ?? FALLBACK_STOCKS,
    isLoading,
    isError: !!error,
    error,
    mutate,
  };
}

export function useStock(ticker: string | null) {
  const { data, error, isLoading, mutate } = useSWR(
    ticker ? `stock-${ticker}` : null,
    async () => {
      if (!ticker) return null;
      const response = await getStockStocksTickerGet({
        path: { ticker },
      });
      return response.data;
    },
    {
      refreshInterval: 2000,
      revalidateOnFocus: false,
    }
  );

  return {
    stock: data,
    isLoading,
    isError: !!error,
    error,
    mutate,
  };
}

export function useStockSnapshots(ticker: string | null, limit = 100) {
  const { data, error, isLoading, mutate } = useSWR<StockSnapshotResponse[] | undefined>(
    ticker ? `snapshots-${ticker}-${limit}` : null,
    async () => {
      if (!ticker) return undefined;
      const response = await getStockSnapshotsStocksTickerSnapshotsGet({
        path: { ticker },
        query: { limit },
      });
      return response.data;
    },
    {
      refreshInterval: 5000,
      revalidateOnFocus: false,
    }
  );

  return {
    snapshots: data ?? [],
    isLoading,
    isError: !!error,
    error,
    mutate,
  };
}

// Swipe action helper (not a hook, but useful utility)
export async function submitSwipe(
  ticker: string,
  direction: SwipeDirection,
  swipeToken?: string | null
) {
  const response = await swipeSwipePost({
    body: {
      ticker,
      direction,
      swipe_token: swipeToken,
    },
  });

  if (response.error) {
    throw new Error('Swipe failed');
  }

  return response.data;
}
