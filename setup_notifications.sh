#!/bin/bash

echo "🚀 Setting up Market Scanner WhatsApp Notifications"
echo "=================================================="

# Install required packages
echo "📦 Installing Python packages..."
pip3 install pywhatkit schedule requests

# Make notification script executable
chmod +x whatsapp_notify.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Edit whatsapp_notify.py and update FRIENDS_CONTACTS with real phone numbers"
echo "2. Test manually: python3 whatsapp_notify.py manual"
echo "3. Start monitoring: python3 whatsapp_notify.py"
echo ""
echo "⚠️  Important: First run will open WhatsApp Web for authentication"
echo "   Make sure you're logged into WhatsApp Web in your browser"
echo ""
echo "🎯 The script will:"
echo "   • Check GitHub for new releases every 10 minutes"
echo "   • Send download links to your friends automatically"
echo "   • Include both macOS and Android download links"
echo "   • Only notify once per release"
echo ""