import TerminalClient from "./terminal-client";

/**
 * The server component for the Terminal page.
 * It renders the `TerminalClient` which contains all the logic for the terminal display.
 * @returns {JSX.Element} The rendered terminal page component.
 */
export default function TerminalPage() {
    return (
        <div className="w-full h-full bg-black font-code">
            <TerminalClient />
        </div>
    )
}
