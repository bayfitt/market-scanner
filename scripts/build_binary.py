#!/usr/bin/env python3
"""
Build script for creating macOS binary distribution
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run shell command and handle errors"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    
    print(result.stdout)
    return result

def build_binary():
    """Build macOS binary using PyInstaller"""
    
    # Get project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🏗️  Building Market Scanner macOS Binary")
    print(f"📁 Project root: {project_root}")
    
    # Install build dependencies
    print("\n📦 Installing build dependencies...")
    run_command("pip install -r requirements-build.txt")
    
    # Clean previous builds
    print("\n🧹 Cleaning previous builds...")
    build_dirs = ["build", "dist", "__pycache__"]
    for dir_name in build_dirs:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Removed {dir_name}")
    
    # Build binary using PyInstaller spec file
    print("\n🔨 Building binary with PyInstaller...")
    run_command("pyinstaller market_scanner.spec --clean")
    
    # Verify binary was created
    binary_path = project_root / "dist" / "market-scanner"
    if binary_path.exists():
        print(f"✅ Binary created: {binary_path}")
        
        # Make executable
        run_command(f"chmod +x {binary_path}")
        
        # Test binary
        print("\n🧪 Testing binary...")
        result = run_command(f"{binary_path} version")
        
        print("✅ Binary build successful!")
        print(f"📦 Location: {binary_path}")
        print(f"📊 Size: {binary_path.stat().st_size / 1024 / 1024:.1f} MB")
        
        return binary_path
    else:
        print("❌ Binary build failed - no output file found")
        sys.exit(1)

def create_distribution():
    """Create distribution package"""
    
    project_root = Path(__file__).parent.parent
    dist_dir = project_root / "dist"
    
    print("\n📦 Creating distribution package...")
    
    # Create dist directory structure
    package_dir = dist_dir / "market-scanner-macos"
    package_dir.mkdir(exist_ok=True)
    
    # Copy binary
    binary_src = dist_dir / "market-scanner"
    binary_dst = package_dir / "market-scanner"
    shutil.copy2(binary_src, binary_dst)
    
    # Copy documentation
    docs_to_copy = ["README.md", "claude_integration.md", "requirements.txt"]
    for doc in docs_to_copy:
        if (project_root / doc).exists():
            shutil.copy2(project_root / doc, package_dir / doc)
    
    # Create install script
    install_script = package_dir / "install.sh"
    with open(install_script, 'w') as f:
        f.write('''#!/bin/bash
# Market Scanner Installation Script for macOS

echo "🚀 Installing Market Scanner..."

# Make binary executable
chmod +x market-scanner

# Create symlink in /usr/local/bin (if writable)
if [ -w /usr/local/bin ]; then
    ln -sf "$(pwd)/market-scanner" /usr/local/bin/market-scanner
    echo "✅ Created symlink: /usr/local/bin/market-scanner"
else
    echo "⚠️  Cannot create symlink to /usr/local/bin (permission denied)"
    echo "💡 Add $(pwd) to your PATH or run: sudo ln -sf $(pwd)/market-scanner /usr/local/bin/market-scanner"
fi

echo ""
echo "🎯 Installation complete!"
echo "📖 Usage: ./market-scanner scan"
echo "🌐 API: ./market-scanner api"
echo "📚 Docs: ./market-scanner --help"
echo ""
echo "🤖 For Claude integration, see: claude_integration.md"
''')
    
    os.chmod(install_script, 0o755)
    
    # Create ZIP archive
    archive_name = "market-scanner-macos"
    print(f"\n📦 Creating archive: {archive_name}.zip")
    
    shutil.make_archive(
        dist_dir / archive_name,
        'zip',
        dist_dir,
        'market-scanner-macos'
    )
    
    archive_path = dist_dir / f"{archive_name}.zip"
    print(f"✅ Distribution created: {archive_path}")
    print(f"📊 Archive size: {archive_path.stat().st_size / 1024 / 1024:.1f} MB")
    
    return archive_path

if __name__ == "__main__":
    print("🚀 Market Scanner Build System")
    print("=" * 50)
    
    try:
        # Build binary
        binary_path = build_binary()
        
        # Create distribution
        archive_path = create_distribution()
        
        print("\n" + "=" * 50)
        print("🎉 BUILD COMPLETE!")
        print(f"📦 Binary: {binary_path}")
        print(f"📦 Distribution: {archive_path}")
        print("\n🚀 Ready for GitHub release!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Build cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Build failed: {e}")
        sys.exit(1)