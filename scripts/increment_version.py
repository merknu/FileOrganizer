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
        # Parse version (e.g., "0.2.001" -> 0.2001)
        version_float = float(current_version.replace(".", "", 1))
        
        # Increment by 0.001
        new_version_float = version_float + 0.001
        
        # Format back to string (e.g., 0.2002 -> "0.2.002")
        version_str = f"{new_version_float:.3f}"
        
        # Ensure proper format with two dots
        parts = version_str.split(".")
        if len(parts) == 2:
            major = parts[0]
            minor_patch = parts[1].zfill(4)  # Ensure 4 digits after first dot
            return f"{major}.{minor_patch[0]}.{minor_patch[1:]}"
        
        return version_str
    except:
        # Fallback: simple increment
        parts = current_version.split(".")
        if len(parts) == 3:
            major = parts[0]
            minor = parts[1]
            patch = int(parts[2]) + 1
            return f"{major}.{minor}.{patch:03d}"
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
        content = re.sub(
            r'filevers=\([0-9, ]+\)',
            f'filevers=({new_version.replace(".", ", ")}, 0)',
            content
        )
        content = re.sub(
            r'prodvers=\([0-9, ]+\)',
            f'prodvers=({new_version.replace(".", ", ")}, 0)',
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