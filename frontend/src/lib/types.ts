export interface Stock {
  id: string;
  ticker: string;
  nickname: string;
  photoUrl: string;
  description: string;
  currentValue: number;
  initialValue: number;
  change: number;
  percentChange: number;
  valueChangeLastMinute: number;
  valueChangeLast5Minutes: number;
  percentChangeLast5Minutes: number;
  history: { value: number, timestamp: string }[];
  rank?: number;
  previousRank?: number;
}
