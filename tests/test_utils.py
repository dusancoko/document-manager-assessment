# src/tests/test_utils.py
"""
Test cases for utility functions
"""

import os
import tempfile
from unittest.mock import Mock, patch, mock_open
from datetime import datetime

from django.test import TestCase

from propylon_document_manager.file_versions.models import FileVersion, User
from .base import BaseTestCase


class FileManagementUtilsTest(TestCase):
    """Test cases for file management utilities"""
    
    def test_unique_file_upload_path_basic(self):
        """Test basic unique file upload path generation"""
        from propylon_document_manager.utils.file_management import unique_file_upload_path
        
        # Mock file instance
        instance = Mock()
        filename = "test_document.pdf"
        
        # Generate path
        path = unique_file_upload_path(instance, filename)
        
        # Check path structure
        self.assertTrue(path.endswith('.pdf'))
        self.assertIn('test-document', path)  # Slugified base name
        
        # Check date prefix (YYYYMMDD format)
        date_prefix = path[:8]
        self.assertEqual(len(date_prefix), 8)
        self.assertTrue(date_prefix.isdigit())
        
        # Verify it's today's date
        today = datetime.now().strftime("%Y%m%d")
        self.assertEqual(date_prefix, today)
    
    def test_unique_file_upload_path_uniqueness(self):
        """Test that multiple calls generate different paths"""
        from propylon_document_manager.utils.file_management import unique_file_upload_path
        
        instance = Mock()
        filename = "duplicate.txt"
        
        # Generate multiple paths
        paths = []
        for _ in range(5):
            path = unique_file_upload_path(instance, filename)
            paths.append(path)
        
        # All paths should be unique
        self.assertEqual(len(paths), len(set(paths)))
        
        # All should have same date prefix and extension
        for path in paths:
            self.assertTrue(path.endswith('.txt'))
            self.assertEqual(path[:8], datetime.now().strftime("%Y%m%d"))
    
        """Test handling of special characters in filename"""
        from propylon_document_manager.utils.file_management import unique_file_upload_path
        
        instance = Mock()
        
        test_cases = [
            ("Tëst Fîlé with spéciál chàracters.txt", "test-file-with-special-characters"),
            ("File with spaces and CAPS.pdf", "file-with-spaces-and-caps"),
            ("file_with_underscores.doc", "file-with-underscores"),
            ("file-with-dashes.xlsx", "file-with-dashes"),
            ("123 numeric start.png", "123-numeric-start"),
            ("!@#$%^&*()_+.gif", ""),  # Only special chars
            ("UPPERCASE.JPEG", "uppercase"),
        ]
        
        for filename, expected_slug_part in test_cases:
            with self.subTest(filename=filename):
                path = unique_file_upload_path(instance, filename)
                
                # Extract extension
                expected_ext = os.path.splitext(filename)[1].lower()
                self.assertTrue(path.endswith(expected_ext))
                
                if expected_slug_part:
                    self.assertIn(expected_slug_part, path)
    
    def test_unique_file_upload_path_empty_filename(self):
        """Test handling of empty or very short filenames"""
        from propylon_document_manager.utils.file_management import unique_file_upload_path
        
        instance = Mock()
        
        test_cases = [
            "",
            ".",
            ".txt",
            "a.txt",
        ]
        
        for filename in test_cases:
            with self.subTest(filename=filename):
                path = unique_file_upload_path(instance, filename)
                
                # Should generate a valid path even with problematic filenames
                self.assertIsInstance(path, str)
                self.assertTrue(len(path) > 8)  # At least date + some identifier
    
    def test_unique_file_upload_path_very_long_filename(self):
        """Test handling of very long filenames"""
        from propylon_document_manager.utils.file_management import unique_file_upload_path
        
        instance = Mock()
        
        # Create very long filename
        long_base = "a" * 200
        filename = f"{long_base}.txt"
        
        path = unique_file_upload_path(instance, filename)
        
        # Should handle gracefully and not create excessively long paths
        self.assertTrue(path.endswith('.txt'))
        self.assertLess(len(path), 255)  # Reasonable path length limit


class FileExtractionUtilsTest(BaseTestCase):
    """Test cases for file text extraction utilities"""
    
    def test_extract_text_from_plain_text(self):
        """Test text extraction from plain text files"""
        from propylon_document_manager.utils.file_extraction import extract_text
        
        content = "This is plain text content\nWith multiple lines\nFor testing"
        file_version = FileVersion.objects.create(
            file_name="plain.txt",
            version_number=1,
            file_path=self.create_test_file("plain.txt", content.encode()),
            uploader=self.user1,
            virtual_path="/documents/plain.txt",
            mime_type="text/plain",
            checksum="plain_checksum"
        )
        
        extracted_text = extract_text(file_version)
        self.assertEqual(extracted_text, content)
    
    def test_extract_text_from_json(self):
        """Test text extraction from JSON files"""
        from propylon_document_manager.utils.file_extraction import extract_text
        
        json_content = '{"key": "value", "number": 42, "array": [1, 2, 3]}'
        file_version = FileVersion.objects.create(
            file_name="data.json",
            version_number=1,
            file_path=self.create_test_file("data.json", json_content.encode()),
            uploader=self.user1,
            virtual_path="/documents/data.json",
            mime_type="application/json",
            checksum="json_checksum"
        )
        
        extracted_text = extract_text(file_version)
        self.assertEqual(extracted_text, json_content)
    
    def test_extract_text_from_html(self):
        """Test text extraction from HTML files"""
        from propylon_document_manager.utils.file_extraction import extract_text
        
        html_content = "<html><body><h1>Test HTML</h1><p>Content here</p></body></html>"
        file_version = FileVersion.objects.create(
            file_name="page.html",
            version_number=1,
            file_path=self.create_test_file("page.html", html_content.encode()),
            uploader=self.user1,
            virtual_path="/documents/page.html",
            mime_type="text/html",
            checksum="html_checksum"
        )
        
        extracted_text = extract_text(file_version)
        self.assertEqual(extracted_text, html_content)
    
    def test_extract_text_unsupported_mime_type(self):
        """Test text extraction from unsupported file types"""
        from propylon_document_manager.utils.file_extraction import extract_text
        
        file_version = FileVersion.objects.create(
            file_name="binary.bin",
            version_number=1,
            file_path=self.create_test_file("binary.bin", b"\x00\x01\x02"),
            uploader=self.user1,
            virtual_path="/documents/binary.bin",
            mime_type="application/octet-stream",
            checksum="binary_checksum"
        )
        
        extracted_text = extract_text(file_version)
        self.assertIn("Unsupported MIME type", extracted_text)
        self.assertIn("application/octet-stream", extracted_text)
    
    @patch('propylon_document_manager.utils.file_extraction.pypdf.PdfReader')
    def test_extract_text_from_pdf_success(self, mock_pdf_reader):
        """Test successful text extraction from PDF files"""
        from propylon_document_manager.utils.file_extraction import extract_text
        
        # Mock PDF reader
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2 content"
        
        mock_reader_instance = Mock()
        mock_reader_instance.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader_instance
        
        file_version = FileVersion.objects.create(
            file_name="document.pdf",
            version_number=1,
            file_path=self.create_test_file("document.pdf", b"fake pdf content"),
            uploader=self.user1,
            virtual_path="/documents/document.pdf",
            mime_type="application/pdf",
            checksum="pdf_checksum"
        )
        
        extracted_text = extract_text(file_version)
        self.assertEqual(extracted_text, "Page 1 content\nPage 2 content")
        mock_pdf_reader.assert_called_once()
    
    @patch('propylon_document_manager.utils.file_extraction.pypdf.PdfReader')
    def test_extract_text_from_pdf_empty_pages(self, mock_pdf_reader):
        """Test PDF text extraction with empty pages"""
        from propylon_document_manager.utils.file_extraction import extract_text
        
        # Mock PDF with empty pages
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = None
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = ""
        mock_page3 = Mock()
        mock_page3.extract_text.return_value = "Only page with content"
        
        mock_reader_instance = Mock()
        mock_reader_instance.pages = [mock_page1, mock_page2, mock_page3]
        mock_pdf_reader.return_value = mock_reader_instance
        
        file_version = FileVersion.objects.create(
            file_name="sparse.pdf",
            version_number=1,
            file_path=self.create_test_file("sparse.pdf", b"fake pdf content"),
            uploader=self.user1,
            virtual_path="/documents/sparse.pdf",
            mime_type="application/pdf",
            checksum="sparse_checksum"
        )
        
        extracted_text = extract_text(file_version)
        self.assertEqual(extracted_text, "\n\nOnly page with content")
    
    @patch('propylon_document_manager.utils.file_extraction.mammoth.convert_to_markdown')
    def test_extract_text_from_docx(self, mock_mammoth):
        """Test text extraction from DOCX files"""
        from propylon_document_manager.utils.file_extraction import extract_text
        
        # Mock mammoth response
        mock_result = Mock()
        mock_result.value = "# Document Title\n\nThis is a Word document converted to markdown."
        mock_mammoth.return_value = mock_result
        
        file_version = FileVersion.objects.create(
            file_name="document.docx",
            version_number=1,
            file_path=self.create_test_file("document.docx", b"fake docx content"),
            uploader=self.user1,
            virtual_path="/documents/document.docx",
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            checksum="docx_checksum"
        )
        
        extracted_text = extract_text(file_version)
        self.assertEqual(extracted_text, "# Document Title\n\nThis is a Word document converted to markdown.")
        mock_mammoth.assert_called_once()
    
    @patch('propylon_document_manager.utils.file_extraction.zipfile.ZipFile')
    def test_extract_text_from_odt(self, mock_zipfile):
        """Test text extraction from ODT files"""
        from propylon_document_manager.utils.file_extraction import extract_text
        
        # Mock ODT content
        odt_xml = b'<?xml version="1.0"?><document>ODT content here</document>'
        
        mock_file = Mock()
        mock_file.read.return_value = odt_xml
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=None)
        
        mock_zip = Mock()
        mock_zip.open.return_value = mock_file
        mock_zip.__enter__ = Mock(return_value=mock_zip)
        mock_zip.__exit__ = Mock(return_value=None)
        
        mock_zipfile.return_value = mock_zip
        
        file_version = FileVersion.objects.create(
            file_name="document.odt",
            version_number=1,
            file_path=self.create_test_file("document.odt", b"fake odt content"),
            uploader=self.user1,
            virtual_path="/documents/document.odt",
            mime_type="application/vnd.oasis.opendocument.text",
            checksum="odt_checksum"
        )
        
        extracted_text = extract_text(file_version)
        self.assertEqual(extracted_text, odt_xml.decode('utf-8'))
    
    def test_extract_text_file_encoding_errors(self):
        """Test text extraction with encoding errors"""
        from propylon_document_manager.utils.file_extraction import extract_text
        
        # Create file with invalid UTF-8 bytes
        invalid_content = b'\xff\xfe\x00\x00invalid utf-8'
        file_version = FileVersion.objects.create(
            file_name="encoding_test.txt",
            version_number=1,
            file_path=self.create_test_file("encoding_test.txt", invalid_content),
            uploader=self.user1,
            virtual_path="/documents/encoding_test.txt",
            mime_type="text/plain",
            checksum="encoding_checksum"
        )
        
        # Should handle encoding errors gracefully
        extracted_text = extract_text(file_version)
        self.assertIsInstance(extracted_text, str)
        # Content may be mangled but shouldn't crash
    
    def test_extract_text_mime_type_fallback(self):
        """Test text extraction with missing mime_type (uses filename guess)"""
        from propylon_document_manager.utils.file_extraction import extract_text
        
        content = "Text content without explicit mime type"
        file_version = FileVersion.objects.create(
            file_name="no_mime.txt",
            version_number=1,
            file_path=self.create_test_file("no_mime.txt", content.encode()),
            uploader=self.user1,
            virtual_path="/documents/no_mime.txt",
            mime_type="",  # Empty mime type
            checksum="no_mime_checksum"
        )
        
        extracted_text = extract_text(file_version)
        # Should guess mime type from filename and extract successfully
        self.assertEqual(extracted_text, content)
    
    @patch('builtins.open', mock_open(read_data="mocked file content"))
    def test_extract_text_file_not_found_handling(self):
        """Test handling when file doesn't exist on disk"""
        from propylon_document_manager.utils.file_extraction import extract_text
        
        # Create file version with non-existent file path
        file_version = FileVersion.objects.create(
            file_name="nonexistent.txt",
            version_number=1,
            file_path="nonexistent/path/file.txt",  # Non-existent path
            uploader=self.user1,
            virtual_path="/documents/nonexistent.txt",
            mime_type="text/plain",
            checksum="nonexistent_checksum"
        )
        
        # Should handle file not found gracefully
        extracted_text = extract_text(file_version)
        # The mocked file content should be returned
        self.assertEqual(extracted_text, "mocked file content")


class SupportedMimeTypesTest(TestCase):
    """Test cases for supported MIME types configuration"""
    
    def test_supported_mime_types_constant(self):
        """Test that SUPPORTED_MIME_TYPES is properly defined"""
        from propylon_document_manager.utils.file_extraction import SUPPORTED_MIME_TYPES
        
        self.assertIsInstance(SUPPORTED_MIME_TYPES, set)
        self.assertGreater(len(SUPPORTED_MIME_TYPES), 0)
        
        # Check for expected types
        expected_types = {
            'text/plain',
            'application/json',
            'text/html',
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.oasis.opendocument.text'
        }
        
        for mime_type in expected_types:
            self.assertIn(mime_type, SUPPORTED_MIME_TYPES)
    
    def test_mime_type_coverage(self):
        """Test coverage of common file types"""
        from propylon_document_manager.utils.file_extraction import SUPPORTED_MIME_TYPES
        
        # Text-based types
        text_types = [
            'text/plain',
            'text/markdown', 
            'text/html',
            'text/csv',
            'application/json',
            'application/xml',
            'text/xml'
        ]
        
        for mime_type in text_types:
            self.assertIn(mime_type, SUPPORTED_MIME_TYPES)
        
        # Code file types
        code_types = [
            'application/javascript',
            'text/javascript',
            'text/x-python'
        ]
        
        for mime_type in code_types:
            self.assertIn(mime_type, SUPPORTED_MIME_TYPES)
        
        # Document types
        document_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.oasis.opendocument.text'
        ]
        
        for mime_type in document_types:
            self.assertIn(mime_type, SUPPORTED_MIME_TYPES)


class UtilityFunctionEdgeCasesTest(BaseTestCase):
    """Test cases for edge cases in utility functions"""
    
    def test_file_upload_path_concurrent_calls(self):
        """Test that concurrent calls to file upload path are unique"""
        from propylon_document_manager.utils.file_management import unique_file_upload_path
        import threading
        import time
        
        instance = Mock()
        filename = "concurrent.txt"
        paths = []
        paths_lock = threading.Lock()
        
        def generate_path():
            path = unique_file_upload_path(instance, filename)
            with paths_lock:
                paths.append(path)
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=generate_path)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All paths should be unique
        self.assertEqual(len(paths), len(set(paths)))
    
    def test_extract_text_with_very_large_file(self):
        """Test text extraction behavior with very large file content"""
        from propylon_document_manager.utils.file_extraction import extract_text
        
        # Create large content (1MB of text)
        large_content = "This is a large file content. " * 35000  # ~1MB
        
        file_version = FileVersion.objects.create(
            file_name="large.txt",
            version_number=1,
            file_path=self.create_test_file("large.txt", large_content.encode()),
            uploader=self.user1,
            virtual_path="/documents/large.txt",
            mime_type="text/plain",
            checksum="large_checksum"
        )
        
        # Should handle large files without issues
        extracted_text = extract_text(file_version)
        self.assertEqual(extracted_text, large_content)
        self.assertGreater(len(extracted_text), 1000000)  # At least 1MB
    
    def test_file_path_generation_date_rollover(self):
        """Test file path generation behavior around date rollover"""
        from propylon_document_manager.utils.file_management import unique_file_upload_path
        
        instance = Mock()
        filename = "rollover.txt"
        
        # Generate path and check date consistency
        path = unique_file_upload_path(instance, filename)
        date_part = path[:8]
        
        # Should match current date
        from datetime import datetime
        expected_date = datetime.now().strftime("%Y%m%d")
        self.assertEqual(date_part, expected_date)
        
        # Path should be deterministic for date part
        path2 = unique_file_upload_path(instance, filename)
        date_part2 = path2[:8]
        self.assertEqual(date_part, date_part2)
    
    def test_extract_text_memory_efficiency(self):
        """Test that text extraction doesn't consume excessive memory"""
        from propylon_document_manager.utils.file_extraction import extract_text
        import tracemalloc
        
        # Start memory tracking
        tracemalloc.start()
        
        # Create moderately large file
        content = "Memory test content. " * 1000  # ~20KB
        file_version = FileVersion.objects.create(
            file_name="memory.txt",
            version_number=1,
            file_path=self.create_test_file("memory.txt", content.encode()),
            uploader=self.user1,
            virtual_path="/documents/memory.txt",
            mime_type="text/plain",
            checksum="memory_checksum"
        )
        
        # Extract text
        extracted_text = extract_text(file_version)
        
        # Get memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Memory usage should be reasonable (less than 10MB for this small file)
        self.assertLess(peak, 10 * 1024 * 1024)  # 10MB
        self.assertEqual(extracted_text, content)
    
    def test_slugify_edge_cases_in_path_generation(self):
        """Test edge cases in filename slugification"""
        from propylon_document_manager.utils.file_management import unique_file_upload_path
        
        instance = Mock()
        
        edge_cases = [
            ("", ""),  # Empty filename
            ("....", ""),  # Only dots
            ("___", ""),  # Only underscores  
            ("---", ""),  # Only dashes
            ("   ", ""),  # Only spaces
            ("файл.txt", ""),  # Non-Latin characters
            ("文件.pdf", ""),  # Chinese characters
            ("αρχείο.doc", ""),  # Greek characters
            ("123", "123"),  # Only numbers
        ]
        
        for filename, expected_slug_content in edge_cases:
            with self.subTest(filename=filename):
                path = unique_file_upload_path(instance, filename)
                
                # Should generate valid path regardless of input
                self.assertIsInstance(path, str)
                self.assertGreater(len(path), 8)  # At least date part
                
                if expected_slug_content:
                    self.assertIn(expected_slug_content, path)


class MimeTypeGuessingTest(TestCase):
    """Test cases for MIME type guessing functionality"""
    
    def test_mime_type_guessing_by_extension(self):
        """Test MIME type guessing based on file extensions"""
        import mimetypes
        
        test_cases = [
            ("document.txt", "text/plain"),
            ("data.json", "application/json"),
            ("page.html", "text/html"),
            ("style.css", "text/css"),
            ("script.js", "application/javascript"),
            ("archive.zip", "application/zip"),
            ("image.png", "image/png"),
            ("image.jpg", "image/jpeg"),
            ("document.pdf", "application/pdf"),
        ]
        
        for filename, expected_mime in test_cases:
            with self.subTest(filename=filename):
                guessed_mime, _ = mimetypes.guess_type(filename)
                
                # Some systems might return slightly different MIME types
                # so we check for either exact match or reasonable alternatives
                if expected_mime == "application/javascript":
                    self.assertIn(guessed_mime, [
                        "application/javascript", 
                        "text/javascript"
                    ])
                else:
                    self.assertEqual(guessed_mime, expected_mime)
    
    def test_mime_type_guessing_case_insensitive(self):
        """Test that MIME type guessing is case insensitive"""
        import mimetypes
        
        test_cases = [
            ("FILE.TXT", "file.txt"),
            ("DATA.JSON", "data.json"), 
            ("PAGE.HTML", "page.html"),
            ("IMAGE.PNG", "image.png"),
        ]
        
        for upper_filename, lower_filename in test_cases:
            with self.subTest(filename=upper_filename):
                upper_mime, _ = mimetypes.guess_type(upper_filename)
                lower_mime, _ = mimetypes.guess_type(lower_filename)
                
                # Should return same MIME type regardless of case
                self.assertEqual(upper_mime, lower_mime)
    
    def test_unknown_extension_handling(self):
        """Test handling of unknown file extensions"""
        import mimetypes
        
        unknown_files = [
            "file.unknownext",
            "file.xyz123", 
            "file.nonexistent",
            "file",  # No extension
        ]
        
        for filename in unknown_files:
            with self.subTest(filename=filename):
                guessed_mime, _ = mimetypes.guess_type(filename)
                
                # Should return None for unknown types
                self.assertIsNone(guessed_mime)


class FileSystemInteractionTest(BaseTestCase):
    """Test cases for file system interactions in utilities"""
    
    @patch('os.path.exists')
    def test_extract_text_file_existence_check(self, mock_exists):
        """Test file existence checking in text extraction"""
        from propylon_document_manager.utils.file_extraction import extract_text
        
        # Mock file doesn't exist
        mock_exists.return_value = False
        
        file_version = FileVersion.objects.create(
            file_name="missing.txt",
            version_number=1,
            file_path="missing/file/path.txt",
            uploader=self.user1,
            virtual_path="/documents/missing.txt",
            mime_type="text/plain",
            checksum="missing_checksum"
        )
        
        # Should handle missing file gracefully
        # The actual behavior depends on implementation
        try:
            extracted_text = extract_text(file_version)
            # If it succeeds, it should return some kind of error message or empty string
            self.assertIsInstance(extracted_text, str)
        except (FileNotFoundError, IOError):
            # If it raises an exception, that's also acceptable behavior
            pass
    
    def test_file_path_directory_creation(self):
        """Test that file upload paths don't require directory creation"""
        from propylon_document_manager.utils.file_management import unique_file_upload_path
        
        instance = Mock()
        filename = "test.txt"
        
        # Generate multiple paths
        paths = []
        for _ in range(10):
            path = unique_file_upload_path(instance, filename)
            paths.append(path)
        
        # All paths should be flat (no directory separators)
        for path in paths:
            self.assertNotIn('/', path)
            self.assertNotIn('\\', path)
    
    def test_file_path_length_limits(self):
        """Test that generated file paths respect system limits"""
        from propylon_document_manager.utils.file_management import unique_file_upload_path
        
        instance = Mock()
        
        # Test with very long filename
        long_filename = "a" * 200 + ".txt"
        path = unique_file_upload_path(instance, long_filename)
        
        # Most file systems have a 255 character limit for filenames
        self.assertLessEqual(len(path), 255)
        
        # Path should still be valid
        self.assertTrue(path.endswith('.txt'))
        self.assertGreater(len(path), 10)  # Should have some content