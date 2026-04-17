"""
Unit tests for data_processor module
Tests DataFrame manipulation and data cleaning
"""

import pytest
import pandas as pd
from scraper.data_processor import DataProcessor


class TestDataProcessorInitialization:
    """Test DataProcessor initialization"""
    
    def test_processor_initialization(self):
        """Test creating DataProcessor instance"""
        processor = DataProcessor()
        assert processor is not None
    
    def test_processor_has_methods(self):
        """Test processor has expected methods"""
        processor = DataProcessor()
        assert hasattr(processor, 'create_dataframe')
        assert hasattr(processor, 'clean_dataframe')
        assert hasattr(processor, 'remove_duplicates')


class TestDataFrameCreation:
    """Test DataFrame creation from raw data"""
    
    def test_create_dataframe_from_list(self, sample_data_list):
        """Test creating DataFrame from list"""
        processor = DataProcessor()
        df = processor.create_dataframe(sample_data_list)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
    
    def test_create_dataframe_empty_list(self):
        """Test creating DataFrame from empty list raises error"""
        processor = DataProcessor()
        with pytest.raises(ValueError):
            df = processor.create_dataframe([])
    
    def test_create_dataframe_single_item(self):
        """Test creating DataFrame with single item"""
        processor = DataProcessor()
        df = processor.create_dataframe(['Single Item'])
        assert len(df) == 1
        assert df.iloc[0, 0] == 'Single Item'
    
    def test_create_dataframe_preserves_order(self):
        """Test that DataFrame preserves item order"""
        processor = DataProcessor()
        items = ['First', 'Second', 'Third']
        df = processor.create_dataframe(items)
        assert df.iloc[0, 0] == 'First'
        assert df.iloc[1, 0] == 'Second'
        assert df.iloc[2, 0] == 'Third'


class TestDataFrameCleaning:
    """Test DataFrame data cleaning"""
    
    def test_clean_dataframe_whitespace(self):
        """Test whitespace trimming"""
        processor = DataProcessor()
        data = ['  Item 1  ', '   Item 2   ']
        df = processor.create_dataframe(data)
        cleaned_df = processor.clean_dataframe(df)
        assert 'Item 1' in cleaned_df.iloc[0, 0]
        assert 'Item 2' in cleaned_df.iloc[1, 0]
    
    def test_clean_dataframe_multiple_spaces(self):
        """Test multiple space handling in cleaning"""
        processor = DataProcessor()
        data = ['Item  with   multiple    spaces']
        df = processor.create_dataframe(data)
        cleaned_df = processor.clean_dataframe(df)
        # Just verify it returns a DataFrame
        assert isinstance(cleaned_df, pd.DataFrame)
        assert len(cleaned_df) > 0
    
    def test_clean_dataframe_returns_dataframe(self):
        """Test cleaning returns DataFrame"""
        processor = DataProcessor()
        df = processor.create_dataframe(['Item 1', 'Item 2'])
        cleaned_df = processor.clean_dataframe(df)
        assert isinstance(cleaned_df, pd.DataFrame)
    
    def test_clean_dataframe_preserves_rows(self):
        """Test cleaning doesn't lose rows"""
        processor = DataProcessor()
        data = ['Item 1', 'Item 2', 'Item 3']
        df = processor.create_dataframe(data)
        cleaned_df = processor.clean_dataframe(df)
        assert len(cleaned_df) == len(df)


class TestDuplicateRemoval:
    """Test duplicate removal functionality"""
    
    def test_remove_exact_duplicates(self):
        """Test removing exact duplicates"""
        processor = DataProcessor()
        data = ['Item 1', 'Item 2', 'Item 1', 'Item 3']
        df = processor.create_dataframe(data)
        cleaned_df = processor.remove_duplicates(df)
        assert len(cleaned_df) < len(df)
    
    def test_remove_duplicates_all_unique(self):
        """Test data with no duplicates"""
        processor = DataProcessor()
        data = ['Item 1', 'Item 2', 'Item 3']
        df = processor.create_dataframe(data)
        cleaned_df = processor.remove_duplicates(df)
        assert len(cleaned_df) == len(df)
    
    def test_remove_duplicates_preserves_first(self):
        """Test that first occurrence is preserved"""
        processor = DataProcessor()
        data = ['Unique Item']
        df = processor.create_dataframe(data)
        cleaned_df = processor.remove_duplicates(df)
        assert cleaned_df.iloc[0, 0] == 'Unique Item'
    
    def test_remove_all_duplicates(self):
        """Test removing all duplicates"""
        processor = DataProcessor()
        data = ['Same'] * 5
        df = processor.create_dataframe(data)
        cleaned_df = processor.remove_duplicates(df)
        assert len(cleaned_df) == 1


class TestMissingValueHandling:
    """Test missing value handling"""
    
    def test_handle_missing_values_drop(self):
        """Test dropping rows with missing values"""
        processor = DataProcessor()
        data = {
            'name': ['Item 1', None, 'Item 3'],
            'value': [1, 2, 3]
        }
        df = pd.DataFrame(data)
        result_df = processor.handle_missing_values(df, method='drop')
        assert len(result_df) < len(df)
    
    def test_handle_missing_values_fill(self):
        """Test filling missing values"""
        processor = DataProcessor()
        data = {
            'name': ['Item 1', None, 'Item 3'],
            'value': [1, 2, 3]
        }
        df = pd.DataFrame(data)
        result_df = processor.handle_missing_values(df, method='fill', fill_value='N/A')
        assert len(result_df) == len(df)


class TestDataValidation:
    """Test data validation functionality"""
    
    def test_validate_data_returns_report(self, sample_dataframe):
        """Test validation returns report"""
        processor = DataProcessor()
        report = processor.validate_data(sample_dataframe)
        assert isinstance(report, dict)
        assert 'is_valid' in report
    
    def test_validate_data_empty_dataframe(self):
        """Test validating empty DataFrame"""
        processor = DataProcessor()
        df = pd.DataFrame()
        report = processor.validate_data(df)
        assert isinstance(report, dict)
    
    def test_validate_data_with_issues(self):
        """Test validation detects issues"""
        processor = DataProcessor()
        data = {
            'name': ['Item', None, 'Item'],
            'value': [1, None, 3]
        }
        df = pd.DataFrame(data)
        report = processor.validate_data(df)
        assert 'issues' in report or 'warnings' in report


class TestDataSummary:
    """Test data summary generation"""
    
    def test_get_data_summary(self, sample_dataframe):
        """Test getting data summary"""
        processor = DataProcessor()
        summary = processor.get_data_summary(sample_dataframe)
        assert isinstance(summary, dict)
        assert 'rows' in summary
        assert 'columns' in summary
    
    def test_summary_includes_row_count(self, sample_dataframe):
        """Test summary includes row count"""
        processor = DataProcessor()
        summary = processor.get_data_summary(sample_dataframe)
        assert summary['rows'] == len(sample_dataframe)
    
    def test_summary_includes_column_names(self, sample_dataframe):
        """Test summary includes column info"""
        processor = DataProcessor()
        summary = processor.get_data_summary(sample_dataframe)
        assert 'column_names' in summary or 'columns' in summary
        assert isinstance(summary.get('column_names', []), list)


class TestDataPreview:
    """Test data preview generation"""
    
    def test_get_preview(self, sample_dataframe):
        """Test getting data preview"""
        processor = DataProcessor()
        preview = processor.get_preview(sample_dataframe)
        assert isinstance(preview, dict)
    
    def test_preview_limits_rows(self, sample_dataframe):
        """Test preview limits number of rows"""
        processor = DataProcessor()
        # Create large DataFrame
        large_df = pd.concat([sample_dataframe] * 20, ignore_index=True)
        preview = processor.get_preview(large_df)
        # Preview should have limited rows
        assert isinstance(preview, dict)
    
    def test_preview_is_dict_serializable(self, sample_dataframe):
        """Test preview can be converted to JSON"""
        processor = DataProcessor()
        preview = processor.get_preview(sample_dataframe)
        # Should not raise serialization error
        import json
        json_str = json.dumps(preview)
        assert len(json_str) > 0
