import StockChartClient from "./stock-chart-client";

/**
 * The server component for the Stock Chart page.
 * It renders the `StockChartClient` component which handles the data fetching
 * and visualization logic for the cycling stock charts.
 * @returns {JSX.Element} The rendered stock chart page.
 */
export default function StockChartPage() {
    return (
        <div className="w-full h-full bg-black font-sans">
            <StockChartClient />
        </div>
    )
}
