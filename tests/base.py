# src/tests/base.py
"""
Base test classes and common utilities for all tests
"""

import os
import tempfile
import shutil
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from propylon_document_manager.file_versions.models import User


# Create a temporary directory for test files
TEST_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class BaseTestCase(TestCase):
    """Base test case with common setup and teardown"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test directory
        os.makedirs(TEST_MEDIA_ROOT, exist_ok=True)
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Clean up test files
        if os.path.exists(TEST_MEDIA_ROOT):
            shutil.rmtree(TEST_MEDIA_ROOT)
    
    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            password='testpass123',
            name='Test User 1'
        )
        self.user2 = User.objects.create_user(
            email='user2@test.com', 
            password='testpass123',
            name='Test User 2'
        )
        
        # Create test file content
        self.test_file_content = b"This is test file content for testing purposes."
        self.test_file = SimpleUploadedFile(
            "test_document.txt",
            self.test_file_content,
            content_type="text/plain"
        )
    
    def create_test_file(self, filename="test.txt", content=b"test content", content_type="text/plain"):
        """Helper method to create test files"""
        return SimpleUploadedFile(filename, content, content_type=content_type)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class BaseAPITestCase(APITestCase):
    """Base API test case with authentication setup"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.makedirs(TEST_MEDIA_ROOT, exist_ok=True)
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        if os.path.exists(TEST_MEDIA_ROOT):
            shutil.rmtree(TEST_MEDIA_ROOT)
    
    def setUp(self):
        """Set up test users and authentication"""
        self.user1 = User.objects.create_user(
            email='api_user1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='api_user2@test.com',
            password='testpass123'
        )
        
        # Create tokens for authentication
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)
    
    def authenticate_user1(self):
        """Authenticate as user1"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
    
    def authenticate_user2(self):
        """Authenticate as user2"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
    
    def create_test_file(self, filename="test.txt", content=b"test content", content_type="text/plain"):
        """Helper method to create test files"""
        return SimpleUploadedFile(filename, content, content_type=content_type)