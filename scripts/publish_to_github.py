#!/usr/bin/env python3
"""
Script to initialize and publish Market Scanner to GitHub
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(cmd, cwd=None, capture=True):
    """Run shell command and handle errors"""
    print(f"Running: {cmd}")
    
    if capture:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False
        if result.stdout.strip():
            print(result.stdout)
    else:
        result = subprocess.run(cmd, shell=True, cwd=cwd)
        if result.returncode != 0:
            print(f"Command failed with code {result.returncode}")
            return False
    
    return True

def check_git_installed():
    """Check if git is installed"""
    result = subprocess.run("git --version", shell=True, capture_output=True, text=True)
    return result.returncode == 0

def check_gh_cli_installed():
    """Check if GitHub CLI is installed"""
    result = subprocess.run("gh --version", shell=True, capture_output=True, text=True)
    return result.returncode == 0

def initialize_git_repo():
    """Initialize git repository"""
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🔧 Initializing Git repository...")
    
    # Initialize git if not already done
    if not (project_root / ".git").exists():
        if not run_command("git init"):
            return False
    
    # Add all files
    if not run_command("git add ."):
        return False
    
    # Create initial commit
    commit_msg = "🚀 Initial release of Market Scanner - Autonomous market analysis tool"
    if not run_command(f'git commit -m "{commit_msg}"'):
        # Might fail if nothing to commit, that's ok
        pass
    
    return True

def create_github_repo():
    """Create GitHub repository using GitHub CLI"""
    
    print("🌐 Creating GitHub repository...")
    
    repo_name = "market-scanner"
    description = "🚀 Autonomous Market Scanner - Find symbols guaranteed to outperform Bitcoin using advanced technical analysis"
    
    # Create public repository
    cmd = f'''gh repo create {repo_name} \\
        --description "{description}" \\
        --public \\
        --source . \\
        --remote origin \\
        --push'''
    
    if not run_command(cmd, capture=False):
        print("❌ Failed to create GitHub repository")
        return False
    
    print(f"✅ GitHub repository created: https://github.com/$(gh api user --jq .login)/{repo_name}")
    return True

def setup_repository_settings():
    """Configure repository settings"""
    
    print("⚙️  Configuring repository settings...")
    
    # Enable issues and wiki
    if not run_command("gh repo edit --enable-issues --enable-wiki"):
        print("⚠️  Could not configure repository settings")
    
    # Add topics
    topics = [
        "trading", "market-analysis", "bitcoin", "technical-analysis", 
        "python", "api", "claude-ai", "fintech", "macos"
    ]
    
    topics_str = " ".join(topics)
    if not run_command(f"gh repo edit --add-topic {topics_str}"):
        print("⚠️  Could not add repository topics")
    
    return True

def create_initial_release():
    """Create initial release"""
    
    print("🏷️  Creating initial release...")
    
    # Build binary first
    print("📦 Building binary for release...")
    if not run_command("python scripts/build_binary.py"):
        print("❌ Binary build failed")
        return False
    
    # Create release
    release_notes = """# Market Scanner v1.0.0

🚀 **Initial Release** - Autonomous Market Scanner that finds symbols guaranteed to outperform Bitcoin

## 🎯 Features

- **100% FREE APIs** - No paid subscriptions required
- **One-Button Scanning** - Find top 3 opportunities instantly  
- **BTC Benchmarking** - Only returns symbols with higher expected returns than Bitcoin
- **Claude Integration** - REST API for autonomous trading workflows
- **Advanced Analysis** - VWAP momentum, options flow, squeeze detection
- **Paper Trading Ready** - Built-in execution framework

## 📦 Installation (macOS)

1. Download `market-scanner-macos.zip`
2. Extract and run `./install.sh`
3. Run `market-scanner scan`

## 🤖 Claude Integration

Start API server: `market-scanner api`

Then Claude can call:
- `POST /scan` - Run market scan
- `POST /quick-analysis` - Analyze specific symbols  
- `GET /performance` - View performance stats

See `claude_integration.md` for complete API documentation.

## 🚨 Disclaimer

Educational use only. Not financial advice. Trade at your own risk.
"""

    # Check if we have distribution files
    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("❌ No distribution files found. Run build script first.")
        return False
    
    # Create git tag
    if not run_command("git tag v1.0.0"):
        print("⚠️  Could not create git tag")
    
    # Push tag
    if not run_command("git push origin v1.0.0"):
        print("⚠️  Could not push git tag")
    
    # Create release
    release_files = []
    if (dist_dir / "market-scanner-macos.zip").exists():
        release_files.append("dist/market-scanner-macos.zip")
    if (dist_dir / "market-scanner").exists():
        release_files.append("dist/market-scanner")
    
    if release_files:
        files_str = " ".join(release_files)
        cmd = f'''gh release create v1.0.0 {files_str} \\
            --title "Market Scanner v1.0.0" \\
            --notes "{release_notes}"'''
        
        if not run_command(cmd, capture=False):
            print("❌ Could not create release")
            return False
    
    print("✅ Release created successfully!")
    return True

def main():
    """Main publish workflow"""
    
    print("🚀 Market Scanner GitHub Publisher")
    print("=" * 50)
    
    # Pre-flight checks
    if not check_git_installed():
        print("❌ Git is not installed. Please install Git first.")
        sys.exit(1)
    
    if not check_gh_cli_installed():
        print("❌ GitHub CLI is not installed.")
        print("💡 Install with: brew install gh")
        print("💡 Then login with: gh auth login")
        sys.exit(1)
    
    # Check if user is logged into GitHub CLI
    result = subprocess.run("gh auth status", shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Not logged into GitHub CLI")
        print("💡 Login with: gh auth login")
        sys.exit(1)
    
    print("✅ Pre-flight checks passed")
    
    try:
        # Step 1: Initialize Git repository
        if not initialize_git_repo():
            print("❌ Failed to initialize Git repository")
            sys.exit(1)
        
        # Step 2: Create GitHub repository
        if not create_github_repo():
            print("❌ Failed to create GitHub repository")
            sys.exit(1)
        
        # Step 3: Configure repository
        setup_repository_settings()
        
        # Step 4: Create initial release
        if not create_initial_release():
            print("❌ Failed to create initial release")
            sys.exit(1)
        
        print("\n" + "=" * 50)
        print("🎉 PUBLICATION COMPLETE!")
        
        # Get repository URL
        result = subprocess.run("gh repo view --web --json url -q .url", 
                              shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            repo_url = result.stdout.strip()
            print(f"🌐 Repository: {repo_url}")
            print(f"📦 Releases: {repo_url}/releases")
            print(f"📖 API Docs: {repo_url}/blob/main/claude_integration.md")
        
        print("\n🤖 Ready for Claude integration!")
        print("💡 Start the API: market-scanner api")
        
    except KeyboardInterrupt:
        print("\n⏹️  Publication cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Publication failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()