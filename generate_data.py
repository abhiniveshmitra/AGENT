import json
import os
import random
import uuid
from datetime import datetime, timedelta

# Configuration
OUTPUT_DIR = "jsonl_data"
NUM_FILES = 50
RECORDS_PER_FILE = 25
USER_NAMES = ["Jamie Torres", "Aryan Nayan-XT", "Mitra, Abhinivesh-XT", "More, Santosh", "Murali, Srinath-XT"]
ISSUES = ["Inactive Video Stream", "VideoFreezeDuration", "Audio Jitter", "Packet Loss", "High CPU Usage"]
SEVERITY = ["Low", "Medium", "High"]
PLATFORMS = ["CitrixVDI", "Windows", "MacOS", "Mobile"]

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_random_record():
    """Generates a single random call quality record."""
    user = random.choice(USER_NAMES)
    issue = random.choice(ISSUES)
    # Ensure some calls are clearly 'bad' for easier filtering
    is_bad_call = random.random() > 0.7  # 30% chance of a bad call
    
    return {
        "alert_id": str(uuid.uuid4()),
        "timestamp": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat() + "Z",
        "Level": "User Level",
        "Severity": random.choice(SEVERITY) if is_bad_call else "Low",
        "Source": "CQD",
        "call_id": str(uuid.uuid4()),
        "User": {
            "DisplayName": user,
            "email": f"{user.lower().replace(' ', '.').replace(',', '')}@example.com"
        },
        "Type": "Others",
        "Issue": issue,
        "Metric": issue.replace(" ", ""),
        "Description": f"User experienced {issue.lower()} during the call.",
        "Platform": random.choice(PLATFORMS)
    }

# Generate files
for i in range(NUM_FILES):
    file_path = os.path.join(OUTPUT_DIR, f"call_data_{i+1}.jsonl")
    with open(file_path, "w") as f:
        for _ in range(RECORDS_PER_FILE):
            record = create_random_record()
            f.write(json.dumps(record) + "\n")

print(f"Successfully generated {NUM_FILES} files in '{OUTPUT_DIR}'.")
