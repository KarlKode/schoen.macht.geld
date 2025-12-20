// Re-export all generated client functions and types
export * from './client';
export { client } from './client/client.gen';

// Configure base URL based on environment
// In production: Caddy proxies /api/* to backend
// In development: direct to backend at localhost:8000
import { client } from './client/client.gen';

const baseUrl = typeof window !== 'undefined'
  ? (process.env.NEXT_PUBLIC_API_URL || '/api')
  : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');

client.setConfig({ baseUrl });
