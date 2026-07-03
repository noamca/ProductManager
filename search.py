import json
import re

transcript_path = r"C:\Users\USER\.gemini\antigravity\brain\7d4505b9-c544-48e0-962c-06100e08b2c3\.system_generated\logs\transcript.jsonl"
keywords = ["credit", "קרדיט", "token", "עלות", "מחיר", "בזבז", "מתבזבז"]

results = []

with open(transcript_path, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        try:
            data = json.loads(line)
            content = str(data.get("content", ""))
            # Check if any keyword matches (exact word or contains it)
            matched_kws = [kw for kw in keywords if kw in content.lower()]
            if matched_kws:
                results.append(f"Line {i} matches {matched_kws}:")
                results.append(content[:1000])
                results.append("-" * 80)
        except Exception as e:
            pass

with open("search_results.txt", "w", encoding="utf-8") as out:
    out.write("\n".join(results))
