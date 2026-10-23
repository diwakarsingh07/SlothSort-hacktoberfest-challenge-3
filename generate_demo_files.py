"""
SlothSort Demo Clutter Generator
Generates realistic chaotic files in demo_messy_folder for instant 1-click testing.
"""

import os
from pathlib import Path

def create_sample_files(target_dir: str):
    dir_path = Path(target_dir)
    dir_path.mkdir(parents=True, exist_ok=True)

    samples = {
        "INV_98242_oct_final_v2.txt": """ACME Cloud Services
INVOICE #98242
Date: 2026-10-15
Billed To: Diwakar Enterprises
Description: Monthly GPU Cluster Compute Instance (A100)
Subtotal: $420.00
Tax: $33.60
Total Amount Due: $453.60
Status: Paid via MasterCard ending in 9811
Thank you for your business!""",

        "coffee_shop_bill_scan.txt": """BLUE BOTTLE COFFEE
Store #104 - San Francisco
Date: 2026-10-18 09:14 AM
1x Oat Milk Latte ($6.50)
1x Almond Croissant ($4.75)
Receipt Total: $11.25
Tip: $2.00
Payment Method: Apple Pay""",

        "my_updated_resume_draft_FINAL(1).txt": """John Doe - Senior Machine Learning Engineer
Email: john.doe@example.com | Portfolio: github.com/johndoe
Summary: 6+ years experience building open-source AI agent frameworks,
fine-tuning open-weight models, and optimizing local inference with Ollama and llama.cpp.
Experience:
- Staff AI Engineer at OpenTech (2023 - Present)
- ML Research Engineer at DeepScale (2020 - 2023)
Education: B.S. in Computer Science""",

        "quick_notes_thursday_sync.md": """# Engineering All-Hands Sync
Date: October 19, 2026
Attendees: Alice, Bob, Diwakar, Chloe

Agenda & Discussion:
- Discussed migration from cloud APIs to local Ollama inference for zero latency and privacy.
- International Sloth Day theme launched: team loves the Slow & Steady motto.
- Action Items:
  * Diwakar to finalize SlothSort demo dashboard.
  * Bob to test vision pipeline on multimodal receipts.""",

        "temp_fix_database_conn.py": """import sqlite3

def get_connection(db_name="sloth_cache.db"):
    # Lazy connection helper for persistent cache
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    return conn

if __name__ == "__main__":
    print("Database connection verified.")
""",

        "quarterly_churn_stats_2026_q3.csv": """customer_id,signup_date,plan,mrr,churned
1001,2026-01-15,Enterprise,1200,False
1002,2026-02-20,Pro,250,False
1003,2026-03-01,Starter,49,True
1004,2026-04-12,Enterprise,1800,False""",

        "Screenshot 2026-10-21 at 2.45.19 PM.png": "SIMULATED_PNG_BINARY_DATA",
        "Screenshot_error_traceback_404.png": "SIMULATED_PNG_BINARY_DATA",
        "dank_programmer_meme_about_yaml.png": "SIMULATED_PNG_BINARY_DATA",
        "backup_project_assets_october.zip": "SIMULATED_ZIP_CONTENT",
        "vlc_player_installer_v3.4.exe": "SIMULATED_EXE_CONTENT"
    }

    created = []
    for filename, content in samples.items():
        file_path = dir_path / filename
        if filename.endswith(".png") or filename.endswith(".zip") or filename.endswith(".exe"):
            with open(file_path, "wb") as f:
                f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" if filename.endswith(".png") else b"PK\x03\x04" if filename.endswith(".zip") else b"MZ\x90\x00")
        else:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        created.append(str(file_path))

    return created

if __name__ == "__main__":
    base = Path(__file__).parent / "demo_messy_folder"
    created = create_sample_files(str(base))
    print(f"Created {len(created)} sample clutter files in {base}")
