# generate_manifest.py

import os
import json

docs_dir = "docs"
manifest = []

for filename in sorted(os.listdir(docs_dir)):
    if filename.endswith(".json") and filename != "manifest.json":
        manifest.append({
            "file": filename,
            "label": filename.replace(".json", "")
        })

with open(os.path.join(docs_dir, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)

print(f"✅ Wrote {len(manifest)} entries to docs/manifest.json")
