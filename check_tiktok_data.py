
import json

with open("tiktok_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

default_scope = data.get("__DEFAULT_SCOPE__", {})
print("Keys in __DEFAULT_SCOPE__:", list(default_scope.keys()))
print("\nwebapp.video-detail keys:", list(default_scope.get("webapp.video-detail", {}).keys()))
print("\nwebapp.video-detail:", json.dumps(default_scope.get("webapp.video-detail", {}), indent=2))
