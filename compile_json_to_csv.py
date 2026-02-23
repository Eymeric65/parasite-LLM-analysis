"""compile_json_to_csv.py

Utility: export all findings to a flat CSV for spreadsheet analysis.

Iterates every ``.json`` file in ``output/``, extracts the scratchpad and the
findings list, and writes one row per finding to
``output/compiled_findings.csv``.  Columns: source_file, reference_paper,
parasite_species, host_species, country, area, confidence_score, scratchpad.

This script is optional and independent of the main database pipeline.
"""
import os
import json
import csv
import re

output_csv = "output/compiled_findings.csv"

# CSV columns
fieldnames = [
    "source_file",
    "reference_paper",
    "parasite_species",
    "host_species",
    "country",
    "area",
    "confidence_score",
    "scratchpad"
]

with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    
    for filename in sorted(os.listdir("output")):
        if not filename.endswith(".json"):
            continue
        
        json_path = os.path.join("output", filename)
        
        with open(json_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Extract scratchpad
        scratchpad_match = re.search(r'<scratchpad>(.*?)</scratchpad>', content, re.DOTALL)
        scratchpad = scratchpad_match.group(1).strip() if scratchpad_match else ""
        
        # Extract JSON object
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if not json_match:
            print(f"Warning: No JSON found in {filename}")
            continue
        
        try:
            data = json.loads(json_match.group(1))
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON in {filename}: {e}")
            continue
        
        reference_paper = data.get("reference_paper", "")
        findings = data.get("findings", [])
        
        if not findings:
            print(f"Warning: No findings in {filename}")
            continue
        
        # Write one row per finding
        for finding in findings:
            writer.writerow({
                "source_file": filename,
                "reference_paper": reference_paper,
                "parasite_species": finding.get("parasite_species", ""),
                "host_species": finding.get("host_species", ""),
                "country": finding.get("country", ""),
                "area": finding.get("area", ""),
                "confidence_score": finding.get("confidence_score", ""),
                "scratchpad": scratchpad
            })
        
        print(f"Processed {filename} - {len(findings)} finding(s)")

print(f"\nCSV compiled to {output_csv}")
