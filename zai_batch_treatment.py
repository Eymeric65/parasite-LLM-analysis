from zai import ZaiClient
from dotenv import load_dotenv
import os
import base64
import csv
from PyPDF2 import PdfReader

load_dotenv()
client = ZaiClient(api_key=os.getenv("ZAI_KEY"))

# Load already processed files
processed = set()
if os.path.exists("output/token_usage.csv"):
    with open("output/token_usage.csv") as f:
        processed = {row[0] for row in csv.reader(f)}

for filename in os.listdir("input"):
    if not filename.endswith(".pdf") or filename in processed:
        continue
    
    file_path = f"input/{filename}"
    file_size = os.path.getsize(file_path)
    file_size_mb = file_size / (1024 * 1024)
    
    reader = PdfReader(file_path)
    num_pages = len(reader.pages)
    
    # Skip if exceeds limits: 50MB or 100 pages
    if file_size_mb > 50 or num_pages > 100:
        with open("output/skipped_pdf.txt", "a") as f:
            f.write(f"{filename} ({file_size_mb:.2f}MB, {num_pages} pages)\n")
        print(f"Skipped {filename} ({file_size_mb:.2f}MB, {num_pages} pages)")
        continue
    
    with open(file_path, "rb") as f:
        pdf_data_uri = f"data:application/pdf;base64,{base64.b64encode(f.read()).decode()}"
    
    print(f"Processing {filename} ({file_size_mb:.2f}MB, {num_pages} pages)...")
    response = client.layout_parsing.create(model="glm-ocr", file=pdf_data_uri)

    with open("output/token_usage.csv", "a") as f:
        f.write(f"\"{filename}\",{file_size_mb:.2f},{num_pages},{response.usage.total_tokens},{response.usage.prompt_tokens},{response.usage.completion_tokens}\n")

    output_file = os.path.join("output", os.path.splitext(filename)[0]+".md")
    
    with open(output_file, "w") as f:
        f.write(response.md_results)
