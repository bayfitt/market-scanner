#!/usr/bin/env python3
import os
import subprocess
import shutil

# This will create a Python script bundle that can run on macOS
def create_macos_bundle():
    print("Creating macOS ARM64 Python bundle...")
    
    # Create a standalone Python script with dependencies
    with open("market-scanner-macos", "w") as f:
        f.write("#!/usr/bin/env python3\n")
        f.write("# Market Scanner for macOS ARM64\n\n")
        
        # Include all dependencies inline
        modules = ["simple_scanner.py", "signal_engines.py", "data_feeds.py", 
                  "composite_scoring.py", "orchestrator.py"]
        
        for module in modules:
            if os.path.exists(module):
                with open(module) as m:
                    content = m.read()
                    # Remove the shebang and imports we will handle
                    lines = content.split("\n")
                    filtered = []
                    for line in lines:
                        if not line.startswith("#!/") and not line.startswith("from ."):
                            filtered.append(line)
                    f.write("\n".join(filtered) + "\n\n")
        
        # Add main execution
        f.write("\nif __name__ == \"__main__\":\n")
        f.write("    scanner = SimpleScanner()\n")
        f.write("    scanner.run()\n")
    
    # Make executable
    os.chmod("market-scanner-macos", 0o755)
    
    # Create ARM64 binary wrapper using osxcross
    print("Creating native ARM64 wrapper...")
    os.environ["PATH"] = "/opt/osxcross/target/bin:" + os.environ.get("PATH", "")
    os.environ["CC"] = "arm64-apple-darwin23-clang"
    
    wrapper_code = """
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
    return system("/usr/bin/python3 market-scanner-macos");
}
"""
    
    with open("wrapper.c", "w") as f:
        f.write(wrapper_code)
    
    # Compile wrapper
    subprocess.run([
        "arm64-apple-darwin23-clang",
        "-o", "market-scanner-macos-arm64",
        "-arch", "arm64",
        "-mmacosx-version-min=11.0",
        "wrapper.c"
    ])
    
    print("✅ macOS ARM64 binary created: market-scanner-macos-arm64")

if __name__ == "__main__":
    create_macos_bundle()
