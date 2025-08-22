#!/usr/bin/env node

const fs = require("fs");
const { spawn } = require("child_process");
const https = require("https");
const os = require("os");

// Your specific contacts - UPDATE THESE WITH REAL PHONE NUMBERS
const CONTACTS = {
    "David Eiber": "+1234567890",        // Replace with David's real number
    "ACP Group": "+1234567891",          // Replace with ACP group ID
    "Precious Perl": "+1234567892",      // Replace with Precious's real number  
    "JB": "+1234567893",                 // Replace with JB's real number
    "Doron": "+1234567894",              // Replace with Doron's real number
    "Asher": "+1234567895",              // Replace with Asher's real number
    "Josh Noahide": "+1234567896",       // Replace with Josh's real number
    "Dassy": "+1234567897",              // Replace with Dassy's real number
    "Dad": "+1234567898"                 // Replace with Dad's real number
};

const GITHUB_REPO = "bayfitt/market-scanner";

class WhatsAppNotifier {
    constructor() {
        this.lastNotifiedFile = "/tmp/market_scanner_last_release.txt";
    }

    async getSystemSpecs() {
        try {
            const cpuCount = os.cpus().length;
            const totalRAM = Math.round(os.totalmem() / 1024 / 1024 / 1024);
            const platform = os.platform();
            const arch = os.arch();
            const release = os.release();
            
            // Check for GPU
            let gpu = "Integrated Graphics";
            if (fs.existsSync("/dev/dri/card0")) {
                gpu = "Intel/AMD Integrated + GPU Passthrough";
            }
            
            return {
                cpu: `${cpuCount} cores`,
                ram: `${totalRAM}GB`,
                os: `${platform} ${arch}`,
                build: release,
                gpu: gpu
            };
        } catch (error) {
            return {
                cpu: "4 cores",
                ram: "8GB", 
                os: "Linux x64",
                build: "Debian 12 (Build Container)",
                gpu: "GPU Passthrough Enabled"
            };
        }
    }

    async getLatestRelease() {
        return new Promise((resolve, reject) => {
            const options = {
                hostname: "api.github.com",
                path: `/repos/${GITHUB_REPO}/releases/latest`,
                method: "GET",
                headers: {
                    "User-Agent": "Market-Scanner-Build-Bot/1.0"
                }
            };

            const req = https.request(options, (res) => {
                let data = "";
                res.on("data", (chunk) => data += chunk);
                res.on("end", () => {
                    try {
                        resolve(JSON.parse(data));
                    } catch (error) {
                        reject(error);
                    }
                });
            });

            req.on("error", reject);
            req.end();
        });
    }

    async formatReleaseMessage(release) {
        const version = release.tag_name || "Unknown";
        const releaseUrl = release.html_url || "";
        const specs = await this.getSystemSpecs();
        const buildTime = new Date().toISOString();
        
        // Find download links
        let macosLink = "";
        let androidLink = "";
        
        for (const asset of release.assets || []) {
            if (asset.name.includes("macos") || asset.name.includes("dmg")) {
                macosLink = asset.browser_download_url;
            } else if (asset.name.includes("android") || asset.name.includes("apk")) {
                androidLink = asset.browser_download_url;
            }
        }

        const message = `🚀 *Market Scanner ${version} - Ready to Download!*

🎯 *Autonomous Bitcoin Outperformer Scanner*

📱 *Download Links:*
🍎 macOS: ${macosLink || "https://github.com/bayfitt/market-scanner/releases/latest"}
🤖 Android: ${androidLink || "https://github.com/bayfitt/market-scanner/releases/latest"}

⚡ *Key Features:*
✅ Real-time market scanning
✅ VWAP momentum analysis
✅ Options gamma walls detection
✅ Squeeze metrics (float, SI, volume)
✅ BTC benchmark comparison
✅ One-button trading interface
✅ Dark theme (8-bit ANSI colors)

🔗 *Full Release:* ${releaseUrl}

🤖 *AUTOMATED NOTIFICATION*
📧 *Sent by:* Market Scanner Build Bot
📊 *Reason:* New app version available for testing
⏰ *Build Time:* ${buildTime}

💻 *Built on:*
🖥️ CPU: ${specs.cpu}
🧠 RAM: ${specs.ram}
🎮 GPU: ${specs.gpu}
🖥️ OS: ${specs.os}
🏗️ Build: ${specs.build}

Ready to find the next Bitcoin outperformer! 🌙🚀

_This is an automated message sent from the build container_`;

        return message;
    }

    async sendMessage(phoneNumber, message) {
        return new Promise((resolve, reject) => {
            console.log(`📤 Sending to ${phoneNumber}...`);
            
            // Use Mudslide to send WhatsApp message
            const mudslide = spawn("npx", ["mudslide", "send", phoneNumber, message], {
                cwd: "/home/dev/projects/market-scanner",
                stdio: ["pipe", "pipe", "pipe"]
            });

            let output = "";
            let error = "";

            mudslide.stdout.on("data", (data) => {
                output += data.toString();
            });

            mudslide.stderr.on("data", (data) => {
                error += data.toString();
            });

            mudslide.on("close", (code) => {
                if (code === 0) {
                    console.log(`✅ Message sent successfully to ${phoneNumber}`);
                    resolve(output);
                } else {
                    console.error(`❌ Failed to send to ${phoneNumber}: ${error}`);
                    reject(new Error(`Mudslide exited with code ${code}: ${error}`));
                }
            });
        });
    }

    async sendToAllContacts(message) {
        console.log(`📱 Sending notifications to ${Object.keys(CONTACTS).length} contacts...`);
        
        const results = [];
        
        for (const [name, phoneNumber] of Object.entries(CONTACTS)) {
            if (!phoneNumber || phoneNumber.startsWith("+123")) {
                console.log(`⚠️ Skipping ${name} - Please update phone number in script`);
                continue;
            }

            try {
                await this.sendMessage(phoneNumber, message);
                results.push({ name, phoneNumber, status: "success" });
                
                // Wait 3 seconds between messages to avoid rate limiting
                await new Promise(resolve => setTimeout(resolve, 3000));
                
            } catch (error) {
                console.error(`❌ Failed to send to ${name}: ${error.message}`);
                results.push({ name, phoneNumber, status: "failed", error: error.message });
            }
        }
        
        // Summary
        const successful = results.filter(r => r.status === "success").length;
        const failed = results.filter(r => r.status === "failed").length;
        
        console.log(`\n📊 Notification Summary:`);
        console.log(`✅ Successful: ${successful}`);
        console.log(`❌ Failed: ${failed}`);
        console.log(`📱 Total contacts: ${Object.keys(CONTACTS).length}`);
        
        return results;
    }

    async checkForNewRelease() {
        console.log(`🔍 Checking for new releases at ${new Date().toISOString()}`);
        
        try {
            // Check last notified version
            let lastNotifiedVersion = "";
            if (fs.existsSync(this.lastNotifiedFile)) {
                lastNotifiedVersion = fs.readFileSync(this.lastNotifiedFile, "utf8").trim();
            }
            
            // Get latest release
            const release = await this.getLatestRelease();
            if (!release || !release.tag_name) {
                console.log("❌ Could not fetch release info");
                return false;
            }
            
            const currentVersion = release.tag_name;
            
            if (currentVersion && currentVersion !== lastNotifiedVersion) {
                console.log(`🎉 New release found: ${currentVersion}`);
                
                // Format and send message
                const message = await this.formatReleaseMessage(release);
                await this.sendToAllContacts(message);
                
                // Save this version as notified
                fs.writeFileSync(this.lastNotifiedFile, currentVersion);
                console.log(`📝 Marked ${currentVersion} as notified`);
                
                return true;
            } else {
                console.log(`ℹ️ No new release (current: ${currentVersion})`);
                return false;
            }
            
        } catch (error) {
            console.error("❌ Error checking releases:", error.message);
            return false;
        }
    }

    async sendManualNotification() {
        console.log("📱 Sending manual notification for latest release...");
        
        try {
            const release = await this.getLatestRelease();
            if (!release) {
                console.log("❌ Could not fetch release info");
                return;
            }
            
            const message = await this.formatReleaseMessage(release);
            console.log("\n📝 Message to send:");
            console.log("=".repeat(50));
            console.log(message);
            console.log("=".repeat(50));
            
            await this.sendToAllContacts(message);
            
        } catch (error) {
            console.error("❌ Error sending manual notification:", error.message);
        }
    }

    async startMonitoring() {
        console.log("🚀 Starting Market Scanner Release Monitor...");
        console.log(`📊 Monitoring: ${GITHUB_REPO}`);
        console.log(`👥 Will notify ${Object.keys(CONTACTS).length} contacts`);
        console.log("⏰ Checking every 10 minutes");
        
        // Check immediately
        await this.checkForNewRelease();
        
        // Set up interval checking
        setInterval(async () => {
            await this.checkForNewRelease();
        }, 10 * 60 * 1000); // 10 minutes
        
        console.log("✅ Monitor is running. Press Ctrl+C to stop.");
    }
}

// Command line interface
async function main() {
    const notifier = new WhatsAppNotifier();
    
    const args = process.argv.slice(2);
    
    if (args.includes("--manual")) {
        await notifier.sendManualNotification();
        process.exit(0);
    } else if (args.includes("--monitor")) {
        await notifier.startMonitoring();
    } else if (args.includes("--test")) {
        console.log("🧪 Testing system specs...");
        const specs = await notifier.getSystemSpecs();
        console.log("💻 System Specifications:");
        console.log(`   CPU: ${specs.cpu}`);
        console.log(`   RAM: ${specs.ram}`);
        console.log(`   GPU: ${specs.gpu}`);
        console.log(`   OS: ${specs.os}`);
        console.log(`   Build: ${specs.build}`);
        process.exit(0);
    } else {
        console.log("🤖 Market Scanner WhatsApp Notifier");
        console.log("=".repeat(40));
        console.log("");
        console.log("📋 Usage:");
        console.log("  node whatsapp_notify.js --manual     # Send notification for latest release");
        console.log("  node whatsapp_notify.js --monitor    # Start monitoring for new releases");
        console.log("  node whatsapp_notify.js --test       # Test system specs");
        console.log("");
        console.log("📝 Setup Instructions:");
        console.log("1. First, authenticate Mudslide: npx mudslide auth");
        console.log("2. Edit CONTACTS object with real phone numbers");
        console.log("3. Test with: node whatsapp_notify.js --test");
        console.log("4. Send manual test: node whatsapp_notify.js --manual");
        console.log("5. Start monitoring: node whatsapp_notify.js --monitor");
        console.log("");
        console.log("⚠️ IMPORTANT: Update phone numbers in CONTACTS before using!");
        console.log("   Current numbers are placeholders (+123456789X)");
    }
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = WhatsAppNotifier;