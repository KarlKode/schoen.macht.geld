import MarketMapClient from './market-map-client';

/**
 * The server component for the Market Map page.
 * It renders the `MarketMapClient` which handles the data fetching and visualization.
 * @returns {JSX.Element} The rendered market map page.
 */
export default function MarketMapPage() {
  return (
    <div className="w-full h-full p-4 bg-black">
      <MarketMapClient />
    </div>
  );
}
