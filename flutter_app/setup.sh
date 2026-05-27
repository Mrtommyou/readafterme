#!/usr/bin/env bash
set -euo pipefail

# Bootstrap a Flutter project with our custom Dart source files.
# Run this from the repo root: bash flutter_app/setup.sh

PROJECT="flutter_app"
NAME="read_after_me"
ORG="com.readafterme"

echo "==> Backing up custom Dart sources..."
TMP=$(mktemp -d)
cp -r "$PROJECT/lib" "$TMP/lib"
cp "$PROJECT/pubspec.yaml" "$TMP/pubspec.yaml"
cp "$PROJECT/analysis_options.yaml" "$TMP/analysis_options.yaml" 2>/dev/null || true

echo "==> Deleting old $PROJECT dir..."
rm -rf "$PROJECT"

echo "==> Creating fresh Flutter project..."
flutter create --project-name "$NAME" --org "$ORG" "$PROJECT"

echo "==> Restoring custom Dart sources..."
cp "$TMP/pubspec.yaml" "$PROJECT/pubspec.yaml"
cp -r "$TMP/lib" "$PROJECT/lib"

echo "==> Getting dependencies..."
cd "$PROJECT"
flutter pub get

echo "==> Done! Project is ready at $PROJECT/"
echo "    Build with: cd $PROJECT && flutter build apk --debug"
