# Nano Banana Pro API Integration

**Updated:** Task 11 - Switched from Flux to Nano Banana Pro API

---

## Overview

The tile generation script (`generate_tiles.py`) has been updated to use **Nano Banana Pro API** (via Google Gemini) instead of Flux. This uses the same API infrastructure as the existing Nano Banana implementation but optimized for text-to-image generation.

---

## Changes Made

### 1. Updated `generate_tiles.py`

**Added:**
- Nano Banana Pro API integration using `google.genai` client
- Direct text-to-image generation (no template images needed)
- Automatic fallback to regular Nano Banana if Pro not available
- Dry-run mode for prompt generation without API calls
- Configurable model selection

**Key Features:**
- Uses `gemini-2.0-flash-exp` model (Nano Banana Pro)
- Falls back to `gemini-3-pro-image-preview` if Pro unavailable
- Saves generated tiles as PNG files
- Saves prompts as JSON for manual retry on failures

---

## Usage

### Setup

1. **Install dependencies** (if not already installed):
   ```bash
   pip install google-genai python-dotenv pillow
   ```

2. **Set API key**:
   ```bash
   export GEMINI_API_KEY=your_api_key_here
   ```
   
   Or create a `.env` file:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

### Generate Tiles

**Dry Run (Prompts Only):**
```bash
cd isometric-nyc-main
$env:PYTHONPATH="src"
python -m isometric_hanford.generation.generate_tiles
```

**Actual Generation:**
```bash
# Set API key first
$env:GEMINI_API_KEY="your_key"
$env:PYTHONPATH="src"
python -m isometric_hanford.generation.generate_tiles
```

**With Custom Model:**
```python
from isometric_hanford.generation.generate_tiles import generate_all_snapshots

# Use specific model
generate_all_snapshots(
    dry_run=False,
    model="gemini-2.0-flash-exp"  # or "gemini-3-pro-image-preview"
)
```

---

## Model Options

### Nano Banana Pro (Recommended)
- **Model:** `gemini-2.0-flash-exp`
- **Features:** Faster, higher quality
- **Status:** Latest version

### Regular Nano Banana (Fallback)
- **Model:** `gemini-3-pro-image-preview`
- **Features:** Stable, proven for isometric generation
- **Status:** Used in existing NYC project

---

## Output Structure

```
output/tiles/hanford/
├── 1943/
│   ├── tiles/          # Generated PNG tiles
│   │   ├── 13/
│   │   │   ├── 1373_2891.png
│   │   │   └── ...
│   │   └── 14/
│   └── prompts/        # JSON prompts (for retry/failure cases)
│       ├── 13/
│       └── 14/
├── 1945/
├── 1964/
├── 1987/
├── 2000/
├── 2026/
├── 2070/
└── 2100/
```

---

## API Integration Details

### How It Works

1. **Prompt Generation:**
   - Creates prompts using `ManifestationPromptGenerator`
   - Includes reactor state, manifestation density, temporal context
   - Generates both positive and negative prompts

2. **API Call:**
   ```python
   response = client.models.generate_content(
       model="gemini-2.0-flash-exp",
       contents=[positive_prompt, negative_prompt],
       config=types.GenerateContentConfig(
           response_modalities=["TEXT", "IMAGE"],
           image_config=types.ImageConfig(aspect_ratio="1:1"),
       ),
   )
   ```

3. **Image Extraction:**
   - Extracts PIL Image from response
   - Resizes to tile size (256×256px default)
   - Saves as PNG

### Error Handling

- **API Key Missing:** Switches to dry-run mode automatically
- **Model Unavailable:** Falls back to regular Nano Banana
- **Generation Failure:** Saves prompt JSON for manual retry
- **Network Errors:** Logs error and continues with next tile

---

## Comparison: Flux vs Nano Banana Pro

| Feature | Flux | Nano Banana Pro |
|---------|------|-----------------|
| **API Type** | REST API | Google Gemini API |
| **Setup** | Requires API key + endpoint | Requires GEMINI_API_KEY only |
| **Model Access** | Via Modal or direct API | Via Google Cloud |
| **Generation Type** | Text-to-image | Text-to-image |
| **Quality** | High | High (Pro version) |
| **Speed** | Fast | Very fast (Flash model) |
| **Cost** | Pay-per-use | Pay-per-use |
| **Integration** | New setup needed | Already integrated in codebase |

---

## Advantages of Nano Banana Pro

1. **Already Integrated:** Uses same API client as existing Nano Banana code
2. **Proven:** Used successfully in NYC project
3. **Fast:** Flash model optimized for speed
4. **Simple:** Just need API key, no infrastructure setup
5. **Fallback:** Automatic fallback to regular Nano Banana

---

## Testing

### Test Prompt Generation (No API Calls)
```bash
# Dry run mode
python -m isometric_hanford.generation.generate_tiles
```

### Test Single Tile Generation
```python
from isometric_hanford.generation.generate_tiles import HanfordTileGenerator, TileGenerationConfig
from pathlib import Path

config = TileGenerationConfig(
    output_dir=Path("output/tiles/hanford"),
    zoom_levels=[13],
    dry_run=False,  # Set to True to skip API calls
)

generator = HanfordTileGenerator(config)
generator.generate_snapshot(2026)  # Generate one year
```

---

## Troubleshooting

### "GEMINI_API_KEY not found"
- Set environment variable: `export GEMINI_API_KEY=your_key`
- Or create `.env` file with the key

### "Model not available"
- Script automatically falls back to `gemini-3-pro-image-preview`
- Check Google Cloud Console for API access

### "No image in Gemini response"
- Check API quota/limits
- Verify API key has image generation permissions
- Try with regular Nano Banana model

### Generation Failures
- Prompts are saved to `prompts/` directory
- Can manually retry failed tiles
- Check API response text for error details

---

## Next Steps

1. **Get API Key:** Obtain Gemini API key from Google Cloud Console
2. **Test Generation:** Run with dry-run first to verify prompts
3. **Generate Sample:** Generate a few tiles to test quality
4. **Batch Generation:** Generate all 920 tiles (may take time/API quota)
5. **Quality Review:** Check generated tiles match prompt expectations

---

## Cost Considerations

- **Nano Banana Pro:** Pay-per-use pricing via Google Cloud
- **Rate Limits:** Check Google Cloud quotas
- **Batch Processing:** Consider rate limiting for large batches
- **Estimated Cost:** ~$0.01-0.05 per image (check current pricing)

---

**Status:** ✅ Nano Banana Pro integration complete. Ready for testing with API key.

