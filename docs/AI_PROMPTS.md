# AI Prompts Reference

This document preserves the AI prompts from the frontend (Genkit) for reference when consolidating AI functionality into the backend.

## Model Configuration

### Frontend (Genkit)
- **Provider**: Google Gemini via `@genkit-ai/google-genai`
- **Model**: `googleai/gemini-2.5-flash`
- **API Key**: `GEMINI_API_KEY` environment variable

### Backend (Current)
- **Provider**: AtlasCloud (configured in settings)
- **Models**:
  - Text: `settings.atlascloud_text_model`
  - Image: `settings.atlascloud_image_model`
  - Video T2V: `settings.atlascloud_video_t2v_model`
  - Video I2V: `settings.atlascloud_video_i2v_model`

---

## 1. Profile Description Generation

### Frontend Version (German, Party-Themed) - RECOMMENDED

**Purpose**: Generate satirical "stock prospectus" descriptions for party guests

**Input**:
```typescript
{
  nickname: string;      // Guest's nickname
  photoDataUri: string;  // Base64 data URI with MIME type
}
```

**Output**:
```typescript
{
  description: string;   // Max 350 characters, German
}
```

**Prompt** (German):
```
Du bist ein Ghostwriter für die exzessive Zürcher Partyszene und schreibst witzige, bissige "Börsenprospekte" in der Ich-Perspektive für das Partyspiel "Schön. Macht. Geld.". Das Spiel wird vom "Verein für ambitionierten Konsum (VAK)" und dem Club "Amphitheater" veranstaltet. Das Motto: hedonistischer Konsum, Macht, Schönheit und Drogen.

Schreibe eine sarkastische, ironische und prahlerische Profilbeschreibung in der Ich-Form, basierend auf dem Spitznamen und dem Foto der Person.

Spitzname: {{{nickname}}}
Foto: {{media url=photoDataUri}}

Regeln:
1.  **Perspektive:** Schreibe immer aus der Ich-Perspektive.
2.  **Ton:** Selbstverliebt, sarkastisch, satirisch. Mische Finanzjargon mit Party-Slang.
3.  **Themen:** Spiele mit Klischees über das Zürcher Nachtleben, Konsum, Status, Oberflächlichkeit und Exzesse.
4.  **Länge:** Maximal 350 Zeichen (inkl. Leerzeichen).
5.  **Sprache:** Deutsch.

Beispiel: "Mein Kurs? Steigt schneller als mein Puls nach der dritten Line. Ich bin keine Aktie, ich bin ein Gerücht, eine Legende auf dem Zürcher Parkett. Investier jetzt, bevor ich zu teuer für dein kleines Portfolio werde."
```

**Key Features**:
- First-person perspective ("Ich-Perspektive")
- Accepts photo for visual context (multimodal)
- Party-specific references (VAK, Amphitheater, Zürich nightlife)
- Mix of financial jargon and party slang
- 350 character limit

### Backend Version (English, Generic) - CURRENT

```python
DESCRIPTION_PROMPT = (
    "You are a satirical stock market analyst. Take this stock and make "
    "its description absurd, exaggerated, and funny while keeping it "
    "believable enough for a parody stock trading game.\n\n"
    "Stock: {title}\n"
    "Current description: {description}\n\n"
    "Write a new 2-3 sentence description that is ridiculous but "
    "entertaining. Only output the description, no other text."
)
```

**Recommendation**: Replace backend prompt with frontend version, adapted for non-multimodal use if image analysis isn't available.

---

## 2. News Headlines Generation (Batch)

### Frontend Version (German, Party-Themed)

**Purpose**: Generate 5 satirical news headlines about trending stocks

**Input**:
```typescript
{
  stocks: [
    {
      stockTicker: string;
      companyName: string;    // Person's nickname
      description: string;
      currentValue: number;
      change: number;
      percentChange: number;
    }
  ]  // Top 5 trending stocks
}
```

**Output**:
```typescript
{
  headlines: [string, string, string, string, string];  // Exactly 5
}
```

**Prompt** (German):
```
Du bist ein zynischer Finanzredakteur für ein Klatschblatt, das über das Börsen-Partyspiel "Schön. Macht. Geld." berichtet, veranstaltet vom "Verein für ambitionierten Konsum (VAK)" und "Amphitheater" in Zürich. Dein Publikum liebt Klatsch, dunklen Humor und ist fasziniert von der hedonistischen Party-Szene, Konsum, Drogen und der Absurdität, den Selbstwert an einen Aktienkurs zu koppeln.

Basierend auf den folgenden Informationen über die 5 volatilsten Aktien, generiere ein Set von genau 5 kurzen, schlagkräftigen und urkomischen Schlagzeilen. Jede Schlagzeile sollte für sich stehen. Der Ton sollte scharf, ironisch und voller Satire sein. Denk an eine Mischung aus Society-Klatsch und Finanz-Desaster.

Achte auf korrekte deutsche Rechtschreibung und die korrekte Verwendung von Umlauten (ä, ö, ü).

Hier sind die Daten der Top-Aktien:
{{#each stocks}}
- Börsenkürzel: {{{this.stockTicker}}}, Spitzname: {{{this.companyName}}}, Aktueller Wert: {{{this.currentValue}}} CHF, Veränderung: {{{this.change}}} CHF ({{{this.percentChange}}}%)
{{/each}}

Generiere 5 einzigartige Schlagzeilen. Sei provokant und einprägsam. Konzentriere dich auf Themen wie soziale Kletterei, vergänglichen Ruhm, schlechte Entscheidungen auf Partys, Exzesse im Zürcher Nachtleben und die Absurdität des Ganzen. Sei kreativ und nutze den Vibe von VAK und Amphitheater.
```

**Key Features**:
- Cynical financial editor persona
- References actual stock data (ticker, value, change)
- German with proper umlauts
- Themes: social climbing, fleeting fame, party excess, absurdity

**Note**: This prompt is defined in frontend but appears unused. Should be added to backend.

---

## 3. Image Generation

### Backend Version (Current)

```python
IMAGE_PROMPTS = {
    ImageType.MAIN: (
        "Corporate stock photo for {title}, professional but slightly off and weird"
    ),
    ImageType.LOGO: (
        "Minimalist corporate logo for {title}, clean vector style, simple design"
    ),
    ImageType.BILLBOARD: (
        "Highway billboard ad for {title} stock, dramatic and absurd"
    ),
    ImageType.WEBSITE: (
        "Screenshot of corporate website hero section for {title}, modern design"
    ),
}
```

**Note**: No frontend equivalent. Backend version is reasonable.

---

## 4. Video Generation

### Backend Version (Current)

```python
VIDEO_PROMPT = (
    "15-second stock market ad for {title}. Dramatic corporate style "
    "with text overlays showing rising stock prices. Slightly absurd tone."
)
```

**Note**: No frontend equivalent. Backend version is reasonable.

---

## Migration Recommendations

1. **Replace backend description prompt** with the German frontend version
   - Adapt for text-only if multimodal (photo) isn't supported
   - Keep 350 char limit

2. **Add headlines endpoint** to backend using the frontend prompt
   - New endpoint: `POST /ai/generate/headlines`
   - Input: top N volatile stocks
   - Output: array of headline strings

3. **Keep image/video prompts** as-is in backend

4. **Language**: All user-facing AI outputs should be German

5. **Model selection**: Consider using Gemini for text (better German) and keep AtlasCloud for image/video if that's the provider setup
