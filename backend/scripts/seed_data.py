#!/usr/bin/env python3
"""
Seed script to populate the database with initial mock data.
Run with: python -m scripts.seed_data
"""

import asyncio
import httpx

BASE_URL = "http://localhost:8000"

PLACEHOLDER_IMAGES = [
    "https://images.unsplash.com/photo-1600180758890-6b94519a8ba6?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=400",
    "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=400",
    "https://images.unsplash.com/photo-1707156222575-bfb9e7daa3d8?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=400",
    "https://images.unsplash.com/photo-1654088041812-06b55e872a55?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=400",
    "https://images.unsplash.com/photo-1549541519-33d26f5b23f1?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=400",
    "https://images.unsplash.com/photo-1473830394358-91588751b241?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=400",
]

MOCK_STOCKS = [
    {
        "ticker": "CAPT",
        "title": "Captain-Chaos",
        "description": "Macht Geld wirklich schön? Dieses Profil stellt die These auf die Probe.",
        "initial_price": 100.0,
    },
    {
        "ticker": "DIAM",
        "title": "Diamond-Hands",
        "description": "Hält durch dick und dünn. Verkauft niemals. HODL forever.",
        "initial_price": 100.0,
    },
    {
        "ticker": "KRYP",
        "title": "Krypto-König",
        "description": "To the moon! Oder zum Boden. Wer weiss das schon.",
        "initial_price": 100.0,
    },
    {
        "ticker": "ALEX",
        "title": "Aktien-Alex",
        "description": "Diversifiziert wie ein Profi. Oder so ähnlich.",
        "initial_price": 100.0,
    },
    {
        "ticker": "BELL",
        "title": "Börsen-Bella",
        "description": "Die Königin des Parketts. Kauft hoch, verkauft höher.",
        "initial_price": 100.0,
    },
    {
        "ticker": "CHAM",
        "title": "Chart-Champion",
        "description": "Sieht Muster wo andere nur Linien sehen. Meistens.",
        "initial_price": 100.0,
    },
]


async def download_image(url: str) -> bytes:
    """Download image from URL and return bytes."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, follow_redirects=True)
        _ = response.raise_for_status()
        return response.content


async def create_stock(stock_data: dict[str, str | float], image_url: str) -> None:
    """Create a stock via the API."""
    async with httpx.AsyncClient() as client:
        # Download the image
        print(f"  Downloading image for {stock_data['ticker']}...")
        image_bytes = await download_image(image_url)

        # Create the stock with the image
        files = {
            "image": ("image.jpg", image_bytes, "image/jpeg"),
        }
        data = {
            "ticker": stock_data["ticker"],
            "title": stock_data["title"],
            "description": stock_data["description"],
            "initial_price": stock_data["initial_price"],
        }

        response = await client.post(
            f"{BASE_URL}/stocks/",
            data=data,
            files=files,
            timeout=30.0,
        )

        if response.status_code == 200:
            print(f"  Created: {stock_data['ticker']} - {stock_data['title']}")
        elif response.status_code == 400 and "already exists" in response.text:
            print(f"  Skipped (exists): {stock_data['ticker']}")
        else:
            print(f"  Failed: {stock_data['ticker']} - {response.status_code}: {response.text}")


async def main():
    print("Seeding database with mock stocks...")
    print()

    # Check if backend is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code != 200:
                print("Error: Backend is not healthy")
                return
    except httpx.ConnectError:
        print("Error: Cannot connect to backend at", BASE_URL)
        print("Make sure the backend is running: uvicorn src.app.main:app --reload")
        return

    for i, stock in enumerate(MOCK_STOCKS):
        image_url = PLACEHOLDER_IMAGES[i % len(PLACEHOLDER_IMAGES)]
        await create_stock(stock, image_url)

    print()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
