import LeaderboardClient from './leaderboard-client';

/**
 * The server component for the Leaderboard page.
 * It renders the `LeaderboardClient` component which handles the data fetching and display logic.
 * @returns {JSX.Element} The rendered leaderboard page.
 */
export default function LeaderboardPage() {
  return (
    <div className="w-full h-full bg-black font-sans">
      <LeaderboardClient />
    </div>
  );
}
