#!/usr/bin/env python3
"""
scrape_multi_sport_rules.py
Downloads PDF rulebooks for multiple sports, extracts text, splits into sections,
and writes a combined rules.json for a tabbed static site.
/Users/madigan/madiganb55.github.io/scrape_rules.py
Dependencies:
    pip install requests pdfplumber tqdm
"""

import re
import json
import requests
import pdfplumber
from tqdm import tqdm
from pathlib import Path

# === CONFIG ===
# Add rulebook URLs for each Furman D1 sport
SPORTS_RULEBOOKS = {
    "Women's Lacrosse": "https://cdn1.sportngin.com/attachments/document/3c7d-3127216/WLRules2024_2025.pdf",
    
    # Football - check your conference or athletics department for PDF access
    # NCAA Publications page: https://www.ncaapublications.comuire purchase)
    # Men's: https://www.ncaapublications.com/p-4700-2024-25-ncaa-mens-basketball-rules-book.aspx
    # Women's: https://www.ncaapublications.com/p-4699-2024-25-ncaa-womens-basketball-rules-book.aspx
    "Men's Basketball": "https://cdn1.sportngin.com/attachments/document/e0d1-2810991/2023-2024_Mens_BBall_Rules_Book.pdf",
    "Women's Basketball": "https://ncaaorg.s3.amazonaws.com/championships/sports/basketball/d1/2024-25WBB_OfficialPlayingRules.pdf",
    
    
    
    # Soccer - https://www.ncaapublications.com/p-4692-2024-and-2025-soccer-rules.aspx
    "Men's Soccer": "https://cdn1.sportngin.com/attachments/document/18d0-3216650/2024-2025_Rule_Book.pdf",
    "Women's Soccer": "https://cdn1.sportngin.com/attachments/document/18d0-3216650/2024-2025_Rule_Book.pdf",
    
    # Volleyball - https://www.ncaapublications.com/p-4691-2024-and-2025-womens-volleyball-rules-book.aspx
    "Volleyball": "https://www.ncaapublications.com/productdownloads/VBR24.pdf",
    
    # Golf - USGA Rules apply, but NCAA has modifications
    "Men's Golf": "https://www.usga.org/rules/rules-and-clarifications/rules-and-clarifications.html#!ruletype=pe&section=rule&rulenum=1",
    "Women's Golf": "https://www.usga.org/rules/rules-and-clarifications/rules-and-clarifications.html#!ruletype=pe&section=rule&rulenum=1",
    
    # Tennis - USTA Rules apply with NCAA modifications
    "Men's Tennis": "https://ncaaorg.s3.amazonaws.com/championships/sports/tennis/rules/2022-23PRXTE_ITARulesBook.pdf",
    "Women's Tennis": "https://ncaaorg.s3.amazonaws.com/championships/sports/tennis/rules/2022-23PRXTE_ITARulesBook.pdf",

}

OUT_DIR = Path("output")
OUT_DIR.mkdir(exist_ok=True)
JSON_PATH = OUT_DIR / "rules.json"
# ==============

def download_pdf(url, dest_path):
    print(f"  Downloading from {url[:60]}...")
    try:
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with open(dest_path, "wb") as f, tqdm(total=total, unit='B', unit_scale=True, leave=False) as pbar:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        print(f"  ✓ Downloaded to {dest_path}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to download: {e}")
        return False

def extract_pages_text(pdf_path):
    pages = []
    print("  Extracting text from PDF pages...")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                pages.append(text)
        print(f"  ✓ Extracted {len(pages)} pages")
        return pages
    except Exception as e:
        print(f"  ✗ Failed to extract: {e}")
        return []

def join_pages(pages):
    joined = "\n\n".join(f"[PAGE {i+1}]\n{p}" for i, p in enumerate(pages))
    return joined

def split_into_sections(full_text):
    text = full_text.replace("—", " - ").replace("–", "-")
    
    heading_iter = list(re.finditer(
        r"(?:\n|^)\s*(RULE\s+\d+|Rule\s+\d+|SECTION\s+\d+|Section\s+\d+|ARTICLE\s+\d+|Article\s+\d+|"
        r"Points of Emphasis|Table Reference Sheet|Appendix|Interpretations|Definitions|"
        r"CHAPTER\s+\d+|Chapter\s+\d+)[^\n]*", 
        text, 
        flags=re.IGNORECASE
    ))
    
    if not heading_iter:
        return [{"title": "Full Document", "content": text[:5000], "start_page": 1}]
    
    items = []
    for idx, match in enumerate(heading_iter):
        start = match.start()
        title = match.group(0).strip()
        end = heading_iter[idx+1].start() if idx+1 < len(heading_iter) else len(text)
        content = text[match.end():end].strip()
        
        page_search = text.rfind("[PAGE", 0, start)
        page_num = None
        if page_search != -1:
            m = re.search(r"\[PAGE\s+(\d+)\]", text[page_search: start+1])
            if m:
                page_num = int(m.group(1))
        
        items.append({
            "title": re.sub(r"\s+", " ", title).strip(),
            "content": content,
            "start_page": page_num
        })
    
    return items

def make_snippet(s, n=200):
    txt = re.sub(r"\s+", " ", s).strip()
    return txt[:n] + ("…" if len(txt) > n else "")

def process_sport(sport_name, pdf_url):
    print(f"\n{'='*60}")
    print(f"Processing: {sport_name}")
    print('='*60)
    
    # Create filename from sport name
    filename = re.sub(r'[^\w\s-]', '', sport_name).replace(' ', '_').lower()
    pdf_path = OUT_DIR / f"{filename}.pdf"
    
    if not download_pdf(pdf_url, pdf_path):
        return None
    
    pages = extract_pages_text(pdf_path)
    if not pages:
        return None
    
    full_text = join_pages(pages)
    sections = split_into_sections(full_text)
    
    for i, s in enumerate(sections):
        s["id"] = f"{filename}-rule-{i+1}"
        s["snippet"] = make_snippet(s.get("content", ""))
        if "start_page" not in s:
            s["start_page"] = None
    
    print(f"  ✓ Processed {len(sections)} sections")
    
    return {
        "sport": sport_name,
        "source_url": pdf_url,
        "sections": sections
    }

def main():
    print("Multi-Sport Rulebook Scraper")
    print("="*60)
    
    all_sports_data = []
    
    for sport_name, pdf_url in SPORTS_RULEBOOKS.items():
        result = process_sport(sport_name, pdf_url)
        if result:
            all_sports_data.append(result)
    
    # Write combined JSON
    output_data = {
        "sports": all_sports_data,
        "generated_at": "2024-2025 season"
    }
    
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"✓ Successfully processed {len(all_sports_data)} sports")
    print(f"✓ Wrote combined data to {JSON_PATH}")
    print('='*60)

if __name__ == "__main__":
    main()
