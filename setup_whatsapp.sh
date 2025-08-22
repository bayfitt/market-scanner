#!/bin/bash

echo "🚀 Setting up Market Scanner WhatsApp Notifications"
echo "=================================================="
echo ""

# Make the notification script executable
chmod +x whatsapp_notify.js

echo "📋 WhatsApp CLI Setup Instructions:"
echo ""
echo "1. 📱 FIRST: Have your phone with WhatsApp ready"
echo "2. 🔐 Authenticate Mudslide with WhatsApp Web:"
echo "   npx mudslide@latest login"
echo ""
echo "3. 📱 When QR code appears:"
echo "   - Open WhatsApp on your phone"
echo "   - Go to Settings > Linked Devices" 
echo "   - Tap \"Link a Device\""
echo "   - Scan the QR code displayed in terminal"
echo ""
echo "4. ✅ Test authentication:"
echo "   npx mudslide@latest send me \"Test from build container\""
echo ""
echo "5. 📝 Edit contacts in whatsapp_notify.js:"
echo "   nano whatsapp_notify.js"
echo "   # Update phone numbers in CONTACTS object"
echo ""
echo "6. 🧪 Test the notification system:"
echo "   node whatsapp_notify.js --test"
echo "   node whatsapp_notify.js --manual"
echo ""
echo "7. 🤖 Start automatic monitoring:"
echo "   node whatsapp_notify.js --monitor"
echo ""
echo "📍 Container Info:"
echo "   - Name: build-container-privileged"
echo "   - CPU: 4 cores"
echo "   - RAM: 8GB"
echo "   - GPU: Passthrough enabled"
echo "   - Cache: ~/.local/share/mudslide"
echo ""
echo "⚠️  IMPORTANT:"
echo "   - Keep your phone nearby during first setup"
echo "   - Update phone numbers before testing"
echo "   - Authentication persists until you logout"
echo ""

# Show current configuration
echo "📊 Current Contact List:"
grep -A 10 "const CONTACTS" whatsapp_notify.js | head -12

echo ""
echo "🚀 Ready to authenticate? Run: npx mudslide@latest login"
