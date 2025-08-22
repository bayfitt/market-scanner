#!/usr/bin/env python3
"""
Market Scanner Telegram Notification System
"""

import asyncio
import json
import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path

# Your specific contacts - UPDATE THESE WITH REAL USERNAMES/PHONE NUMBERS
CONTACTS = {
    "David Eiber": "@davideiber",           # Replace with David's Telegram username
    "ACP Group": "-1001234567890",          # Replace with ACP group chat ID  
    "Precious Perl": "@preciousperl",       # Replace with Precious's username
    "JB": "@jb_username",                   # Replace with JB's username
    "Doron": "@doron_username",             # Replace with Doron's username
    "Asher": "@asher_username",             # Replace with Asher's username
    "Josh Noahide": "@josh_noahide",        # Replace with Josh's username
    "Dassy": "@dassy_username",             # Replace with Dassy's username
    "Dad": "+14045433417"                   # Phone numbers work too
}

GITHUB_REPO = "bayfitt/market-scanner"

class TelegramNotifier:
    def __init__(self):
        self.last_notified_file = "/tmp/market_scanner_last_release.txt"
        self.tg_cli = "/root/.tg-cli/tg.py"
        
    def get_system_specs(self):
        """Get system specifications"""
        try:
            # Get CPU cores
            cpu_count = os.cpu_count() or 4
            
            # Get RAM info
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                mem_total = 8  # Default
                for line in meminfo.split('\n'):
                    if 'MemTotal:' in line:
                        mem_total = int(line.split()[1]) // 1024 // 1024  # Convert to GB
                        break
            
            # Check for GPU
            gpu = "GPU Passthrough Enabled"
            if os.path.exists("/dev/dri/card0"):
                gpu = "Intel/AMD + GPU Passthrough"
            
            return {
                "cpu": f"{cpu_count} cores",
                "ram": f"{mem_total}GB",
                "os": "Linux x64",
                "build": "Debian 12 (Build Container)",
                "gpu": gpu
            }
        except Exception:
            return {
                "cpu": "4 cores",
                "ram": "8GB",
                "os": "Linux x64", 
                "build": "Debian 12 (Build Container)",
                "gpu": "GPU Passthrough Enabled"
            }
    
    def get_latest_release(self):
        """Get latest release from GitHub API"""
        try:
            import urllib.request
            import json
            
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Market-Scanner-Build-Bot/1.0')
            
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            print(f"Error fetching release: {e}")
            return None
    
    def format_release_message(self, release):
        """Format the release notification message"""
        version = release.get('tag_name', 'Unknown')
        release_url = release.get('html_url', '')
        specs = self.get_system_specs()
        build_time = datetime.now().isoformat()
        
        # Find download links
        macos_link = ""
        android_link = ""
        
        for asset in release.get('assets', []):
            name = asset.get('name', '').lower()
            if 'macos' in name or 'dmg' in name:
                macos_link = asset.get('browser_download_url', '')
            elif 'android' in name or 'apk' in name:
                android_link = asset.get('browser_download_url', '')
        
        if not macos_link:
            macos_link = f"https://github.com/{GITHUB_REPO}/releases/latest"
        if not android_link:
            android_link = f"https://github.com/{GITHUB_REPO}/releases/latest"
        
        message = f"""🚀 **Market Scanner {version} - Ready to Download!**

🎯 **Autonomous Bitcoin Outperformer Scanner**

📱 **Download Links:**
🍎 macOS: {macos_link}
🤖 Android: {android_link}

⚡ **Key Features:**
✅ Real-time market scanning
✅ VWAP momentum analysis  
✅ Options gamma walls detection
✅ Squeeze metrics (float, SI, volume)
✅ BTC benchmark comparison
✅ One-button trading interface
✅ Dark theme (8-bit ANSI colors)

🔗 **Full Release:** {release_url}

🤖 **AUTOMATED NOTIFICATION**
📧 **Sent by:** Market Scanner Build Bot
📊 **Reason:** New app version available for testing
⏰ **Build Time:** {build_time}

💻 **Built on:**
🖥️ CPU: {specs['cpu']}
🧠 RAM: {specs['ram']}
🎮 GPU: {specs['gpu']}
🖥️ OS: {specs['os']}
🏗️ Build: {specs['build']}

Ready to find the next Bitcoin outperformer! 🌙🚀

_This is an automated message sent from the build container_"""
        
        return message
    
    async def send_message(self, contact, message):
        """Send message using Telegram CLI"""
        print(f"📤 Sending to {contact}...")
        
        try:
            # Activate venv and run telegram CLI
            cmd = f"cd ~/.tg-cli && . .venv/bin/activate && python3 tg.py send --to '{contact}' --text '{message}'"
            
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                print(f"✅ Message sent successfully to {contact}")
                return True
            else:
                print(f"❌ Failed to send to {contact}: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending to {contact}: {e}")
            return False
    
    async def send_to_all_contacts(self, message):
        """Send message to all contacts"""
        print(f"📱 Sending notifications to {len(CONTACTS)} contacts...")
        
        results = []
        
        for name, contact in CONTACTS.items():
            if not contact or contact.startswith("@username") or contact.startswith("-100123"):
                print(f"⚠️ Skipping {name} - Please update contact info in script")
                continue
            
            success = await self.send_message(contact, message)
            results.append({"name": name, "contact": contact, "status": "success" if success else "failed"})
            
            # Wait 3 seconds between messages to avoid rate limiting
            await asyncio.sleep(3)
        
        # Summary
        successful = len([r for r in results if r["status"] == "success"])
        failed = len([r for r in results if r["status"] == "failed"])
        
        print(f"\n📊 Notification Summary:")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📱 Total contacts: {len(CONTACTS)}")
        
        return results
    
    def check_for_new_release(self):
        """Check for new release and send notifications"""
        print(f"🔍 Checking for new releases at {datetime.now().isoformat()}")
        
        try:
            # Check last notified version
            last_notified_version = ""
            if os.path.exists(self.last_notified_file):
                with open(self.last_notified_file, 'r') as f:
                    last_notified_version = f.read().strip()
            
            # Get latest release
            release = self.get_latest_release()
            if not release or not release.get('tag_name'):
                print("❌ Could not fetch release info")
                return False
            
            current_version = release['tag_name']
            
            if current_version and current_version != last_notified_version:
                print(f"🎉 New release found: {current_version}")
                
                # Format and send message
                message = self.format_release_message(release)
                asyncio.run(self.send_to_all_contacts(message))
                
                # Save this version as notified
                with open(self.last_notified_file, 'w') as f:
                    f.write(current_version)
                print(f"📝 Marked {current_version} as notified")
                
                return True
            else:
                print(f"ℹ️ No new release (current: {current_version})")
                return False
                
        except Exception as e:
            print(f"❌ Error checking releases: {e}")
            return False
    
    def send_manual_notification(self):
        """Send manual notification for latest release"""
        print("📱 Sending manual notification for latest release...")
        
        try:
            release = self.get_latest_release()
            if not release:
                print("❌ Could not fetch release info")
                return
            
            message = self.format_release_message(release)
            print("\n📝 Message to send:")
            print("=" * 50)
            print(message)
            print("=" * 50)
            
            asyncio.run(self.send_to_all_contacts(message))
            
        except Exception as e:
            print(f"❌ Error sending manual notification: {e}")
    
    def start_monitoring(self):
        """Start monitoring for new releases"""
        print("🚀 Starting Market Scanner Release Monitor...")
        print(f"📊 Monitoring: {GITHUB_REPO}")
        print(f"👥 Will notify {len(CONTACTS)} contacts")
        print("⏰ Checking every 10 minutes")
        
        try:
            while True:
                self.check_for_new_release()
                print("💤 Sleeping for 10 minutes...")
                time.sleep(600)  # 10 minutes
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")

def main():
    notifier = TelegramNotifier()
    
    if len(sys.argv) < 2:
        print("🤖 Market Scanner Telegram Notifier")
        print("=" * 40)
        print("")
        print("📋 Usage:")
        print("  python3 telegram_notify.py manual     # Send notification for latest release")
        print("  python3 telegram_notify.py monitor    # Start monitoring for new releases") 
        print("  python3 telegram_notify.py test       # Test system specs")
        print("")
        print("📝 Setup Instructions:")
        print("1. Get API credentials from my.telegram.org")
        print("2. Update ~/.tg-cli/.env with your API_ID and API_HASH")
        print("3. Authenticate: cd ~/.tg-cli && . .venv/bin/activate && python3 tg.py login --phone +14045433417")
        print("4. Edit CONTACTS in this script with real usernames/chat IDs")
        print("5. Test with: python3 telegram_notify.py test")
        print("6. Send manual test: python3 telegram_notify.py manual")
        print("7. Start monitoring: python3 telegram_notify.py monitor")
        print("")
        print("⚠️ IMPORTANT: Update CONTACTS with real Telegram usernames!")
        return
    
    command = sys.argv[1].lower()
    
    if command == "manual":
        notifier.send_manual_notification()
    elif command == "monitor":
        notifier.start_monitoring()
    elif command == "test":
        print("🧪 Testing system specs...")
        specs = notifier.get_system_specs()
        print("💻 System Specifications:")
        for key, value in specs.items():
            print(f"   {key.upper()}: {value}")
    else:
        print(f"❌ Unknown command: {command}")
        print("💡 Run without arguments to see available commands")

if __name__ == "__main__":
    main()
