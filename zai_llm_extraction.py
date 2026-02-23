from zai import ZaiClient
from dotenv import load_dotenv
import os
import json
import csv

load_dotenv()
client = ZaiClient(api_key=os.getenv("ZAI_KEY"))

SYSTEM_PROMPT = """You are an expert marine biologist, parasitologist, and taxonomist. Your task is to extract highly precise relational data from OCR-processed academic papers regarding oyster parasites.

**Instructions:**
1. Read the provided OCR text of the academic paper carefully.
2. Identify all marine parasite species discussed as the *subject of the study* (ignore species only briefly mentioned in passing in the literature review unless they are part of the study's primary dataset).
3. For each parasite species, identify the corresponding Host (usually an oyster species), the Country where the study/sampling took place, and the specific Area (e.g., a specific bay, estuary, or coast).
4. Extract the primary Reference Paper (Title, Authors, Year) from the text.
5. Pay special attention to Latin binomial names (e.g., *Bonamia ostreae*, *Crassostrea gigas*). Correct minor OCR spelling artifacts only if you are 100% certain of the correct taxonomic name.

**Step 1: Scratchpad Analysis**
First, write a `<scratchpad>` detailing your thought process.
- Identify the paper's title and authors.
- List all potential parasites found in the text.
- Scan the "Materials and Methods" or "Study Site" section specifically to confidently link the location to the host and parasite.

**Step 2: JSON Output**
After your scratchpad, output a JSON object strictly matching this structure:
```json
{
  "reference_paper": "Author(s), Year. Title",
  "findings": [
    {
      "parasite_species": "Latin name of the parasite",
      "host_species": "Latin name of the host",
      "country": "Country of sampling",
      "area": "Specific bay/region/estuary",
      "confidence_score": "High/Medium/Low"
    }
  ]
}
```"""

# Load already processed files
processed = set()
if os.path.exists("output/llm_token_usage.csv"):
    with open("output/llm_token_usage.csv") as f:
        processed = {row[0] for row in csv.reader(f)}

# Process each markdown file
for filename in os.listdir("output"):
    if not filename.endswith(".md"):
        continue
    
    if filename in processed:
        print(f"Skipping {filename} (already processed)")
        continue
    
    md_path = os.path.join("output", filename)
    
    # Read markdown content
    with open(md_path, "r", encoding="utf-8") as f:
        ocr_text = f.read()
    
    print(f"Processing {filename}...")
    
    # Call chat completion API with GLM-5
    try:
        response = client.chat.completions.create(
            model="glm-5",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"**Input Document:**\n\n{ocr_text}"}
            ],
            temperature=0.1
        )
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        with open("output/llm_errors.txt", "a") as f:
            f.write(f"{filename}: {str(e)}\n")
        continue
    
    # Extract response
    content = response.choices[0].message.content
    
    # Save full response (with scratchpad)
    json_filename = os.path.splitext(filename)[0] + ".json"
    json_path = os.path.join("output", json_filename)
    
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    # Log token usage
    with open("output/llm_token_usage.csv", "a") as f:
        writer = csv.writer(f)
        writer.writerow([
            filename,
            response.usage.total_tokens,
            response.usage.prompt_tokens,
            response.usage.completion_tokens
        ])
    
    print(f"Completed {filename} - Tokens: {response.usage.total_tokens}")
