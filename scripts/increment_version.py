#!/usr/bin/env python3
"""
Automatic version incrementing script
Increments version by 0.001 for each build/push
"""

import sys
from pathlib import Path

def get_current_version():
    """Read current version from version.txt"""
    version_file = Path(__file__).parent.parent / 'version.txt'
    if version_file.exists():
        return version_file.read_text().strip()
    return "0.2.000"

def increment_version(current_version):
    """Increment version by 0.001"""
    try:
        # Simple increment approach: parse parts and increment patch
        parts = current_version.split(".")
        if len(parts) == 3:
            major = int(parts[0])
            minor = int(parts[1])  
            patch = int(parts[2]) + 1
            return f"{major}.{minor}.{patch:03d}"
        return "0.2.001"
    except:
        return "0.2.001"

def update_version_file(new_version):
    """Update version.txt with new version"""
    version_file = Path(__file__).parent.parent / 'version.txt'
    version_file.write_text(new_version)
    return version_file

def update_build_script(new_version):
    """Update build_exe.py with new version"""
    build_script = Path(__file__).parent.parent / 'build' / 'build_exe.py'
    if build_script.exists():
        content = build_script.read_text()
        
        # Update version in multiple places
        import re
        
        # Update filevers and prodvers tuples
        version_parts = new_version.split(".")
        version_tuple = f"{int(version_parts[0])}, {int(version_parts[1])}, {int(version_parts[2])}, 0"
        
        content = re.sub(
            r'filevers=\([0-9, ]+\)',
            f'filevers=({version_tuple})',
            content
        )
        content = re.sub(
            r'prodvers=\([0-9, ]+\)',
            f'prodvers=({version_tuple})',
            content
        )
        
        # Update FileVersion string
        content = re.sub(
            r"StringStruct\(u'FileVersion', u'[0-9\.]+'\)",
            f"StringStruct(u'FileVersion', u'{new_version}.0')",
            content
        )
        
        # Update ProductVersion string
        content = re.sub(
            r"StringStruct\(u'ProductVersion', u'[0-9\.]+'\)",
            f"StringStruct(u'ProductVersion', u'{new_version}.0')",
            content
        )
        
        build_script.write_text(content)
        print(f"Updated build_exe.py with version {new_version}")

def update_spec_files(new_version):
    """Update spec files with new version"""
    spec_files = [
        Path(__file__).parent.parent / 'FileOrganizer.spec',
        Path(__file__).parent.parent / 'FileOrganizer_SystemTray.spec',
        Path(__file__).parent.parent / 'build' / 'FileOrganizer.spec',
        Path(__file__).parent.parent / 'build' / 'FileOrganizer_SystemTray.spec'
    ]
    
    for spec_file in spec_files:
        if spec_file.exists():
            content = spec_file.read_text()
            # Update version in spec files if present
            import re
            content = re.sub(
                r"version='[0-9\.]+'",
                f"version='{new_version}'",
                content
            )
            spec_file.write_text(content)
            print(f"Updated {spec_file.name} with version {new_version}")

def main():
    """Main function to increment version"""
    # Get current version
    current_version = get_current_version()
    print(f"Current version: {current_version}")
    
    # Increment version
    new_version = increment_version(current_version)
    print(f"New version: {new_version}")
    
    # Update version file
    version_file = update_version_file(new_version)
    print(f"Updated {version_file}")
    
    # Update build scripts
    update_build_script(new_version)
    
    # Update spec files
    update_spec_files(new_version)
    
    # Output new version for GitHub Actions
    print(f"::set-output name=version::{new_version}")
    
    # Also write to environment file for GitHub Actions
    github_env = Path(os.environ.get('GITHUB_ENV', '/dev/null'))
    if github_env.exists():
        with open(github_env, 'a') as f:
            f.write(f"NEW_VERSION={new_version}\n")
    
    return new_version

if __name__ == "__main__":
    import os
    new_version = main()
    sys.exit(0)