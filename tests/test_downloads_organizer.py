#!/usr/bin/env python3
"""
Test script for Downloads Organizer
Creates sample files and demonstrates the organization functionality
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src directory to Python path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent
src_dir = project_root / 'src'
sys.path.insert(0, str(src_dir))

from transfers.downloads_organizer import DownloadsOrganizer, SystemFolderManager

def create_sample_downloads(downloads_path: Path) -> None:
    """Create sample files in the downloads folder for testing"""
    
    sample_files = [
        # Documents
        'presentation.pptx',
        'report.pdf', 
        'spreadsheet.xlsx',
        'notes.txt',
        'contract.docx',
        'data.csv',
        'readme.md',
        
        # Images
        'vacation_photo.jpg',
        'screenshot.png',
        'diagram.svg',
        'avatar.gif',
        'photo.heic',
        'raw_image.cr2',
        
        # Videos
        'movie.mp4',
        'clip.avi',
        'recording.mov',
        'stream.mkv',
        'tutorial.webm',
        
        # Music
        'song.mp3',
        'album.flac',
        'podcast.m4a',
        'audio.wav',
        'track.ogg',
        
        # Archives
        'backup.zip',
        'software.rar',
        'files.7z',
        'archive.tar.gz',
        
        # Code files
        'script.py',
        'website.html',
        'styles.css',
        'app.js',
        'config.json',
        
        # Executables
        'installer.exe',
        'app.msi',
        'program.dmg',
        
        # eBooks
        'novel.epub',
        'manual.pdf',
        'guide.mobi',
        
        # Fonts
        'font.ttf',
        'typeface.otf',
        
        # Unknown/misc
        'unknown.xyz',
        'data.dat',
        'temp.tmp',  # Should be excluded
        'file.crdownload'  # Should be excluded
    ]
    
    print(f"Creating {len(sample_files)} sample files in {downloads_path}")
    
    for filename in sample_files:
        file_path = downloads_path / filename
        
        # Create empty file with some content
        content = f"Sample content for {filename}\nCreated for testing downloads organizer.\n"
        file_path.write_text(content)
    
    print(f"✅ Created {len(sample_files)} sample files")

def test_downloads_organizer():
    """Test the downloads organizer with sample data"""
    
    # Create temporary directory structure
    temp_dir = Path(tempfile.mkdtemp(prefix='downloads_test_'))
    
    try:
        print("🧪 Downloads Organizer Test")
        print("=" * 50)
        print(f"Test directory: {temp_dir}")
        
        # Create fake system folders
        downloads = temp_dir / 'Downloads'
        documents = temp_dir / 'Documents' 
        pictures = temp_dir / 'Pictures'
        videos = temp_dir / 'Videos'
        music = temp_dir / 'Music'
        
        for folder in [downloads, documents, pictures, videos, music]:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Create sample files
        create_sample_downloads(downloads)
        
        print(f"\n📁 Initial Downloads folder contents:")
        files = list(downloads.glob('*'))
        for file in sorted(files):
            if file.is_file():
                print(f"   • {file.name}")
        
        # Test the organizer (dry run first)
        print(f"\n🔍 Running dry run to preview organization...")
        
        # Monkey patch the system folder detection for testing
        class TestSystemFolderManager(SystemFolderManager):
            def detect_system_folders(self):
                return {
                    'Desktop': temp_dir / 'Desktop',
                    'Documents': documents,
                    'Downloads': downloads,
                    'Pictures': pictures,
                    'Videos': videos,
                    'Music': music
                }
        
        # Create organizer with test folder manager
        organizer = DownloadsOrganizer()
        organizer.folder_manager = TestSystemFolderManager()
        # Override the downloads path to use our test directory
        organizer.downloads_path = downloads
        
        # Run dry run
        dry_results = organizer.organize_downloads(dry_run=True)
        print(organizer.create_report(dry_results))
        
        # Ask user if they want to proceed with actual organization
        print(f"\n❓ Proceed with actual file organization? (y/N): ", end='')
        try:
            response = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            response = 'n'
        
        if response in ['y', 'yes']:
            print(f"\n🗂️ Organizing files...")
            
            # Run actual organization
            real_results = organizer.organize_downloads(dry_run=False)
            print(organizer.create_report(real_results))
            
            # Show final folder structure
            print(f"\n📋 Final folder structure:")
            for folder in [documents, pictures, videos, music]:
                if folder.exists():
                    files = list(folder.glob('**/*'))
                    files = [f for f in files if f.is_file()]
                    if files:
                        print(f"\n{folder.name}/ ({len(files)} files)")
                        for file in sorted(files)[:5]:  # Show first 5
                            rel_path = file.relative_to(folder)
                            print(f"   • {rel_path}")
                        if len(files) > 5:
                            print(f"   ... and {len(files) - 5} more")
            
            # Check remaining downloads
            remaining = list(downloads.glob('*'))
            remaining = [f for f in remaining if f.is_file()]
            if remaining:
                print(f"\nRemaining in Downloads/ ({len(remaining)} files):")
                for file in sorted(remaining):
                    print(f"   • {file.name}")
            else:
                print(f"\n✨ Downloads folder is now empty!")
        
        else:
            print("Organization cancelled.")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        try:
            shutil.rmtree(temp_dir)
            print(f"\n🧹 Cleaned up test directory: {temp_dir}")
        except Exception as e:
            print(f"⚠️ Could not clean up test directory: {e}")

def test_file_categorization():
    """Test file categorization logic"""
    
    print("🏷️ File Categorization Test")
    print("=" * 40)
    
    from transfers.downloads_organizer import DownloadsOrganizer
    
    organizer = DownloadsOrganizer()
    
    test_files = [
        'document.pdf',
        'image.jpg', 
        'video.mp4',
        'song.mp3',
        'archive.zip',
        'app.exe',
        'font.ttf',
        'script.py',
        'ebook.epub',
        'unknown.xyz'
    ]
    
    print("File categorization results:")
    for filename in test_files:
        file_path = Path(filename)
        category, icon = organizer.categorize_file(file_path)
        destination = organizer.folder_manager.get_destination_folder(category)
        print(f"   {icon} {filename:<15} → {category:<12} → {destination.name}")

def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Downloads Organizer')
    parser.add_argument('--categorization-only', action='store_true',
                       help='Only test file categorization')
    
    args = parser.parse_args()
    
    if args.categorization_only:
        test_file_categorization()
    else:
        test_file_categorization()
        print("\n")
        test_downloads_organizer()

if __name__ == "__main__":
    main()