import os
import json
import re

os.makedirs("database", exist_ok=True)

documents_file = "database/documents.jsonl"
findings_file = "database/findings.jsonl"

# Clear existing files
open(documents_file, "w").close()
open(findings_file, "w").close()

doc_id = 1

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
    
    # Write document record
    document_record = {
        "id": doc_id,
        "source_file": filename,
        "reference_paper": reference_paper,
        "scratchpad": scratchpad
    }
    
    with open(documents_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(document_record, ensure_ascii=False) + "\n")
    
    # Write finding records
    for finding in findings:
        finding_record = {
            "document_id": doc_id,
            "parasite_species": finding.get("parasite_species", ""),
            "host_species": finding.get("host_species", ""),
            "country": finding.get("country", ""),
            "area": finding.get("area", ""),
            "confidence_score": finding.get("confidence_score", "")
        }
        
        with open(findings_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(finding_record, ensure_ascii=False) + "\n")
    
    print(f"Processed {filename} (ID: {doc_id}) - {len(findings)} finding(s)")
    doc_id += 1

print(f"\nDatabase created:")
print(f"  - {documents_file}")
print(f"  - {findings_file}")
