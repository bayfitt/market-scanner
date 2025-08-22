#!/usr/bin/env python3
"""
WhatsApp notification script for Market Scanner releases
Requires: pip install pywhatkit schedule
"""

import pywhatkit as pwk
import time
import requests
import json
from datetime import datetime, timedelta
import schedule
import os

# Configuration
GITHUB_REPO = "bayfitt/market-scanner"
FRIENDS_CONTACTS = [
    "+1234567890",  # Replace with actual phone numbers
    "+0987654321",  # Add more friends as needed
]

# GitHub API to check for latest release
def get_latest_release():
    """Get latest GitHub release info"""
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error fetching release: {e}")
        return None

def format_release_message(release_data):
    """Format WhatsApp message for release"""
    version = release_data.get('tag_name', 'Unknown')
    release_url = release_data.get('html_url', '')
    
    # Find download links
    macos_link = ""
    android_link = ""
    
    for asset in release_data.get('assets', []):
        if 'macos.dmg' in asset['name']:
            macos_link = asset['browser_download_url']
        elif 'android.apk' in asset['name']:
            android_link = asset['browser_download_url']
    
    message = f"""🚀 *Market Scanner {version} is Ready!*

🎯 *Autonomous Bitcoin Outperformer Scanner*

📱 *Downloads:*
• macOS: {macos_link}
• Android: {android_link}

⚡ *Features:*
✅ Real-time market scanning
✅ VWAP momentum analysis
✅ Options gamma detection
✅ Squeeze metrics
✅ BTC benchmark comparison
✅ One-button interface
✅ Dark theme (8-bit ANSI)

🔗 *Full Release:* {release_url}

Ready to find the next moonshot! 🌙
Built with Claude Code 🤖"""
    
    return message

def send_to_friends(message):
    """Send WhatsApp message to all friends"""
    print(f"📱 Sending notifications to {len(FRIENDS_CONTACTS)} friends...")
    
    for i, contact in enumerate(FRIENDS_CONTACTS):
        try:
            # Calculate send time (now + 2 minutes per contact to avoid spam)
            send_time = datetime.now() + timedelta(minutes=i * 2)
            hour = send_time.hour
            minute = send_time.minute
            
            print(f"⏰ Scheduling message to {contact} at {hour}:{minute:02d}")
            
            # Send WhatsApp message
            pwk.sendwhatmsg(
                phone_no=contact,
                message=message,
                time_hour=hour,
                time_min=minute,
                wait_time=15,  # Wait 15 seconds before sending
                tab_close=True
            )
            
            print(f"✅ Message scheduled for {contact}")
            
        except Exception as e:
            print(f"❌ Failed to send to {contact}: {e}")
    
    print("🎉 All notifications scheduled!")

def check_for_new_release():
    """Check for new releases and notify"""
    print(f"🔍 Checking for new releases at {datetime.now()}")
    
    # Check if we've already notified about this release
    last_notified_file = "/tmp/market_scanner_last_release.txt"
    last_notified_version = ""
    
    if os.path.exists(last_notified_file):
        with open(last_notified_file, 'r') as f:
            last_notified_version = f.read().strip()
    
    # Get latest release
    release = get_latest_release()
    if not release:
        print("❌ Could not fetch release info")
        return
    
    current_version = release.get('tag_name', '')
    
    if current_version and current_version != last_notified_version:
        print(f"🎉 New release found: {current_version}")
        
        # Format and send message
        message = format_release_message(release)
        send_to_friends(message)
        
        # Save this version as notified
        with open(last_notified_file, 'w') as f:
            f.write(current_version)
        
        print(f"📝 Marked {current_version} as notified")
    else:
        print(f"ℹ️ No new release (current: {current_version})")

def start_monitoring():
    """Start monitoring for releases"""
    print("🚀 Starting Market Scanner release monitor...")
    print(f"📊 Monitoring: {GITHUB_REPO}")
    print(f"👥 Will notify {len(FRIENDS_CONTACTS)} friends")
    print("⏰ Checking every 10 minutes")
    
    # Schedule checks every 10 minutes
    schedule.every(10).minutes.do(check_for_new_release)
    
    # Check immediately
    check_for_new_release()
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute for scheduled tasks

def manual_notify():
    """Manually trigger notification for latest release"""
    print("📱 Manual notification triggered")
    release = get_latest_release()
    
    if release:
        message = format_release_message(release)
        print("\n📝 Message to send:")
        print(message)
        print("\n" + "="*50)
        
        confirm = input("Send this message to friends? (y/N): ")
        if confirm.lower() == 'y':
            send_to_friends(message)
        else:
            print("❌ Cancelled")
    else:
        print("❌ Could not fetch release info")

if __name__ == "__main__":
    import sys
    
    print("🤖 Market Scanner WhatsApp Notifier")
    print("="*40)
    
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        manual_notify()
    else:
        # Show setup instructions
        print("\n📋 Setup Instructions:")
        print("1. Install: pip install pywhatkit schedule requests")
        print("2. Edit FRIENDS_CONTACTS with real phone numbers")
        print("3. Run: python whatsapp_notify.py")
        print("4. For manual test: python whatsapp_notify.py manual")
        print("\n⚠️  First run will open WhatsApp Web for authentication")
        
        if input("\nStart monitoring? (y/N): ").lower() == 'y':
            start_monitoring()
        else:
            print("👋 Exiting")