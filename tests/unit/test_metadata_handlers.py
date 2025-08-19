"""
Unit tests for file_handler.metadata_handlers module.

Tests cover:
- Image metadata extraction (dimensions, formats)
- Audio metadata extraction (duration, formats)
- Document metadata extraction (word counts, formats)
- Video metadata extraction (duration, formats)
- Error handling for missing dependencies
- Edge cases and invalid files
"""

import os
import tempfile
from unittest.mock import Mock, patch, MagicMock

import pytest

from file_handler.metadata_handlers import (
    get_image_size,
    get_audio_duration,
    get_document_word_count,
    get_video_duration,
    get_file_metadata,
    _get_pdf_word_count,
    _get_docx_word_count,
    _get_txt_word_count
)


class TestImageMetadataHandling:
    """Test image metadata extraction functionality."""
    
    @pytest.mark.unit
    @pytest.mark.requires_dependencies
    def test_get_image_size_pillow_not_available(self):
        """Test image size extraction when Pillow is not available."""
        with patch('file_handler.metadata_handlers.Image', None):
            with pytest.raises(ImportError, match="Pillow is required"):
                get_image_size("test.jpg")
    
    @pytest.mark.unit
    @patch('file_handler.metadata_handlers.Image')
    def test_get_image_size_success(self, mock_image_module):
        """Test successful image size extraction."""
        # Mock PIL.Image
        mock_image = Mock()
        mock_image.size = (1920, 1080)
        mock_image.__enter__ = Mock(return_value=mock_image)
        mock_image.__exit__ = Mock(return_value=None)
        
        mock_image_module.open.return_value = mock_image
        
        result = get_image_size("test.jpg")
        assert result == (1920, 1080)
        mock_image_module.open.assert_called_once_with("test.jpg")
    
    @pytest.mark.unit
    @patch('file_handler.metadata_handlers.Image')
    def test_get_image_size_file_error(self, mock_image_module):
        """Test image size extraction with file error."""
        mock_image_module.open.side_effect = Exception("File not found")
        
        with pytest.raises(Exception, match="File not found"):
            get_image_size("nonexistent.jpg")
    
    @pytest.mark.unit
    @patch('file_handler.metadata_handlers.Image')
    def test_get_image_size_invalid_image(self, mock_image_module):
        """Test image size extraction with invalid image file."""
        mock_image_module.open.side_effect = Exception("Cannot identify image file")
        
        with pytest.raises(Exception):
            get_image_size("invalid.jpg")
    
    @pytest.mark.unit
    @patch('file_handler.metadata_handlers.Image')
    def test_get_image_size_different_formats(self, mock_image_module):
        """Test image size extraction for different formats."""
        test_sizes = [
            ("small.jpg", (640, 480)),
            ("large.png", (3840, 2160)),
            ("square.gif", (500, 500))
        ]
        
        for filename, expected_size in test_sizes:
            mock_image = Mock()
            mock_image.size = expected_size
            mock_image.__enter__ = Mock(return_value=mock_image)
            mock_image.__exit__ = Mock(return_value=None)
            
            mock_image_module.open.return_value = mock_image
            
            result = get_image_size(filename)
            assert result == expected_size


class TestAudioMetadataHandling:
    """Test audio metadata extraction functionality."""
    
    @pytest.mark.unit
    @pytest.mark.requires_dependencies
    def test_get_audio_duration_mutagen_not_available(self):
        """Test audio duration extraction when Mutagen is not available."""
        with patch('file_handler.metadata_handlers.MutagenFile', None):
            with pytest.raises(ImportError, match="Mutagen is required"):
                get_audio_duration("test.mp3")
    
    @pytest.mark.unit
    @patch('file_handler.metadata_handlers.MutagenFile')
    def test_get_audio_duration_success(self, mock_mutagen_file):
        """Test successful audio duration extraction."""
        mock_audio = Mock()
        mock_audio.info.length = 180.5
        mock_mutagen_file.return_value = mock_audio
        
        result = get_audio_duration("test.mp3")
        assert result == 180.5
        mock_mutagen_file.assert_called_once_with("test.mp3")
    
    @pytest.mark.unit
    @patch('file_handler.metadata_handlers.MutagenFile')
    def test_get_audio_duration_no_info(self, mock_mutagen_file):
        """Test audio duration extraction when file has no info."""
        mock_audio = Mock()
        mock_audio.info = None
        mock_mutagen_file.return_value = mock_audio
        
        result = get_audio_duration("test.mp3")
        assert result is None
    
    @pytest.mark.unit
    @patch('file_handler.metadata_handlers.MutagenFile')
    def test_get_audio_duration_file_none(self, mock_mutagen_file):
        """Test audio duration extraction when file is None."""
        mock_mutagen_file.return_value = None
        
        result = get_audio_duration("test.mp3")
        assert result is None
    
    @pytest.mark.unit
    @patch('file_handler.metadata_handlers.MutagenFile')
    def test_get_audio_duration_error(self, mock_mutagen_file):
        """Test audio duration extraction with error."""
        mock_mutagen_file.side_effect = Exception("Cannot load audio file")
        
        result = get_audio_duration("invalid.mp3")
        assert result is None
    
    @pytest.mark.unit
    @patch('file_handler.metadata_handlers.MutagenFile')
    def test_get_audio_duration_different_formats(self, mock_mutagen_file):
        """Test audio duration extraction for different formats."""
        test_durations = [
            ("short.mp3", 30.0),
            ("medium.wav", 180.5),
            ("long.flac", 3600.0)
        ]
        
        for filename, expected_duration in test_durations:
            mock_audio = Mock()
            mock_audio.info.length = expected_duration
            mock_mutagen_file.return_value = mock_audio
            
            result = get_audio_duration(filename)
            assert result == expected_duration


class TestDocumentMetadataHandling:
    """Test document metadata extraction functionality."""
    
    @pytest.mark.unit
    def test_get_document_word_count_txt(self, temp_dir):
        """Test word count extraction from text file."""
        txt_file = os.path.join(temp_dir, "test.txt")
        content = "This is a test document with exactly ten words total."
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        result = get_document_word_count(txt_file)
        assert result == 10  # "This is a test document with exactly ten words total."
    
    @pytest.mark.unit
    def test_get_document_word_count_empty_txt(self, temp_dir):
        """Test word count extraction from empty text file."""
        txt_file = os.path.join(temp_dir, "empty.txt")
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("")
        
        result = get_document_word_count(txt_file)
        assert result == 0
    
    @pytest.mark.unit
    @patch('file_handler.metadata_handlers.PdfReader')
    def test_get_document_word_count_pdf_available(self, mock_pdf_reader, temp_dir):
        """Test PDF word count when pypdf is available."""
        pdf_file = os.path.join(temp_dir, "test.pdf")
        
        # Mock PDF reader
        mock_page = Mock()
        mock_page.extract_text.return_value = "This is PDF content with five words"
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader
        
        # Create a fake PDF file
        with open(pdf_file, 'wb') as f:
            f.write(b'fake pdf content')
        
        result = get_document_word_count(pdf_file)
        assert result == 7  # "This is PDF content with five words"
    
    @pytest.mark.unit
    def test_get_document_word_count_pdf_not_available(self, temp_dir):
        """Test PDF word count when pypdf is not available."""
        pdf_file = os.path.join(temp_dir, "test.pdf")
        with open(pdf_file, 'wb') as f:
            f.write(b'fake pdf content')
        
        with patch('file_handler.metadata_handlers.PdfReader', None):
            result = get_document_word_count(pdf_file)
            assert result == 0
    
    @pytest.mark.unit
    @patch('file_handler.metadata_handlers.Document')
    def test_get_document_word_count_docx_available(self, mock_document_class, temp_dir):
        """Test DOCX word count when python-docx is available."""
        docx_file = os.path.join(temp_dir, "test.docx")
        
        # Mock DOCX document
        mock_paragraph = Mock()
        mock_paragraph.text = "This is DOCX content"
        
        mock_doc = Mock()
        mock_doc.paragraphs = [mock_paragraph]
        mock_document_class.return_value = mock_doc
        
        # Create fake DOCX file
        with open(docx_file, 'wb') as f:
            f.write(b'fake docx content')
        
        result = get_document_word_count(docx_file)
        assert result == 4  # "This is DOCX content"
    
    @pytest.mark.unit
    def test_get_document_word_count_docx_not_available(self, temp_dir):
        """Test DOCX word count when python-docx is not available."""
        docx_file = os.path.join(temp_dir, "test.docx")
        with open(docx_file, 'wb') as f:
            f.write(b'fake docx content')
        
        with patch('file_handler.metadata_handlers.Document', None):
            result = get_document_word_count(docx_file)
            assert result == 0
    
    @pytest.mark.unit
    def test_get_document_word_count_unsupported_format(self, temp_dir):
        """Test word count for unsupported document format."""
        unsupported_file = os.path.join(temp_dir, "test.xyz")
        with open(unsupported_file, 'w') as f:
            f.write("content")
        
        result = get_document_word_count(unsupported_file)
        assert result == 0
    
    @pytest.mark.unit
    def test_get_document_word_count_error(self, temp_dir):
        """Test word count extraction with file error."""
        result = get_document_word_count("/nonexistent/file.txt")
        assert result == 0


class TestDocumentHelperFunctions:
    """Test document helper functions."""
    
    @pytest.mark.unit
    @patch('file_handler.metadata_handlers.PdfReader')
    def test_get_pdf_word_count_success(self, mock_pdf_reader, temp_dir):
        """Test successful PDF word count extraction."""
        pdf_file = os.path.join(temp_dir, "test.pdf")
        
        # Mock pages with different content
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "First page with content"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Second page with more content"
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader
        
        with open(pdf_file, 'wb') as f:
            f.write(b'fake pdf')
        
        result = _get_pdf_word_count(pdf_file)
        assert result == 8  # 4 + 5 words from both pages
    
    @pytest.mark.unit
    @patch('file_handler.metadata_handlers.PdfReader')
    def test_get_pdf_word_count_empty_pages(self, mock_pdf_reader, temp_dir):
        """Test PDF word count with empty pages."""
        pdf_file = os.path.join(temp_dir, "test.pdf")
        
        mock_page = Mock()
        mock_page.extract_text.return_value = None  # Empty page
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader
        
        with open(pdf_file, 'wb') as f:
            f.write(b'fake pdf')
        
        result = _get_pdf_word_count(pdf_file)
        assert result == 0
    
    @pytest.mark.unit
    @patch('file_handler.metadata_handlers.Document')
    def test_get_docx_word_count_success(self, mock_document_class, temp_dir):
        """Test successful DOCX word count extraction."""
        docx_file = os.path.join(temp_dir, "test.docx")
        
        # Mock paragraphs
        mock_para1 = Mock()
        mock_para1.text = "First paragraph content"
        mock_para2 = Mock()
        mock_para2.text = "Second paragraph with more words"
        
        mock_doc = Mock()
        mock_doc.paragraphs = [mock_para1, mock_para2]
        mock_document_class.return_value = mock_doc
        
        with open(docx_file, 'wb') as f:
            f.write(b'fake docx')
        
        result = _get_docx_word_count(docx_file)
        assert result == 8  # 3 + 5 words from both paragraphs
    
    @pytest.mark.unit
    def test_get_txt_word_count_success(self, temp_dir):
        """Test successful text file word count extraction."""
        txt_file = os.path.join(temp_dir, "test.txt")
        content = "This is a test file with multiple lines.\nSecond line here.\nThird line with more words."
        
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        result = _get_txt_word_count(txt_file)
        assert result == 17  # Total words across all lines
    
    @pytest.mark.unit
    def test_get_txt_word_count_encoding_error(self, temp_dir):
        """Test text file word count with encoding issues."""
        txt_file = os.path.join(temp_dir, "test.txt")
        
        # Write binary data that might cause encoding issues
        with open(txt_file, 'wb') as f:
            f.write(b'\xff\xfe\x00\x00invalid utf-8 content')
        
        # Should handle encoding errors gracefully
        result = _get_txt_word_count(txt_file)
        assert result >= 0  # Should not crash, may return 0 or partial count


class TestVideoMetadataHandling:
    """Test video metadata extraction functionality."""
    
    @pytest.mark.unit
    @pytest.mark.requires_dependencies
    def test_get_video_duration_moviepy_not_available(self):
        """Test video duration extraction when moviepy is not available."""
        with patch('file_handler.metadata_handlers.VideoFileClip', None):
            with pytest.raises(ImportError, match="moviepy is required"):
                get_video_duration("test.mp4")
    
    @pytest.mark.unit
    @patch('file_handler.metadata_handlers.VideoFileClip')
    def test_get_video_duration_success(self, mock_video_clip):
        """Test successful video duration extraction."""
        mock_video = Mock()
        mock_video.duration = 3600.5
        mock_video.__enter__ = Mock(return_value=mock_video)
        mock_video.__exit__ = Mock(return_value=None)
        
        mock_video_clip.return_value = mock_video
        
        result = get_video_duration("test.mp4")
        assert result == 3600.5
        mock_video_clip.assert_called_once_with("test.mp4")
    
    @pytest.mark.unit
    @patch('file_handler.metadata_handlers.VideoFileClip')
    def test_get_video_duration_error(self, mock_video_clip):
        """Test video duration extraction with error."""
        mock_video_clip.side_effect = Exception("Cannot load video file")
        
        result = get_video_duration("invalid.mp4")
        assert result is None
    
    @pytest.mark.unit
    @patch('file_handler.metadata_handlers.VideoFileClip')
    def test_get_video_duration_different_formats(self, mock_video_clip):
        """Test video duration extraction for different formats."""
        test_durations = [
            ("short.mp4", 30.0),
            ("medium.avi", 1800.5),
            ("long.mov", 7200.0)
        ]
        
        for filename, expected_duration in test_durations:
            mock_video = Mock()
            mock_video.duration = expected_duration
            mock_video.__enter__ = Mock(return_value=mock_video)
            mock_video.__exit__ = Mock(return_value=None)
            
            mock_video_clip.return_value = mock_video
            
            result = get_video_duration(filename)
            assert result == expected_duration


class TestComprehensiveMetadataHandling:
    """Test comprehensive metadata extraction functionality."""
    
    @pytest.mark.unit
    @patch('os.path.getsize')
    def test_get_file_metadata_image(self, mock_getsize):
        """Test comprehensive metadata for image files."""
        mock_getsize.return_value = 1024000  # 1MB
        
        with patch('file_handler.metadata_handlers.get_image_size', return_value=(1920, 1080)):
            result = get_file_metadata("test.jpg")
            
            assert result['size'] == 1024000
            assert result['type'] == 'image'
            assert result['additional']['width'] == 1920
            assert result['additional']['height'] == 1080
            assert result['additional']['resolution'] == "1920x1080"
    
    @pytest.mark.unit
    @patch('os.path.getsize')
    def test_get_file_metadata_audio(self, mock_getsize):
        """Test comprehensive metadata for audio files."""
        mock_getsize.return_value = 5000000  # 5MB
        
        with patch('file_handler.metadata_handlers.get_audio_duration', return_value=180.5):
            result = get_file_metadata("test.mp3")
            
            assert result['size'] == 5000000
            assert result['type'] == 'audio'
            assert result['additional']['duration'] == 180.5
            assert result['additional']['duration_formatted'] == "3:00"
    
    @pytest.mark.unit
    @patch('os.path.getsize')
    def test_get_file_metadata_document(self, mock_getsize):
        """Test comprehensive metadata for document files."""
        mock_getsize.return_value = 100000  # 100KB
        
        with patch('file_handler.metadata_handlers.get_document_word_count', return_value=500):
            result = get_file_metadata("test.pdf")
            
            assert result['size'] == 100000
            assert result['type'] == 'document'
            assert result['additional']['word_count'] == 500
    
    @pytest.mark.unit
    @patch('os.path.getsize')
    def test_get_file_metadata_video(self, mock_getsize):
        """Test comprehensive metadata for video files."""
        mock_getsize.return_value = 50000000  # 50MB
        
        with patch('file_handler.metadata_handlers.get_video_duration', return_value=3600.0):
            result = get_file_metadata("test.mp4")
            
            assert result['size'] == 50000000
            assert result['type'] == 'video'
            assert result['additional']['duration'] == 3600.0
            assert result['additional']['duration_formatted'] == "60:00"
    
    @pytest.mark.unit
    @patch('os.path.getsize')
    def test_get_file_metadata_unknown_type(self, mock_getsize):
        """Test comprehensive metadata for unknown file types."""
        mock_getsize.return_value = 1000
        
        result = get_file_metadata("test.xyz")
        
        assert result['size'] == 1000
        assert result['type'] == 'unknown'
        assert result['additional'] == {}
    
    @pytest.mark.unit
    def test_get_file_metadata_error_handling(self):
        """Test metadata extraction with various errors."""
        # Test with non-existent file
        result = get_file_metadata("/nonexistent/file.txt")
        
        assert result['size'] == 0
        assert result['type'] == 'unknown'
        assert result['additional'] == {}
    
    @pytest.mark.unit
    @patch('os.path.getsize')
    def test_get_file_metadata_extraction_errors(self, mock_getsize):
        """Test metadata extraction when specific extractors fail."""
        mock_getsize.return_value = 1000
        
        # Test image with extraction error
        with patch('file_handler.metadata_handlers.get_image_size', side_effect=Exception("Error")):
            result = get_file_metadata("test.jpg")
            
            assert result['type'] == 'image'
            assert result['additional'] == {}  # Should be empty due to error
    
    @pytest.mark.unit
    @patch('os.path.getsize')
    def test_get_file_metadata_duration_formatting(self, mock_getsize):
        """Test duration formatting in metadata."""
        mock_getsize.return_value = 1000
        
        test_cases = [
            (65.0, "1:05"),    # 1 minute 5 seconds
            (3661.0, "61:01"),  # 61 minutes 1 second
            (30.5, "0:30"),     # 30.5 seconds -> 0:30
        ]
        
        for duration, expected_format in test_cases:
            with patch('file_handler.metadata_handlers.get_audio_duration', return_value=duration):
                result = get_file_metadata("test.mp3")
                assert result['additional']['duration_formatted'] == expected_format


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling in metadata extraction."""
    
    @pytest.mark.unit
    def test_metadata_handlers_with_none_file(self):
        """Test metadata handlers with None file path."""
        with pytest.raises((TypeError, AttributeError)):
            get_document_word_count(None)
    
    @pytest.mark.unit
    def test_metadata_handlers_with_empty_string(self):
        """Test metadata handlers with empty string file path."""
        result = get_document_word_count("")
        assert result == 0
    
    @pytest.mark.unit
    def test_get_file_metadata_all_extensions(self):
        """Test get_file_metadata with various file extensions."""
        extensions_and_types = [
            (".jpg", "image"),
            (".jpeg", "image"),
            (".png", "image"),
            (".gif", "image"),
            (".bmp", "image"),
            (".mp3", "audio"),
            (".wav", "audio"),
            (".flac", "audio"),
            (".m4a", "audio"),
            (".ogg", "audio"),
            (".pdf", "document"),
            (".doc", "document"),
            (".docx", "document"),
            (".txt", "document"),
            (".mp4", "video"),
            (".avi", "video"),
            (".mov", "video"),
            (".mkv", "video"),
            (".wmv", "video"),
            (".unknown", "unknown")
        ]
        
        with patch('os.path.getsize', return_value=1000):
            for ext, expected_type in extensions_and_types:
                filename = f"test{ext}"
                result = get_file_metadata(filename)
                assert result['type'] == expected_type
    
    @pytest.mark.unit
    @patch('os.path.getsize')
    def test_get_file_metadata_case_insensitive_extensions(self, mock_getsize):
        """Test that file extension matching is case insensitive."""
        mock_getsize.return_value = 1000
        
        # Test uppercase extensions
        result = get_file_metadata("TEST.JPG")
        assert result['type'] == 'image'
        
        result = get_file_metadata("TEST.MP3")
        assert result['type'] == 'audio'
        
        result = get_file_metadata("TEST.PDF")
        assert result['type'] == 'document'
        
        result = get_file_metadata("TEST.MP4")
        assert result['type'] == 'video'