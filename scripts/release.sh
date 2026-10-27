#!/usr/bin/env bash
# Release a new patch version if anything shipped to users (custom_components/gpm) changed since the last release.

set -e

cd "$(dirname "$0")/.."

manifest=custom_components/gpm/manifest.json
last=$(git describe --tags --abbrev=0)

gitpython=$(python3 -c 'import tomllib; print(next(p["version"] for p in tomllib.load(open("uv.lock", "rb"))["package"] if p["name"] == "gitpython"))')
jq --arg v "$gitpython" '.requirements |= map(if startswith("GitPython") then "GitPython~=" + $v else . end)' "$manifest" > "$manifest.tmp"
mv "$manifest.tmp" "$manifest"
if ! git diff --quiet -- "$manifest"; then
    git commit -m "Require GitPython~=$gitpython" -- "$manifest"
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
