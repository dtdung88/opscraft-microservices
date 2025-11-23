"""Unit tests for services"""
from unittest.mock import Mock, patch

import pytest

from shared.exceptions.custom_exceptions import ResourceNotFoundError
from shared.services.base_service import BaseService


class TestBaseService:
    """Test base service functionality"""

    @pytest.fixture
    def mock_model(self):
        """Mock SQLAlchemy model"""

        class MockModel:
            id = 1
            name = "test"

        return MockModel

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()

    @pytest.fixture
    def service(self, mock_db, mock_model):
        """Create service instance"""
        return BaseService(mock_db, mock_model, "test_resource")

    def test_get_existing(self, service, mock_db, mock_model):
        """Test getting existing resource"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_model()

        result = service.get(1)
        assert result is not None
        assert result.id == 1

    def test_get_not_found(self, service, mock_db):
        """Test getting non-existent resource"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.get(999)
        assert result is None

    def test_get_or_404_existing(self, service, mock_db, mock_model):
        """Test get_or_404 with existing resource"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_model()

        result = service.get_or_404(1)
        assert result is not None

    def test_get_or_404_not_found(self, service, mock_db):
        """Test get_or_404 with non-existent resource"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ResourceNotFoundError):
            service.get_or_404(999)
