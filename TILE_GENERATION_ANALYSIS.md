# Isometric-NYC Tile Generation Pipeline Analysis

**Date:** January 2025  
**Analysis Scope:** Understanding data requirements and generation methodology

---

## 1. Files in `src/isometric_hanford/generation/`

The generation directory contains **49 Python files** covering the full tile generation pipeline:

### Core Generation Scripts
- `generate_tile_omni.py` - Generate tiles using Oxen.ai Omni model
- `generate_tile_nano_banana.py` - Generate tiles using Gemini Nano Banana model
- `generate_omni.py` - Reusable library for Omni generation (used by CLI and web app)
- `generate_template.py` - Template building for infill generation
- `infill_template.py` - Infill region and template builder utilities

### Data Management
- `get_tile_data.py` - Extract render and generation images for tiles
- `shared.py` - Shared utilities (database ops, web server, image processing)
- `queue_db.py` - Generation queue management
- `seed_tiles.py` - Seed initial tiles

### Export & Visualization
- `export_dzi.py` - Export tiles to DZI format
- `export_pmtiles.py` - Export to PMTiles format
- `export_tile.py` - Export individual tiles
- `view_generations.py` - Web viewer for generations
- `visualize_bounds.py` - Visualize geographic bounds

### Web Application
- `app.py` - Main Flask web app for interactive generation (2,400+ lines)
- `web_renderer.py` - Web-based rendering utilities

### Model Configuration
- `model_config.py` - Model configuration management (Modal, Oxen, Nano Banana)
- `app_config.json` - Active model configurations

### Specialized Generation
- `generate_water_masks.py` - Water mask generation
- `generate_dark_mode.py` - Dark mode variant generation
- `generate_layer_snow.py` - Snow layer generation
- `generate_full_map_layer.py` - Full map layer generation

### Planning & Automation
- `make_strip_plan.py` - Create strip-based generation plans
- `make_rectangle_plan.py` - Create rectangle-based generation plans
- `automatic_generation.py` - Automated batch generation

### Utilities
- `bounds.py` - Geographic bounds management
- `temporal_tiles.py` - Temporal snapshot management
- `image_preprocessing.py` - Image preprocessing utilities
- `pixel_art_postprocess.py` - Post-processing for pixel art
- `replace_color.py` - Color replacement utilities
- `detect_water_tiles.py` - Water tile detection
- `check_tiles.py` - Tile validation
- `clear_generations.py` - Clear generation data

---

## 2. Modal Deployment Script

**Location:** `inference/server.py`

**Purpose:** Deploys a fine-tuned Qwen-Image-Edit model on Modal.com for inference

**Key Features:**
- Uses Modal's serverless GPU infrastructure (H100 GPUs)
- Loads LoRA adapters from Modal volumes (`/data/loras/<model-id>/`)
- Provides base64-encoded image editing endpoint
- Supports multiple model variants via `LORA_MODEL_ID` environment variable

**Deployment:**
```bash
# Development (hot-reload)
uv run modal serve inference/server.py

# Production
uv run modal deploy inference/server.py

# With specific model
LORA_MODEL_ID=another-model-id uv run modal deploy inference/server.py
```

**Configuration:**
- Default model: `cannoneyed-dark-copper-flea`
- Endpoint URL stored in `MODAL_INFERENCE_URL` environment variable
- Model configurable via `app_config.json` with `model_type: "url"`

**Setup Steps** (from `inference/README.md`):
1. Download LoRA weights from Oxen
2. Create Modal volume: `uv run modal volume create isometric-lora-vol`
3. Upload weights: `uv run modal volume put isometric-lora-vol lora-weights/models/<model-id> /loras/<model-id>`
4. Deploy server
5. Set `MODAL_INFERENCE_URL` to the endpoint URL

---

## 3. Example Generation Commands

### Using Omni Model (Oxen.ai)
```bash
# Generate a 2x2 tile anchored at (0,0)
uv run python src/isometric_hanford/generation/generate_tile_omni.py \
  generations/nyc 0 0

# Generate single quadrant with context
uv run python src/isometric_hanford/generation/generate_tile_omni.py \
  generations/nyc 0 0 --target-position br
```

### Using Nano Banana (Gemini)
```bash
# Generate a 2x2 tile
uv run python src/isometric_hanford/generation/generate_tile_nano_banana.py \
  generations/nyc 0 0

# Generate arbitrary quadrants with auto context
uv run python src/isometric_hanford/generation/generate_tile_nano_banana.py \
  generations/nyc --quadrants "(0,0),(1,0),(0,1)"

# With reference tiles for style
uv run python src/isometric_hanford/generation/generate_tile_nano_banana.py \
  generations/nyc 0 0 --references "(0,0)" "(2,0)"

# With custom prompt
uv run python src/isometric_hanford/generation/generate_tile_nano_banana.py \
  generations/nyc 0 0 --prompt "Add more trees"
```

### Web App Generation
```bash
# Start the web app
uv run python src/isometric_hanford/generation/app.py

# Then use the web UI at http://localhost:5000
# - Select quadrants
# - Click "Generate"
# - Choose model (Modal/Oxen/Nano Banana)
```

### Extract Tile Data
```bash
# Get render and generation images for a tile
uv run python src/isometric_hanford/generation/get_tile_data.py \
  generations/nyc 0 0 --output-dir ./exports
```

---

## 4. Tile Generation Pipeline Overview

### Data Flow

```
1. Geographic Data (lat/lng bounds)
   ↓
2. Quadrant Database (SQLite: quadrants.db)
   ├── quadrants table (lat, lng, render, generation, etc.)
   └── metadata table (generation config)
   ↓
3. 3D Render Generation
   ├── Web render server (Playwright + Cesium)
   ├── Camera parameters (azimuth, elevation, view_height)
   └── Render saved as PNG blob in database
   ↓
4. Template Construction
   ├── Infill region calculation
   ├── Context quadrant detection
   ├── Render pixels + existing generation pixels
   └── Red border marking infill area
   ↓
5. AI Model Inference
   ├── Modal (Qwen-Image-Edit + LoRA)
   ├── Oxen.ai (fine-tuned models)
   └── Nano Banana (Gemini 3 Pro)
   ↓
6. Post-processing
   ├── Extract quadrants from generated image
   ├── Resize to 512x512 per quadrant
   └── Save PNG blobs to database
   ↓
7. Export
   ├── DZI format (for web viewer)
   ├── PMTiles format
   └── Individual PNG exports
```

### Key Components

**1. Database Schema (`quadrants.db`):**
- `quadrants` table: Stores lat/lng, render PNG, generation PNG, flags, water masks
- `metadata` table: Generation config (camera params, bounds, etc.)
- `generation_queue` table: Queue for batch generation

**2. Template Building:**
- Uses `InfillRegion` and `TemplateBuilder` classes
- Constructs 1024x1024px template with:
  - Existing generation pixels (for context)
  - Render pixels (for infill area)
  - Red border marking infill region
- Supports expansion for seamless generation

**3. Model Integration:**
- **Modal:** Base64 JSON API (`/edit_b64` endpoint)
- **Oxen:** REST API (`https://hub.oxen.ai/api/images/edit`)
- **Nano Banana:** Gemini API with file uploads

**4. Generation Rules:**
- 2x2 tiles: Only legal if not touching existing generations
- 1x2 or 2x1: Legal if adjacent to existing generations
- Context quadrants: Automatically calculated from adjacent generated tiles

---

## 5. How NYC Project Generated Tiles

### Original Methodology

**1. Initial Generation (Nano Banana):**
- Used Gemini Nano Banana (gemini-3-pro-image-preview) for initial tile generation
- Created render→generation pairs
- Notebook: `src/notebooks/nano-banana.py` (Marimo notebook)

**2. Synthetic Dataset Creation:**
- Created "omni" infill datasets from render→generation pairs
- Multiple dataset versions (v01, v02, v03, v04)
- Scripts: `src/isometric_hanford/synthetic_data/create_infill_examples.py`
- Dataset types:
  - Full generation (20%)
  - Quadrant generation (20%)
  - Half generation (20%)
  - Middle strips (15%)
  - Rectangle strips (10%)
  - Rectangle infills (15%)

**3. Model Fine-tuning:**
- Fine-tuned Qwen-Image-Edit models on Oxen.ai
- Models trained on "omni" infill task
- Key models:
  - `cannoneyed-dark-copper-flea` (water tiles)
  - `cannoneyed-quiet-green-lamprey` (more trees)
  - `cannoneyed-rural-rose-dingo` (water v2)

**4. Production Generation:**
- Used fine-tuned models via Oxen API
- Also deployed on Modal for faster inference
- Generated ~32,000 tile quadrants
- Stored in SQLite database (`quadrants.db`)

**5. Data Storage:**
- Database: SQLite with PNG blobs
- Exported to: Oxen.ai repository (`cannoneyed/isometric-nyc-tiles`)
- Format: `<xxx>_<yyy>_<hash>.png` files
- Metadata: `generation_config.json` with lat/lng and camera params

### Key Differences from Hanford Project

**NYC:**
- Pre-generated all tiles
- Used fine-tuned models
- Stored in Oxen.ai repository
- Full coverage of Manhattan area

**Hanford (Current):**
- Placeholder tiles generated (`generate_placeholder_tiles.py`)
- Ready for AI generation but not yet generated
- Temporal snapshots (1943-2100)
- Focus on reactor corridor (~89 sq mi vs NYC's larger area)

---

## 6. Data Requirements Summary

### Required Inputs

**1. Geographic Data:**
- Bounds (north, south, east, west)
- Center coordinates (lat, lng)
- Quadrant grid definition

**2. Database:**
- SQLite database (`quadrants.db`)
- `quadrants` table with columns:
  - `quadrant_x`, `quadrant_y` (coordinates)
  - `lat`, `lng` (geographic position)
  - `render` (PNG blob - 3D render)
  - `generation` (PNG blob - AI-generated pixel art)
  - Flags: `is_water`, `starred`, `flagged`, `is_reference`

**3. Generation Config:**
- Camera parameters (azimuth, elevation, view_height)
- Tile dimensions (width_px, height_px)
- Model configuration (`app_config.json`)

**4. Web Render Server:**
- Cesium-based 3D renderer
- Playwright for headless rendering
- Generates orthographic isometric views

**5. Model Access:**
- **Modal:** `MODAL_INFERENCE_URL` environment variable
- **Oxen:** `OXEN_MODEL_API_KEY` environment variable
- **Nano Banana:** `GEMINI_API_KEY` environment variable

### Output Format

**Per Quadrant:**
- 512×512px PNG image
- Stored as BLOB in database
- Can be exported as individual files

**Per Tile (2×2 quadrants):**
- 1024×1024px stitched image
- Used for generation context
- Exported to DZI/PMTiles for web viewing

---

## 7. Key Files Reference

| File | Purpose |
|------|---------|
| `generate_tile_omni.py` | CLI for Omni model generation |
| `generate_tile_nano_banana.py` | CLI for Nano Banana generation |
| `generate_omni.py` | Reusable Omni generation library |
| `app.py` | Web app for interactive generation |
| `shared.py` | Shared utilities (DB, web server, images) |
| `infill_template.py` | Template building logic |
| `model_config.py` | Model configuration management |
| `inference/server.py` | Modal deployment script |
| `get_tile_data.py` | Extract tile data for export |
| `export_dzi.py` | Export to DZI format |

---

## 8. Next Steps for Hanford Generation

Based on this analysis, to generate tiles for Hanford:

1. **Initialize Generation Database:**
   - Create `generations/hanford/quadrants.db`
   - Populate with quadrant coordinates and lat/lng
   - Set generation config (camera params, bounds)

2. **Render Initial Tiles:**
   - Use web render server to generate 3D renders
   - Save render PNGs to database

3. **Generate Seed Tiles:**
   - Generate initial reference tiles using Nano Banana
   - Mark as `is_reference=1` in database

4. **Batch Generation:**
   - Use fine-tuned models (Modal/Oxen) for production
   - Generate tiles following generation rules
   - Use reference tiles for style consistency

5. **Export:**
   - Export to DZI format for web viewer
   - Replace placeholder tiles with generated tiles

---

**End of Analysis**

