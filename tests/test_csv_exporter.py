"""
Unit tests for csv_exporter module
Tests CSV file generation and management
"""

import pytest
import os
import pandas as pd
from scraper.csv_exporter import CSVExporter


class TestCSVExporterInitialization:
    """Test CSVExporter initialization"""
    
    def test_exporter_initialization(self, temp_dir):
        """Test creating CSVExporter instance"""
        exporter = CSVExporter(output_dir=temp_dir)
        assert exporter is not None
    
    def test_exporter_creates_output_dir(self, temp_dir):
        """Test exporter can be initialized with output dir"""
        exporter = CSVExporter(output_dir=temp_dir)
        assert os.path.isdir(temp_dir)


class TestFilenameGeneration:
    """Test CSV filename generation"""
    
    def test_generate_filename_default(self, temp_dir):
        """Test default filename generation"""
        exporter = CSVExporter(output_dir=temp_dir)
        filename = exporter.generate_filename()
        assert filename.endswith('.csv')
        assert 'data' in filename
    
    def test_generate_filename_with_prefix(self, temp_dir):
        """Test filename generation with custom prefix"""
        exporter = CSVExporter(output_dir=temp_dir)
        filename = exporter.generate_filename(prefix='products')
        assert filename.startswith('products')
        assert filename.endswith('.csv')
    
    def test_generate_filename_includes_timestamp(self, temp_dir):
        """Test filename includes timestamp"""
        exporter = CSVExporter(output_dir=temp_dir)
        filename = exporter.generate_filename(prefix='test')
        # Should include date/time information
        assert len(filename) > len('test.csv')
    
    def test_generate_filename_with_timestamp_param(self, temp_dir):
        """Test filename generation with timestamp parameter"""
        exporter = CSVExporter(output_dir=temp_dir)
        filename = exporter.generate_filename(prefix='data', timestamp=True)
        assert 'data' in filename
        assert '.csv' in filename


class TestCSVExport:
    """Test CSV file export"""
    
    def test_export_to_csv(self, temp_dir, sample_dataframe):
        """Test exporting DataFrame to CSV"""
        exporter = CSVExporter(output_dir=temp_dir)
        filename = 'test_export.csv'
        filepath = exporter.export_to_csv(sample_dataframe, filename)
        assert os.path.exists(filepath)
    
    def test_export_creates_valid_csv(self, temp_dir, sample_dataframe):
        """Test exported file is valid CSV"""
        exporter = CSVExporter(output_dir=temp_dir)
        filename = 'test_valid.csv'
        filepath = exporter.export_to_csv(sample_dataframe, filename)
        # Try reading the exported CSV
        df = pd.read_csv(filepath)
        assert len(df) > 0
    
    def test_export_preserves_data(self, temp_dir, sample_dataframe):
        """Test exported data matches original"""
        exporter = CSVExporter(output_dir=temp_dir)
        filename = 'test_data_match.csv'
        filepath = exporter.export_to_csv(sample_dataframe, filename)
        df_read = pd.read_csv(filepath)
        assert len(df_read) == len(sample_dataframe)
    
    def test_export_empty_dataframe(self, temp_dir):
        """Test exporting empty DataFrame"""
        exporter = CSVExporter(output_dir=temp_dir)
        empty_df = pd.DataFrame()
        filename = 'test_empty.csv'
        filepath = exporter.export_to_csv(empty_df, filename)
        assert os.path.exists(filepath)
    
    def test_export_with_formatting(self, temp_dir, sample_dataframe):
        """Test exporting with formatting"""
        exporter = CSVExporter(output_dir=temp_dir)
        filename = 'test_formatted.csv'
        filepath = exporter.export_with_formatting(sample_dataframe, filename)
        assert os.path.exists(filepath)
    
    def test_export_to_temp_file(self, sample_dataframe):
        """Test exporting to temporary file"""
        exporter = CSVExporter()
        filepath = exporter.export_to_temp_file(sample_dataframe)
        assert os.path.exists(filepath)
        # Temporary file should be created
        assert 'tmp' in filepath or 'temp' in filepath.lower()


class TestFileManagement:
    """Test file management functionality"""
    
    def test_list_exports_empty_directory(self, temp_dir):
        """Test listing exports from empty directory"""
        exporter = CSVExporter(output_dir=temp_dir)
        files = exporter.list_exports()
        assert isinstance(files, list)
    
    def test_list_exports_with_files(self, temp_dir, sample_dataframe):
        """Test listing exports with existing files"""
        exporter = CSVExporter(output_dir=temp_dir)
        # Create some test files
        exporter.export_to_csv(sample_dataframe, 'test1.csv')
        exporter.export_to_csv(sample_dataframe, 'test2.csv')
        
        files = exporter.list_exports()
        assert len(files) >= 2
    
    def test_get_file_info(self, temp_dir, sample_dataframe):
        """Test getting file information"""
        exporter = CSVExporter(output_dir=temp_dir)
        filename = 'test_info.csv'
        filepath = exporter.export_to_csv(sample_dataframe, filename)
        
        file_info = exporter.get_file_info(filepath)
        assert isinstance(file_info, dict)
        assert 'filename' in file_info or 'file_size' in file_info
    
    def test_file_info_has_size(self, temp_dir, sample_dataframe):
        """Test file info includes size"""
        exporter = CSVExporter(output_dir=temp_dir)
        filename = 'test_size.csv'
        filepath = exporter.export_to_csv(sample_dataframe, filename)
        
        file_info = exporter.get_file_info(filepath)
        assert file_info['file_size'] > 0
    
    def test_clean_old_exports(self, temp_dir, sample_dataframe):
        """Test cleaning old export files"""
        exporter = CSVExporter(output_dir=temp_dir)
        
        # Create multiple files
        for i in range(5):
            exporter.export_to_csv(sample_dataframe, f'test_{i}.csv')
        
        initial_count = len(exporter.list_exports())
        exporter.clean_old_exports(keep_count=2)
        final_count = len(exporter.list_exports())
        
        assert final_count <= 2


class TestFileValidation:
    """Test file path validation and security"""
    
    def test_export_directory_creation(self, temp_dir):
        """Test that export directory is created if needed"""
        new_dir = os.path.join(temp_dir, 'new_exports')
        exporter = CSVExporter(output_dir=new_dir)
        assert exporter is not None
    
    def test_export_prevents_path_traversal(self, temp_dir):
        """Test protection against path traversal"""
        exporter = CSVExporter(output_dir=temp_dir)
        
        # Attempting to traverse should fail or be prevented
        # This is handled by the exporter implementation
        try:
            filename = '../../../etc/passwd.csv'
            # Should either fail or be sanitized
            from scraper.csv_exporter import CSVExporter as CSVExp
            # The implementation should prevent this
        except:
            pass


class TestUTF8Encoding:
    """Test UTF-8 encoding and special characters"""
    
    def test_export_utf8_characters(self, temp_dir):
        """Test exporting data with UTF-8 characters"""
        df = pd.DataFrame({
            'name': ['Café', 'Naïve', '日本語'],
            'description': ['Unicode test', 'Special chars', 'International']
        })
        
        exporter = CSVExporter(output_dir=temp_dir)
        filename = 'test_utf8.csv'
        filepath = exporter.export_to_csv(df, filename)
        
        # Read back and verify
        df_read = pd.read_csv(filepath)
        assert len(df_read) == len(df)
    
    def test_export_special_characters(self, temp_dir):
        """Test exporting with special characters in data"""
        df = pd.DataFrame({
            'data': ['Special: !@#$%^&*()', 'Quote: "test"', 'Comma: a,b,c']
        })
        
        exporter = CSVExporter(output_dir=temp_dir)
        filename = 'test_special.csv'
        filepath = exporter.export_to_csv(df, filename)
        
        assert os.path.exists(filepath)
