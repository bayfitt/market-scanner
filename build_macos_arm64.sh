#!/bin/bash
export PATH=/opt/osxcross/target/bin:$PATH
export CC=arm64-apple-darwin23-clang
export CXX=arm64-apple-darwin23-clang++
export OSXCROSS_SDK=MacOSX14.0.sdk
export MACOSX_DEPLOYMENT_TARGET=11.0
export ARCHFLAGS="-arch arm64"

echo "Building macOS ARM64 binary..."

# Use Nuitka for cross-compilation
python3 -m nuitka --standalone --onefile     --output-filename=market-scanner-macos-arm64     --macos-target-arch=arm64     --clang=/opt/osxcross/target/bin/arm64-apple-darwin23-clang     simple_scanner.py

echo "Build complete!"
