'use client';

import { useEffect, useState, useMemo } from 'react';
import { motion, useMotionValue, useTransform, animate } from 'framer-motion';
import Image from 'next/image';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Heart, X, Loader2 } from 'lucide-react';
import { useStocks, submitSwipe } from '@/hooks/use-stocks';
import type { SwipeDirection } from '@/lib/api/client';

/**
 * The main client component for the Swipe Kiosk.
 * This component is the engine of the market, allowing users to influence stock values.
 * It fetches stocks from the API, displays them as swipeable cards, and on swipe,
 * calls the backend to update the stock's value.
 */
export default function SwipeClient() {
  const { stocks, isLoading, mutate } = useStocks({ random: true });
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isTouchDevice, setIsTouchDevice] = useState(true);
  const [swipeToken, setSwipeToken] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // State to hold a stable, shuffled ORDER of stock tickers
  const [shuffledTickers, setShuffledTickers] = useState<string[]>([]);

  // Map stocks by ticker for efficient lookup
  const stocksByTicker = useMemo(() => {
    return new Map(stocks.map((stock) => [stock.ticker, stock]));
  }, [stocks]);

  // Effect to populate and shuffle the stock tickers only when stocks are added or removed
  useEffect(() => {
    if (stocks && stocks.length > 0) {
      const currentTickers = new Set(shuffledTickers);
      const newTickers = new Set(stocks.map((s) => s.ticker));
      if (currentTickers.size !== newTickers.size || ![...newTickers].every((t) => currentTickers.has(t))) {
        setShuffledTickers([...stocks].map((s) => s.ticker).sort(() => Math.random() - 0.5));
      }
    }
  }, [stocks]);

  // Detect if the device has touch capabilities
  useEffect(() => {
    setIsTouchDevice('ontouchstart' in window || navigator.maxTouchPoints > 0);
  }, []);

  // Framer Motion values for card animations
  const x = useMotionValue(0);
  const rotate = useTransform(x, [-200, 200], [-30, 30]);
  const opacity = useTransform(x, [-200, 0, 200], [0.5, 1, 0.5]);
  const likeOpacity = useTransform(x, [0, 100], [0, 1]);
  const nopeOpacity = useTransform(x, [-100, 0], [1, 0]);

  /**
   * Handles the swipe action, either from a drag gesture or a button click.
   * It animates the card off-screen and then calls the backend to update the stock.
   */
  const handleSwipe = async (direction: SwipeDirection) => {
    if (shuffledTickers.length === 0 || isSubmitting) return;

    const tickerToUpdate = shuffledTickers[currentIndex % shuffledTickers.length];
    if (!tickerToUpdate) return;

    setIsSubmitting(true);

    const exitX = direction === 'right' ? 300 : -300;
    animate(x, exitX, {
      duration: 0.3,
      onComplete: async () => {
        setCurrentIndex((prevIndex) => prevIndex + 1);
        x.set(0);

        try {
          const result = await submitSwipe(tickerToUpdate, direction, swipeToken);
          if (result) {
            setSwipeToken(result.swipe_token);
          }
          // Trigger refetch of stocks
          mutate();
        } catch (error) {
          console.error('Swipe failed:', error);
        } finally {
          setIsSubmitting(false);
        }
      },
    });
  };

  // Get the current stock from the stable shuffled list
  const currentStock = useMemo(() => {
    if (shuffledTickers.length === 0 || stocksByTicker.size === 0) return null;
    const currentTicker = shuffledTickers[currentIndex % shuffledTickers.length];
    return stocksByTicker.get(currentTicker) || null;
  }, [shuffledTickers, currentIndex, stocksByTicker]);

  if (isLoading && shuffledTickers.length === 0) {
    return (
      <div className="text-center flex flex-col items-center gap-4">
        <Loader2 className="w-12 h-12 animate-spin text-primary" />
        <h2 className="text-2xl font-bold">Lade Markt...</h2>
        <p className="text-muted-foreground">Die neusten Profile werden für dich vorbereitet.</p>
      </div>
    );
  }

  if (!currentStock) {
    return (
      <div className="text-center">
        <h2 className="text-2xl font-bold">Noch keine Aktien verfügbar!</h2>
        <p className="text-muted-foreground">
          Geh zur Admin-Seite, um die erste Aktie zu erstellen.
        </p>
      </div>
    );
  }

  const imageUrl = currentStock.image || '/placeholder.png';

  return (
    <div className="relative w-full h-full flex flex-col items-center justify-center">
      <div className="relative w-full h-full flex items-center justify-center">
        <motion.div
          key={currentStock.ticker}
          className="absolute w-[90vw] h-[80vh] max-w-sm max-h-[600px]"
          style={{ x, rotate, opacity, zIndex: 1 }}
          drag={isTouchDevice ? 'x' : false}
          dragConstraints={{ left: 0, right: 0, top: 0, bottom: 0 }}
          onDragEnd={(e, { offset }) => {
            if (offset.x > 100) {
              handleSwipe('right');
            } else if (offset.x < -100) {
              handleSwipe('left');
            } else {
              animate(x, 0, { type: 'spring', stiffness: 300, damping: 30 });
            }
          }}
          transition={{ duration: 0.3 }}
        >
          <Card className="relative w-full h-full overflow-hidden shadow-2xl shadow-black/20">
            <div className="absolute inset-0 w-full h-full">
              <Image
                src={imageUrl}
                alt={currentStock.title}
                data-ai-hint="person portrait"
                fill
                className="object-cover"
                priority
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />
            </div>

            <>
              <motion.div
                style={{ opacity: likeOpacity }}
                className="absolute top-8 left-8 rotate-[-30deg] border-4 border-green-400 text-green-400 text-5xl font-bold p-4 rounded-xl"
              >
                LIKE
              </motion.div>
              <motion.div
                style={{ opacity: nopeOpacity }}
                className="absolute top-8 right-8 rotate-[30deg] border-4 border-red-500 text-red-500 text-5xl font-bold p-4 rounded-xl"
              >
                NOPE
              </motion.div>
            </>

            <CardContent className="absolute bottom-0 left-0 right-0 p-6 text-white">
              <div className="flex items-baseline gap-4">
                <h2 className="text-4xl font-bold font-headline">{currentStock.title}</h2>
                <p className="text-2xl font-mono text-green-300">
                  {currentStock.price.toFixed(2)} CHF
                </p>
              </div>
              <p className="mt-2 text-lg text-white/80">{currentStock.description}</p>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <div className="flex gap-8 mt-4 z-50 absolute bottom-10">
        <Button
          variant="outline"
          className="w-24 h-24 rounded-full bg-white/10 backdrop-blur-sm border-red-500/50 text-red-500 hover:bg-red-500/20 hover:text-red-400"
          onClick={() => handleSwipe('left')}
          disabled={isSubmitting}
        >
          <X className="w-12 h-12" />
        </Button>
        <Button
          variant="outline"
          className="w-24 h-24 rounded-full bg-white/10 backdrop-blur-sm border-green-400/50 text-green-400 hover:bg-green-400/20 hover:text-green-300"
          onClick={() => handleSwipe('right')}
          disabled={isSubmitting}
        >
          <Heart className="w-12 h-12" />
        </Button>
      </div>
    </div>
  );
}
