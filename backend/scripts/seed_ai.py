#!/usr/bin/env python3
"""
AI-powered seed script to generate and populate stocks.
Run with: python -m scripts.seed_ai [count]

Example:
    python -m scripts.seed_ai 10  # Generate 10 stocks
"""

import argparse
import asyncio
import json
import random
import re
import sys
from pathlib import Path

import httpx
from loguru import logger

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.services.ai import AIError, ai

BASE_URL = "https://smg.srv.ag/api"

# Placeholder images for stocks (used until AI image is applied)
PLACEHOLDER_IMAGES = [
    "https://images.unsplash.com/photo-1600180758890-6b94519a8ba6?w=400",
    "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=400",
    "https://images.unsplash.com/photo-1707156222575-bfb9e7daa3d8?w=400",
    "https://images.unsplash.com/photo-1654088041812-06b55e872a55?w=400",
    "https://images.unsplash.com/photo-1549541519-33d26f5b23f1?w=400",
    "https://images.unsplash.com/photo-1473830394358-91588751b241?w=400",
    "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400",
    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
]

# Prompt to generate stock data
STOCK_GENERATION_PROMPT = """Du bist ein kreativer Schreiber für das Zürcher Partyspiel "Schön. Macht. Geld.",
veranstaltet vom "Verein für ambitionierten Konsum (VAK)" im Club "Amphitheater".

Generiere {count} einzigartige, fiktive "Party-Persönlichkeiten" als Aktien.

Jede Person braucht:
1. **ticker**: Genau 4 Grossbuchstaben, idealerweise ein Wortspiel oder Bezug zum Namen.
   Beispiele: "COKE" für Schneewittchen, "FLEX" für Rolex-Rolf, "VIBE" für DJ Endorphin,
   "NOSE" für Powder-Paula, "GOLD" für Champagner-Charlotte.
2. **title**: Ein kreativer Aktientitel im Firmenformat.
   Beispiele: "Diamond Hands AG", "Krypto-König GmbH", "Influencer-Insolvenz Inc.",
   "Champagner-Charlotte Holdings", "DJ Endorphin Entertainment".
3. **description**: Eine sarkastische Beschreibung (max 500 Zeichen).

Regeln für Diversität:
- **Archetypen mischen:** DJ, Influencer, Banker, Künstler, Dealer, Erbin, Promoter,
  Model, Tech-Bro, Gastro-Besitzer, Türsteher, Stammgast, Newcomer.
- **Geschlecht/Stil variieren:** Nicht alle gleich.
- **Beschreibungsstile variieren:**
  - Ich-Perspektive (prahlerisch)
  - Corporate Mission Statement
  - Investor Pitch (Q3 Highlights)
  - Tagline (kurz, prägnant)

Beispiele für Beschreibungen:
- "Premium seit der Geburt. Exklusiv bis zum Blackout."
- "Think different. Sniff different."
- "Mission Statement: Wir maximieren hedonistische Rendite bei minimalem Verantwortungsbewusstsein."
- "Kerngeschäft: strategische Präsenz an exklusiven Locations. Wettbewerbsvorteil: Ich kenne den Türsteher."
- "Mein Portfolio besteht aus Vitamin K, fragwürdigen Entscheidungen und Menschen, die 'irgendwas mit Medien' machen."

Die Ticker müssen alle unterschiedlich sein!

Gib die Daten als JSON-Array aus:
[
  {{"ticker": "XXXX", "title": "Name-Name", "description": "..."}},
  ...
]

SEHR WICHTIG: Nur das JSON-Array, kein anderer Text."""

# Fallback prompt for description only
DESCRIPTION_PROMPT = """Du bist ein Ghostwriter für die exzessive Zürcher Partyszene und
schreibst witzige, bissige "Börsenprospekte" für das Partyspiel "Schön. Macht. Geld.".
Das Spiel wird vom "Verein für ambitionierten Konsum (VAK)" und dem Club "Amphitheater"
veranstaltet. Das Motto: hedonistischer Konsum, Macht, Schönheit und Drogen.

Schreibe eine sarkastische, ironische und prahlerische Profilbeschreibung für die Aktie,
basierend auf dem Aktientitel (Name der Person/Firma).

Aktientitel: {title}
Aktuelle Beschreibung (falls vorhanden): {description}
{image_attached_text}

Regeln:
1. **Stil:** Variiere zwischen verschiedenen Formaten:
   - Ich-Perspektive (prahlerisch, selbstverliebt)
   - Corporate Mission Statement (Unternehmensphilosophie-Parodie)
   - Investor Pitch (Q3 Highlights, Kerngeschäft, Prognosen)
   - Tagline (kurz, prägnant, memorable)
2. **Ton:** Selbstverliebt, sarkastisch, satirisch. Mische Finanzjargon mit Party-Slang.
3. **Themen:** Zürcher Nachtleben, Konsum, Status, Oberflächlichkeit, Exzesse,
   Networking, VIP-Kultur, fragwürdige Substanzen, Afterhours.
4. **Länge:** Maximal 500 Zeichen (inkl. Leerzeichen).
5. **Sprache:** Deutsch.
{image_attached_rule}

Beispiele (variiere den Stil!):
- "Mission Statement: Wir maximieren hedonistische Rendite bei minimalem Verantwortungs-
  bewusstsein. Unsere Kernkompetenz? Networking zwischen 2 und 6 Uhr morgens."
- "Unternehmensphilosophie: Move fast and break hearts. Unsere Stakeholder sind alle,
  die meine Nummer haben. Meine Shareholder sind alle, die sie gerne hätten."
- "Premium seit der Geburt. Exklusiv bis zum Blackout."
- "Think different. Sniff different."
- "Just do it. Frag nicht was."
- "The Future is Now. Der Kater ist Morgen."
- "Kerngeschäft: strategische Präsenz an exklusiven Locations. Wettbewerbsvorteil:
  Ich kenne den Türsteher. Risikohinweis: keiner."
- "Ich bin keine Investition – ich bin ein Lifestyle. Wer mich kauft, kauft Zugang
  zu Räumen, die auf keiner Karte existieren. Terms & Conditions: Es gibt keine."
- "Analyst*innen empfehlen: STRONG BUY. Meine Ex empfiehlt: SELL. Der Markt
  entscheidet. Der Markt bin ich."
- "Mein Portfolio besteht aus Vitamin K, fragwürdigen Entscheidungen und einem
  Netzwerk aus Menschen, die alle 'irgendwas mit Medien' machen. ROI? Return on
  Intoxication."
- "Mein Lebenswerk? Eine Studie in exzessiver Selbstüberschätzung, finanziert durch
  Vitamin B und den Glauben, dass Schlaf überbewertet ist. Kaufempfehlung: stark."

Gib nur die Beschreibung aus, keinen anderen Text."""


async def generate_stocks_batch(count: int) -> list[dict]:
    """Generate a single batch of stocks (max 10)."""
    prompt = STOCK_GENERATION_PROMPT.format(count=count)

    response_text = await ai.generate_text(prompt, max_tokens=8000)

    # Parse JSON from response
    json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    raise ValueError("No JSON array found in response")


async def generate_stocks_with_ai(count: int) -> list[dict]:
    """Generate stock data using AI in batches."""
    logger.info(f"Generating {count} stocks with AI...")

    batch_size = 10
    all_stocks = []
    remaining = count

    while remaining > 0:
        batch_count = min(batch_size, remaining)
        logger.info(f"  Generating batch of {batch_count}...")

        try:
            stocks = await generate_stocks_batch(batch_count)
            all_stocks.extend(stocks)
            remaining -= len(stocks)
        except (AIError, json.JSONDecodeError, ValueError) as e:
            logger.error(f"Batch generation failed: {e}")
            if not all_stocks:
                raise
            logger.warning("Continuing with partial results...")
            break

    return all_stocks


async def generate_description(title: str) -> str:
    """Generate a description for a single stock."""
    prompt = DESCRIPTION_PROMPT.format(title=title)

    try:
        return await ai.generate_text(prompt, max_tokens=800)
    except AIError:
        return f"Ich bin {title}. Mehr musst du nicht wissen."


async def download_image(url: str) -> bytes:
    """Download image from URL."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        return response.content


async def create_stock(stock_data: dict, image_url: str) -> bool:
    """Create a stock via the API. Returns True if successful."""
    ticker = stock_data.get("ticker", "")[:4].upper()
    title = stock_data.get("title", "Unknown")
    description = stock_data.get("description", "")

    # Validate ticker
    if len(ticker) != 4 or not ticker.isalpha():
        logger.warning(f"Invalid ticker '{ticker}', generating new one")
        ticker = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=4))

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Download image
            logger.debug(f"  Downloading image for {ticker}...")
            image_bytes = await download_image(image_url)

            # Create stock
            files = {"image": ("image.jpg", image_bytes, "image/jpeg")}
            data = {
                "ticker": ticker,
                "title": title,
                "description": description,
                "initial_price": round(random.uniform(50.0, 200.0), 2),
            }

            response = await client.post(
                f"{BASE_URL}/stocks/",
                data=data,
                files=files,
                timeout=30.0,
            )

            if response.status_code == 200:
                logger.info(f"  ✓ Created: {ticker} - {title}")
                return True
            elif response.status_code == 400 and "already exists" in response.text:
                logger.info(f"  ⊘ Skipped (exists): {ticker}")
                return False
            else:
                logger.error(
                    f"  ✗ Failed: {ticker} - {response.status_code}: {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"  ✗ Error creating {ticker}: {e}")
            return False


async def check_backend() -> bool:
    """Check if backend is running."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health", timeout=5.0)
            return response.status_code == 200
    except Exception:
        return False


async def main(count: int) -> None:
    print(f"\n🎰 AI Stock Seed - Generating {count} stocks\n")
    print("=" * 50)

    # Check backend
    if not await check_backend():
        print(f"\n❌ Cannot connect to backend at {BASE_URL}")
        print("   Make sure the backend is running:")
        print("   uvicorn src.app.main:app --reload --port 8080")
        return

    # Check API keys
    if not ai.is_configured():
        print("\n❌ No AI API keys configured!")
        print("   Set ATLASCLOUD_API_KEY or GOOGLE_AI_API_KEY in .env")
        return

    # Generate stocks with AI
    try:
        stocks = await generate_stocks_with_ai(count)
        print(f"\n✓ AI generated {len(stocks)} stock profiles\n")
    except Exception as e:
        print(f"\n❌ AI generation failed: {e}")
        return

    # Create stocks via API
    created = 0
    for i, stock in enumerate(stocks):
        image_url = PLACEHOLDER_IMAGES[i % len(PLACEHOLDER_IMAGES)]
        if await create_stock(stock, image_url):
            created += 1

    print("\n" + "=" * 50)
    print(f"✓ Created {created}/{len(stocks)} stocks")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate stocks using AI")
    parser.add_argument(
        "count",
        type=int,
        nargs="?",
        default=5,
        help="Number of stocks to generate (default: 5)",
    )
    args = parser.parse_args()

    if args.count < 1:
        print("Count must be at least 1")
        sys.exit(1)
    if args.count > 20:
        print("Warning: Generating more than 20 stocks may hit API limits")

    asyncio.run(main(args.count))
