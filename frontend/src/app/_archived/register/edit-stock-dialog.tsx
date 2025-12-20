'use client';

import { useState, useEffect } from 'react';
import type { Stock } from '@/lib/types';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useFirebase } from '@/firebase';
import { doc } from 'firebase/firestore';
import { updateDocumentNonBlocking } from '@/firebase/non-blocking-updates';
import { useToast } from '@/hooks/use-toast';
import { Loader2 } from 'lucide-react';

interface EditStockDialogProps {
  stock: Stock;
  isOpen: boolean;
  onClose: () => void;
}

/**
 * A dialog component for editing the details of a stock.
 * It allows modification of nickname, description, and current value.
 * @param {EditStockDialogProps} props - The component props.
 * @returns {JSX.Element} The rendered dialog component.
 */
export function EditStockDialog({ stock, isOpen, onClose }: EditStockDialogProps) {
  const [nickname, setNickname] = useState(stock.nickname);
  const [description, setDescription] = useState(stock.description);
  const [currentValue, setCurrentValue] = useState(stock.currentValue.toString());
  const [isSaving, setIsSaving] = useState(false);

  const { firestore } = useFirebase();
  const { toast } = useToast();

  // Reset form when a new stock is selected or the dialog is re-opened.
  useEffect(() => {
    if (stock) {
        setNickname(stock.nickname);
        setDescription(stock.description);
        setCurrentValue(stock.currentValue.toString());
    }
  }, [stock]);

  /**
   * Handles saving the updated stock data to Firestore.
   * If the current value is changed, it recalculates all dependent metrics.
   */
  const handleSave = () => {
    if (!firestore) return;
    setIsSaving(true);

    const updatedData: Partial<Stock> = {
      nickname,
      description,
    };

    const newCurrentValue = parseFloat(currentValue);
    // Check if the value is a valid number and has actually changed.
    if (!isNaN(newCurrentValue) && newCurrentValue !== stock.currentValue) {
      const now = new Date();
      const oneMinuteAgo = new Date(now.getTime() - 60 * 1000);
      const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000);

      // Add new entry to history and cap it at 100 entries.
      const newHistory = [...stock.history, { value: newCurrentValue, timestamp: now.toISOString() }];
      if (newHistory.length > 100) {
        newHistory.shift();
      }

      // Recalculate 1-minute and 5-minute changes.
      const recentHistory1Min = newHistory.filter(h => new Date(h.timestamp) > oneMinuteAgo);
      const oldestValueInLastMinute = recentHistory1Min.length > 0 ? recentHistory1Min[0].value : newCurrentValue;
      
      const recentHistory5Min = newHistory.filter(h => new Date(h.timestamp) > fiveMinutesAgo);
      const oldestValueInLast5Minutes = recentHistory5Min.length > 0 ? recentHistory5Min[0].value : newCurrentValue;

      // Populate updatedData with all new calculated fields.
      updatedData.currentValue = newCurrentValue;
      updatedData.change = newCurrentValue - stock.initialValue;
      updatedData.percentChange = (updatedData.change / stock.initialValue) * 100;
      updatedData.history = newHistory;
      updatedData.valueChangeLastMinute = newCurrentValue - oldestValueInLastMinute;
      updatedData.valueChangeLast5Minutes = newCurrentValue - oldestValueInLast5Minutes;
      updatedData.percentChangeLast5Minutes = (updatedData.valueChangeLast5Minutes / newCurrentValue) * 100;
    }

    const docRef = doc(firestore, 'titles', stock.id);
    updateDocumentNonBlocking(docRef, updatedData);

    // Give feedback after a short delay to feel more responsive.
    setTimeout(() => {
      toast({
        title: 'Titel aktualisiert',
        description: `Die Daten für ${nickname} wurden gespeichert.`,
      });
      setIsSaving(false);
      onClose();
    }, 1000);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Titel bearbeiten: {stock.nickname}</DialogTitle>
          <DialogDescription>
            Ändere die Details dieses Titels. Änderungen werden sofort auf allen Displays wirksam.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="nickname" className="text-right">
              Spitzname
            </Label>
            <Input
              id="nickname"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
              className="col-span-3"
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="currentValue" className="text-right">
              Wert
            </Label>
            <Input
              id="currentValue"
              type="number"
              value={currentValue}
              onChange={(e) => setCurrentValue(e.target.value)}
              className="col-span-3"
            />
          </div>
          <div className="grid grid-cols-4 items-start gap-4">
            <Label htmlFor="description" className="text-right pt-2">
              Beschreibung
            </Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="col-span-3"
              rows={5}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isSaving}>Abbrechen</Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Speichern
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
