'use client';

import { Stock } from '@/lib/types';
import { useEffect, useState, useMemo } from 'react';
import { motion, useMotionValue, useTransform, animate } from 'framer-motion';
import Image from 'next/image';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Heart, X, Loader2 } from 'lucide-react';
import { useFirebase, useCollection, useMemoFirebase } from '@/firebase';
import { collection, doc, runTransaction, writeBatch, getDocs, WriteBatch } from 'firebase/firestore';
import { initiateAnonymousSignIn } from '@/firebase/non-blocking-login';
import { FirestorePermissionError, errorEmitter } from '@/firebase';

/**
 * The main client component for the Swipe Kiosk.
 * This component is the engine of the market, allowing users to influence stock values.
 * It fetches stocks from Firestore, displays them as swipeable cards, and on swipe,
 * runs a Firestore transaction to update the stock's value and history.
 * @returns {JSX.Element} The rendered swipe client component.
 */
export default function SwipeClient() {
  const { firestore, auth, user, isUserLoading } = useFirebase();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isTouchDevice, setIsTouchDevice] = useState(true);
  
  // State to hold a stable, shuffled ORDER of stock IDs.
  const [shuffledIds, setShuffledIds] = useState<string[]>([]);

  const titlesCollection = useMemoFirebase(() => firestore ? collection(firestore, 'titles') : null, [firestore]);
  const { data: stocks, isLoading: isLoadingStocks } = useCollection<Stock>(titlesCollection);

  // Map stocks by ID for efficient lookup. This map always has the latest data.
  const stocksById = useMemo(() => {
    if (!stocks) return new Map();
    return new Map(stocks.map(stock => [stock.id, stock]));
  }, [stocks]);


  // Effect to populate and shuffle the stock IDs only when stocks are added or removed.
  useEffect(() => {
    if (stocks && stocks.length > 0) {
      // Only re-shuffle if the set of IDs has actually changed.
      const currentIds = new Set(shuffledIds);
      const newIds = new Set(stocks.map(s => s.id));
      if (currentIds.size !== newIds.size || ![...newIds].every(id => currentIds.has(id))) {
         setShuffledIds([...stocks].map(s => s.id).sort(() => Math.random() - 0.5));
      }
    }
  }, [stocks]); // Depends on the full stocks array to detect additions/deletions.


  // Detect if the device has touch capabilities to enable/disable drag gestures.
  useEffect(() => {
    setIsTouchDevice('ontouchstart' in window || navigator.maxTouchPoints > 0);
  }, []);

  // Initiate anonymous sign-in if the user is not authenticated.
  // This is required to have write permissions to Firestore.
  useEffect(() => {
    if (!isUserLoading && !user && auth) {
      initiateAnonymousSignIn(auth);
    }
  }, [isUserLoading, user, auth]);

  // Framer Motion values for card animations.
  const x = useMotionValue(0);
  const rotate = useTransform(x, [-200, 200], [-30, 30]);
  const opacity = useTransform(x, [-200, 0, 200], [0.5, 1, 0.5]);
  const likeOpacity = useTransform(x, [0, 100], [0, 1]);
  const nopeOpacity = useTransform(x, [-100, 0], [1, 0]);

  /**
   * Handles the swipe action, either from a drag gesture or a button click.
   * It animates the card off-screen and then triggers a Firestore transaction
   * to update the stock's data.
   * @param {'left' | 'right'} direction - The direction of the swipe.
   */
  const handleSwipe = (direction: 'left' | 'right') => {
    if (!firestore || shuffledIds.length === 0) return;

    const stockIdToUpdate = shuffledIds[currentIndex % shuffledIds.length];
    if (!stockIdToUpdate) return;
    
    const exitX = direction === 'right' ? 300 : -300;
    animate(x, exitX, {
      duration: 0.3,
      onComplete: async () => {
        // Now that the animation is done, update the state and reset the card position.
        setCurrentIndex(prevIndex => prevIndex + 1);
        x.set(0);
        
        const valueChange = direction === 'right' ? 0.1 : -0.1;
        
        try {
          // Use a Firestore transaction to safely read and write the stock data.
          // This prevents race conditions if multiple users swipe the same stock at once.
           await runTransaction(firestore, async (transaction) => {
              const allDocsSnapshot = await getDocs(collection(firestore, 'titles'));
              const allStocks = allDocsSnapshot.docs.map(doc => ({ ...doc.data(), id: doc.id } as Stock));
              
              // 1. Get current ranks for all stocks before any changes.
              const stocksSortedByValue = [...allStocks].sort((a,b) => b.currentValue - a.currentValue);
              const previousRanks = new Map<string, number>();
              stocksSortedByValue.forEach((stock, index) => {
                previousRanks.set(stock.id, index + 1);
              });

              // 2. Find the specific stock we are updating.
              const currentStockDoc = allStocks.find(s => s.id === stockIdToUpdate);
              if (!currentStockDoc) {
                throw "Document does not exist!";
              }
              const currentData = currentStockDoc;

              // 3. Calculate all new values for the swiped stock.
              const now = new Date();
              const oneMinuteAgo = new Date(now.getTime() - 60 * 1000);
              const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000);

              const newValue = currentData.currentValue + valueChange;
              
              // 4. Create a list of all stocks with the updated value for the swiped one.
              const updatedStockListForRanking = allStocks.map(s => 
                s.id === stockIdToUpdate ? { ...s, currentValue: newValue } : s
              );

              // 5. Calculate the new ranks for all stocks.
              const newlySorted = updatedStockListForRanking.sort((a,b) => b.currentValue - a.currentValue);
              const newRanks = new Map<string, number>();
              newlySorted.forEach((stock, index) => {
                newRanks.set(stock.id, index + 1);
              });

              // 6. Use a batched write to update all documents.
              const batch = writeBatch(firestore);

              for (const stock of allStocks) {
                const stockRef = doc(firestore, 'titles', stock.id);
                let updateData: Partial<Stock> = {
                  rank: newRanks.get(stock.id),
                  previousRank: previousRanks.get(stock.id),
                };

                // If this is the stock that was swiped, add all the detailed value changes.
                if (stock.id === stockIdToUpdate) {
                    const newChange = newValue - stock.initialValue;
                    const newPercentChange = (newChange / stock.initialValue) * 100;
                    
                    let newHistory = [...stock.history, { value: newValue, timestamp: now.toISOString() }];
                    if (newHistory.length > 100) {
                      newHistory = newHistory.slice(newHistory.length - 100);
                    }

                    const recentHistory1Min = newHistory.filter((h) => new Date(h.timestamp) > oneMinuteAgo);
                    const oldestValueInLastMinute = recentHistory1Min.length > 1 ? recentHistory1Min[0].value : stock.currentValue;
                    const valueChangeLastMinute = newValue - oldestValueInLastMinute;

                    const recentHistory5Min = newHistory.filter((h) => new Date(h.timestamp) > fiveMinutesAgo);
                    const oldestValueInLast5Minutes = recentHistory5Min.length > 1 ? recentHistory5Min[0].value : stock.currentValue;
                    const valueChangeLast5Minutes = newValue - oldestValueInLast5Minutes;
                    const percentChangeLast5Minutes = (valueChangeLast5Minutes / newValue) * 100;
                    
                    updateData = {
                        ...updateData,
                        currentValue: newValue,
                        change: newChange,
                        percentChange: newPercentChange,
                        valueChangeLastMinute: valueChangeLastMinute,
                        valueChangeLast5Minutes: valueChangeLast5Minutes,
                        percentChangeLast5Minutes: percentChangeLast5Minutes,
                        history: newHistory,
                    };
                }
                
                batch.update(stockRef, updateData);
              }
              
              await batch.commit();
           });

        } catch (e) {
          console.error("Transaction failed: ", e);
          const stockRef = doc(firestore, 'titles', stockIdToUpdate);
          // If the transaction fails, create and emit a contextual error.
          const permissionError = new FirestorePermissionError({
            path: stockRef.path,
            operation: 'update',
            requestResourceData: { valueChange: valueChange }, // Send minimal context
          });
          errorEmitter.emit('permission-error', permissionError);
        }
      },
    });
  };

  // Get the current stock ID from the stable shuffled list, and then get the live data.
  const currentStock = useMemo(() => {
    if (shuffledIds.length === 0 || stocksById.size === 0) return null;
    const currentId = shuffledIds[currentIndex % shuffledIds.length];
    return stocksById.get(currentId) || null;
  }, [shuffledIds, currentIndex, stocksById]);

  const isLoading = isLoadingStocks || isUserLoading;

  if (isLoading && shuffledIds.length === 0) {
     return (
      <div className="text-center flex flex-col items-center gap-4">
        <Loader2 className="w-12 h-12 animate-spin text-primary" />
        <h2 className="text-2xl font-bold">Lade Markt...</h2>
        <p className="text-muted-foreground">
          Die neusten Profile werden für dich vorbereitet.
        </p>
      </div>
    );
  }

  if (!currentStock) {
    return (
      <div className="text-center">
        <h2 className="text-2xl font-bold">Noch keine Aktien verfügbar!</h2>
        <p className="text-muted-foreground">
          Geh zur Registrierungsstation, um die erste Aktie zu werden.
        </p>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full flex flex-col items-center justify-center">
      <div className="relative w-full h-full flex items-center justify-center">
        <motion.div
          key={currentStock.id}
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
                src={currentStock.photoUrl}
                alt={currentStock.nickname}
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
                <h2 className="text-4xl font-bold font-headline">
                  {currentStock.nickname}
                </h2>
                <p className="text-2xl font-mono text-green-300">
                  {currentStock.currentValue.toFixed(2)} CHF
                </p>
              </div>
              <p className="mt-2 text-lg text-white/80">
                {currentStock.description}
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <div className="flex gap-8 mt-4 z-50 absolute bottom-10">
          <Button
            variant="outline"
            className="w-24 h-24 rounded-full bg-white/10 backdrop-blur-sm border-red-500/50 text-red-500 hover:bg-red-500/20 hover:text-red-400"
            onClick={() => handleSwipe('left')}
            disabled={!user}
          >
            <X className="w-12 h-12" />
          </Button>
          <Button
            variant="outline"
            className="w-24 h-24 rounded-full bg-white/10 backdrop-blur-sm border-green-400/50 text-green-400 hover:bg-green-400/20 hover:text-green-300"
            onClick={() => handleSwipe('right')}
            disabled={!user}
          >
            <Heart className="w-12 h-12" />
          </Button>
        </div>
    </div>
  );
}
