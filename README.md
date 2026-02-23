# Parasite LLM Analysis

Automated pipeline for extracting oyster-parasite findings from academic PDFs using LLMs (ZAI API / GLM models), with a Vue 3 + Vite interactive map published at **https://eymeric65.github.io/parasite-LLM-analysis/**.

## Pipeline Overview

```
input/*.pdf
    │
    ▼ zai_batch_treatment.py   (OCR via GLM-OCR)
output/*.md
    │
    ▼ zai_llm_extraction.py    (structured extraction via GLM-5)
output/*.json
    │
    ├─▶ compile_json_to_csv.py → output/compiled_findings.csv
    │
    └─▶ build_database.py      → database/documents.jsonl
                                  database/findings.jsonl
                                        │
                                        ▼ post_process_findings.py
                                  database/post_process_findings.jsonl
                                  (geocoded, species-split, area-parsed)
```

### Scripts

| Script | Description |
|---|---|
| `zai_batch_treatment.py` | Sends PDFs from `input/` to the GLM-OCR API (base64-encoded). Saves OCR output as `.md` files in `output/`. Skips files >50 MB or >100 pages. |
| `zai_llm_extraction.py` | Reads each `.md` in `output/`, prompts GLM-5 to extract parasite species, host species, country, area and confidence score. Saves the raw LLM response (scratchpad + JSON) as `.json` next to the `.md`. |
| `build_database.py` | Aggregates all `.json` output files into two JSONL files: `database/documents.jsonl` (one record per paper) and `database/findings.jsonl` (one record per finding). |
| `post_process_findings.py` | Enriches `database/findings.jsonl`: splits multi-host fields, uses LLM to split composite area strings, geocodes each area via Nominatim (OpenStreetMap). Results saved to `database/post_process_findings.jsonl`. Checkpoints each finding under `log/processed_findings/` to allow resuming. |
| `compile_json_to_csv.py` | Flattens all `.json` output files into a single `output/compiled_findings.csv` for quick spreadsheet inspection. |

## Setup

### Python

```bash
# Install dependencies
pip install -r requirements.txt

# Add your ZAI API key to .env
echo "ZAI_KEY=your_key_here" > .env
```

### ZAI / vLLM Server (OCR)

```bash
# Option A – Docker (GPU)
docker run --runtime nvidia --gpus all \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --env "HF_TOKEN=$HF_TOKEN" \
    -p 8000:8000 --ipc=host \
    vllm/vllm-openai:nightly \
    --model zai-org/GLM-OCR \
    --allowed-local-media-path / \
    --speculative-config '{"method": "mtp", "num_speculative_tokens": 1}' \
    --served-model-name glm-ocr

# Option B – vLLM CLI
vllm serve zai-org/GLM-OCR --allowed-local-media-path / --port 8090 --served-model-name glm-ocr
```

### Running the pipeline

```bash
python zai_batch_treatment.py   # 1. OCR PDFs → .md
python zai_llm_extraction.py    # 2. Extract findings → .json
python build_database.py        # 3. Build JSONL database
python post_process_findings.py # 4. Geocode & normalise findings
python compile_json_to_csv.py   # (optional) Export CSV
```

## Website (Vue 3 + Vite)

The interactive map is in `site/oyster-parasite-findings/`. It reads `database/post_process_findings.jsonl` to display geolocated parasite findings on a Leaflet map.

```bash
cd site/oyster-parasite-findings

npm install       # install dependencies
npm run dev       # start dev server (http://localhost:5173)
npm run build     # build for production → dist/
npm run preview   # preview production build locally
```

The `public/database` directory is symlinked to the project `database/` folder so the dev server reads live data without copying files.

Deployed to GitHub Pages via the `dist/` output.
