import json

transcript_path = r"C:\Users\USER\.gemini\antigravity\brain\7d4505b9-c544-48e0-962c-06100e08b2c3\.system_generated\logs\transcript.jsonl"
results = []

with open(transcript_path, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        try:
            data = json.loads(line)
            content = str(data.get("content", ""))
            if "Brand select details" in content:
                results.append(f"Line {i}:")
                idx = content.find("Brand select details")
                results.append(content[idx:idx+3000])
                results.append("=" * 80)
        except Exception as e:
            pass

with open("brand_details_utf8.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(results))

print("Done")
