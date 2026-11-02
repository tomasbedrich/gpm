#!/usr/bin/env bash
# Release a new patch version if anything shipped to users (custom_components/gpm) changed since the last release.

set -e

cd "$(dirname "$0")/.."

manifest=custom_components/gpm/manifest.json
last=$(git describe --tags --abbrev=0)

# Pin everything HA installs for users to what we tested with
changed=$(python3 - "$manifest" <<'PY'
import json, re, sys, tomllib
from pathlib import Path

manifest_path = Path(sys.argv[1])
manifest = json.loads(manifest_path.read_text())
locked = {p["name"]: p["version"] for p in tomllib.loads(Path("uv.lock").read_text())["package"] if "version" in p}
changed = []
for i, requirement in enumerate(manifest["requirements"]):
    name_with_extras = re.match(r"[^~=<>!;\s]+", requirement)[0]
    name = re.sub(r"[-_.]+", "-", name_with_extras.split("[")[0]).lower()
    pinned = f"{name_with_extras}~={locked[name]}"
    if pinned != requirement:
        manifest["requirements"][i] = pinned
        changed.append(pinned)
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
print(", ".join(changed))
PY
)
if [ -n "$changed" ]; then
    git commit -m "Require $changed" -- "$manifest"
fi

if git diff --quiet "$last" -- custom_components/gpm; then
    echo "Nothing changed for users since $last, skipping release"
    exit 0
fi

version=$(jq -r .version "$manifest")
new="${version%.*}.$((${version##*.} + 1))"
notes="## What's Changed
$(git log --reverse --format="* %s: https://github.com/$GITHUB_REPOSITORY/commit/%h" "$last"..HEAD -- custom_components/gpm)

**Full Changelog**: https://github.com/$GITHUB_REPOSITORY/compare/$last...$new"

jq --arg v "$new" '.version = $v' "$manifest" > "$manifest.tmp"
mv "$manifest.tmp" "$manifest"
git commit -m "Bump version" -- "$manifest"
git tag "$new"
git push --atomic origin HEAD:main "refs/tags/$new"

(cd custom_components/gpm && zip -r "$OLDPWD/gpm.zip" ./)
gh release create "$new" gpm.zip --title "$new" --notes "$notes"
