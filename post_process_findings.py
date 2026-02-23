"""post_process_findings.py

Step 4 of the pipeline: normalise and geocode findings.

Reads ``database/findings.jsonl`` and for every finding:

1. Splits multi-host ``host_species`` fields (comma/slash-separated).
2. Calls the GLM-4 API to parse composite ``area`` strings into individual
   geographic locations.
3. Geocodes each (area, country) pair via the Nominatim OpenStreetMap API
   (1 request/second rate limit respected).
4. Writes the expanded, geocoded records to
   ``database/post_process_findings.jsonl``.

Each finding is hashed (MD5) and cached under ``log/processed_findings/`` so
the script can be interrupted and safely resumed without re-querying APIs.

Requires:
    ZAI_KEY environment variable (loaded from .env via python-dotenv).
"""
import json
import re
import requests
import time
import hashlib
from zai import ZaiClient
from dotenv import load_dotenv
import os

load_dotenv()
client = ZaiClient(api_key=os.getenv("ZAI_KEY"))

# Setup checkpoint directory
CHECKPOINT_DIR = "log/processed_findings"
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

def get_finding_hash(finding):
    """Generate hash of finding for checkpoint identification"""
    # Create deterministic string from finding
    key_str = json.dumps(finding, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(key_str.encode()).hexdigest()

def load_checkpoint(finding_hash):
    """Load cached processed results if available"""
    checkpoint_file = os.path.join(CHECKPOINT_DIR, f"{finding_hash}.json")
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"  Warning: Failed to load checkpoint {finding_hash}: {e}")
    return None

def save_checkpoint(finding_hash, original_finding, processed_results):
    """Save processed results to checkpoint"""
    checkpoint_file = os.path.join(CHECKPOINT_DIR, f"{finding_hash}.json")
    checkpoint_data = {
        "original": original_finding,
        "processed": processed_results
    }
    with open(checkpoint_file, "w", encoding="utf-8") as f:
        json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)

AREA_EXTRACTION_PROMPT = """You are a geographic data parser. Given a country and an area field that may contain multiple locations separated by commas, semicolons, slashes, or "and", extract each distinct geographic area.

Output ONLY a valid JSON array of objects with this structure:
[
  {"country": "Country Name", "area": "Specific Area 1"},
  {"country": "Country Name", "area": "Specific Area 2"}
]

Rules:
- Split areas separated by commas, semicolons, slashes, or "and"
- Keep specific place names (bays, harbors, estuaries, coasts)
- If the area is vague like "northern coast" or just a region, keep it as-is
- Maintain correct country for each area
- Output ONLY the JSON array, no other text"""

def get_coordinates(area, country):
    """Get GPS coordinates using Nominatim OpenStreetMap API"""
    start_time = time.time()
    time.sleep(1)  # Rate limiting
    
    try:
        query = f"{area}, {country}"
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": query,
            "format": "json",
            "limit": 1
        }
        headers = {
            "User-Agent": "OysterParasiteAnalysis/1.0"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        results = response.json()
        
        elapsed = time.time() - start_time
        if results:
            print(f"    [Geocoding: {elapsed:.2f}s]")
            return {
                "latitude": float(results[0]["lat"]),
                "longitude": float(results[0]["lon"])
            }
        else:
            print(f"    [Geocoding: {elapsed:.2f}s - no results]")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"    [Geocoding: {elapsed:.2f}s - ERROR: {e}]")
    
    return {"latitude": None, "longitude": None}

def split_species(species_text):
    """Split species by comma or slash"""
    if not species_text:
        return []
    # Split by comma or slash, strip whitespace
    species_list = re.split(r'[,/]', species_text)
    return [s.strip() for s in species_list if s.strip()]

def extract_areas_with_llm(country, area):
    """Use LLM to extract individual areas from combined area field"""
    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model="glm-4-32b-0414-128k",
            messages=[
                {"role": "system", "content": AREA_EXTRACTION_PROMPT},
                {"role": "user", "content": f"Country: {country}\nArea: {area}"}
            ],
            temperature=0.1
        )
        
        content = response.choices[0].message.content.strip()
        
        # Extract JSON array from response
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            areas_data = json.loads(json_match.group(0))
            elapsed = time.time() - start_time
            print(f"  [LLM extraction: {elapsed:.2f}s - {len(areas_data)} area(s)]")
            return areas_data
        else:
            elapsed = time.time() - start_time
            print(f"  [LLM extraction: {elapsed:.2f}s - WARNING: Could not extract JSON]")
            return [{"country": country, "area": area}]
    
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"  [LLM extraction: {elapsed:.2f}s - ERROR: {e}]")
        return [{"country": country, "area": area}]

# Read findings
findings = []
with open("database/findings.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        findings.append(json.loads(line))

cache_hits = 0
cache_misses = 0
total_entries = 0
total_processing_time = 0.0

# Setup output file path (JSONL format)
output_file = "database/post_process_findings.jsonl"

for idx, finding in enumerate(findings, 1):
    finding_start = time.time()
    
    # Check cache first
    finding_hash = get_finding_hash(finding)
    cached_results = load_checkpoint(finding_hash)
    
    if cached_results:
        print(f"Processing finding {idx}/{len(findings)} [CACHED]...")
        new_processed = cached_results["processed"]
        cache_hits += 1
    else:
        print(f"Processing finding {idx}/{len(findings)} [NEW]...")
        cache_misses += 1
        
        document_id = finding["document_id"]
        parasite_species = finding["parasite_species"]
        host_species = finding["host_species"]
        country = finding["country"]
        area = finding["area"]
        confidence_score = finding["confidence_score"]
        
        # Split host species
        host_species_list = split_species(host_species)
        if not host_species_list:
            host_species_list = [host_species]
        
        # Extract areas using LLM
        areas_data = extract_areas_with_llm(country, area)
        
        # Create combinations
        new_processed = []
        for host in host_species_list:
            for area_data in areas_data:
                area_country = area_data["country"]
                area_name = area_data["area"]
                
                # Get coordinates
                coords = get_coordinates(area_name, area_country)
                
                processed_finding = {
                    "document_id": document_id,
                    "parasite_species": parasite_species,
                    "host_species": host,
                    "country": area_country,
                    "area": area_name,
                    "latitude": coords["latitude"],
                    "longitude": coords["longitude"],
                    "confidence_score": confidence_score
                }
                
                new_processed.append(processed_finding)
                print(f"  → {host} in {area_name}, {area_country} ({coords['latitude']}, {coords['longitude']})")
        
        # Save to checkpoint
        save_checkpoint(finding_hash, finding, new_processed)
    
    # Append each processed finding to JSONL file incrementally
    with open(output_file, "a", encoding="utf-8") as f:
        for entry in new_processed:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    total_entries += len(new_processed)
    finding_elapsed = time.time() - finding_start
    total_processing_time += finding_elapsed
    
    print(f"  [Finding completed in {finding_elapsed:.2f}s | Avg: {total_processing_time/(idx):.2f}s/finding]")
    
    if idx % 10 == 0:
        print(f"  [Progress: {total_entries} total entries saved | {idx}/{len(findings)} findings | Est. remaining: {(total_processing_time/idx)*(len(findings)-idx)/60:.1f}min]")

print(f"\nProcessed {len(findings)} findings into {total_entries} entries")
print(f"Cache hits: {cache_hits}, Cache misses: {cache_misses}")
print(f"Total processing time: {total_processing_time/60:.1f} minutes")
print(f"Average time per finding: {total_processing_time/len(findings):.2f}s")
print(f"Output saved to {output_file}")
