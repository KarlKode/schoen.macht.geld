import type { Stock } from './types';
import { PlaceHolderImages } from './placeholder-images';

const generateTicker = (name: string): string => {
  const sanitized = name.toUpperCase().replace(/[^A-Z]/g, '');
  if (sanitized.length >= 4) {
    return sanitized.slice(0, 4);
  }
  return sanitized.padEnd(4, 'X');
};

const initialNicknames = [
  'Captain-Chaos',
  'Diamond-Hands',
  'Krypto-König',
  'Aktien-Alex',
  'Börsen-Bella',
  'Chart-Champion',
];

export const mockStocks: Stock[] = initialNicknames.map((nickname, index) => {
  const initialValue = parseFloat((100 + (Math.random() - 0.5) * 20).toFixed(2));
  const image = PlaceHolderImages[index % PlaceHolderImages.length];

  return {
    id: `${index + 1}`,
    ticker: generateTicker(nickname),
    nickname: nickname,
    photoUrl: image.imageUrl,
    description:
      'KI generierte Beschreibung: Macht Geld wirklich schön? Dieses Profil stellt die These auf die Probe. Investieren Sie jetzt und finden Sie es heraus.',
    currentValue: initialValue,
    initialValue: initialValue,
    change: 0,
    percentChange: 0,
    history: [{ value: initialValue, timestamp: new Date().toISOString() }],
  };
});
