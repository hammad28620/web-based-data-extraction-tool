"""
CSV Export Module
Handles exporting DataFrame to CSV files
"""

import logging
import os
import pandas as pd
from datetime import datetime
from typing import Optional
import tempfile

logger = logging.getLogger(__name__)


class CSVExporter:
    """
    Handle CSV export functionality
    """
    
    def __init__(self, output_dir: str = None):
        """
        Initialize CSV exporter
        
        Args:
            output_dir (str): Directory for CSV files (default: system temp or 'data')
        """
        if output_dir is None:
            # Use data directory or temp directory
            output_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        
        self.output_dir = output_dir
        
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"CSV Exporter initialized. Output directory: {output_dir}")
    
    def generate_filename(self, prefix: str = 'data', timestamp: bool = True) -> str:
        """
        Generate CSV filename
        
        Args:
            prefix (str): Filename prefix (default: 'data')
            timestamp (bool): Whether to include timestamp
            
        Returns:
            str: Generated filename
        """
        try:
            if timestamp:
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{prefix}_{ts}.csv"
            else:
                filename = f"{prefix}.csv"
            
            logger.info(f"Generated filename: {filename}")
            
            return filename
        
        except Exception as e:
            logger.error(f"Error generating filename: {str(e)}")
            raise
    
    def export_to_csv(self, 
                     df: pd.DataFrame, 
                     filename: Optional[str] = None,
                     include_index: bool = False,
                     encoding: str = 'utf-8') -> str:
        """
        Export DataFrame to CSV file
        
        Args:
            df (pd.DataFrame): DataFrame to export
            filename (str): Output filename (auto-generated if None)
            include_index (bool): Whether to include index column
            encoding (str): File encoding
            
        Returns:
            str: File path to exported CSV
            
        Raises:
            IOError: If file write fails
        """
        try:
            # Generate filename if not provided
            if filename is None:
                filename = self.generate_filename()
            
            # Build full file path
            filepath = os.path.join(self.output_dir, filename)
            
            logger.info(f"Exporting DataFrame to CSV: {filepath}")
            logger.info(f"DataFrame shape: {df.shape[0]} rows, {df.shape[1]} columns")
            
            # Export to CSV - allow empty dataframes
            df.to_csv(
                filepath,
                index=include_index,
                encoding=encoding,
                quoting=1  # QUOTE_ALL for safety
            )
            
            # Verify file was created
            if not os.path.exists(filepath):
                raise IOError(f"Failed to create file: {filepath}")
            
            file_size = os.path.getsize(filepath)
            logger.info(f"CSV export successful. File size: {file_size} bytes")
            
            return filepath
        
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            raise
    
    def export_with_formatting(self, 
                              df: pd.DataFrame,
                              filename: Optional[str] = None,
                              add_headers: bool = True,
                              add_metadata: bool = False) -> str:
        """
        Export DataFrame with additional formatting
        
        Args:
            df (pd.DataFrame): DataFrame to export
            filename (str): Output filename
            add_headers (bool): Include column headers
            add_metadata (bool): Add metadata rows at top
            
        Returns:
            str: File path to exported CSV
        """
        try:
            if filename is None:
                filename = self.generate_filename()
            
            filepath = os.path.join(self.output_dir, filename)
            
            logger.info(f"Exporting DataFrame with formatting to: {filepath}")
            
            # Create output file
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                # Add metadata comments if requested
                if add_metadata:
                    f.write(f"# Exported: {datetime.now().isoformat()}\n")
                    f.write(f"# Rows: {len(df)}\n")
                    f.write(f"# Columns: {len(df.columns)}\n\n")
                
                # Write CSV
                if add_headers:
                    f.write(','.join([f'"{col}"' for col in df.columns]) + '\n')
                
                for _, row in df.iterrows():
                    f.write(','.join([f'"{str(val)}"' for val in row]) + '\n')
            
            logger.info("Export with formatting completed")
            
            return filepath
        
        except Exception as e:
            logger.error(f"Error exporting with formatting: {str(e)}")
            raise
    
    def export_to_temp_file(self, 
                           df: pd.DataFrame,
                           prefix: str = 'scrape_') -> str:
        """
        Export DataFrame to temporary file
        
        Args:
            df (pd.DataFrame): DataFrame to export
            prefix (str): Temp file prefix
            
        Returns:
            str: Temp file path
        """
        try:
            logger.info("Exporting to temporary file")
            
            # Create temp file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.csv',
                prefix=prefix,
                delete=False,
                encoding='utf-8'
            ) as tmp:
                filepath = tmp.name
                df.to_csv(tmp, index=False)
            
            logger.info(f"Temporary file created: {filepath}")
            
            return filepath
        
        except Exception as e:
            logger.error(f"Error exporting to temp file: {str(e)}")
            raise
    
    def get_file_info(self, filepath: str) -> dict:
        """
        Get information about exported CSV file
        
        Args:
            filepath (str): Path to CSV file
            
        Returns:
            dict: File information
        """
        try:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"File not found: {filepath}")
            
            file_stat = os.stat(filepath)
            
            info = {
                'filename': os.path.basename(filepath),
                'path': filepath,
                'file_size': file_stat.st_size,  # Bytes
                'size_bytes': file_stat.st_size,
                'size_kb': round(file_stat.st_size / 1024, 2),
                'created': datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            }
            
            logger.info(f"File info retrieved: {info}")
            
            return info
        
        except Exception as e:
            logger.error(f"Error getting file info: {str(e)}")
            raise
    
    def list_exports(self) -> list:
        """
        List all CSV files in export directory
        
        Returns:
            list: List of CSV filenames
        """
        try:
            if not os.path.exists(self.output_dir):
                return []
            
            files = [f for f in os.listdir(self.output_dir) if f.endswith('.csv')]
            
            logger.info(f"Found {len(files)} CSV files in export directory")
            
            return files
        
        except Exception as e:
            logger.error(f"Error listing exports: {str(e)}")
            raise
    
    def clean_old_exports(self, keep_count: int = 10) -> int:
        """
        Delete old export files, keeping only the most recent
        
        Args:
            keep_count (int): Number of recent files to keep
            
        Returns:
            int: Number of files deleted
        """
        try:
            files = self.list_exports()
            
            if len(files) <= keep_count:
                logger.info("No old files to clean")
                return 0
            
            # Sort by modification time
            file_paths = [os.path.join(self.output_dir, f) for f in files]
            file_paths.sort(key=os.path.getmtime, reverse=True)
            
            # Delete old files
            deleted_count = 0
            for old_file in file_paths[keep_count:]:
                try:
                    os.remove(old_file)
                    deleted_count += 1
                    logger.info(f"Deleted old export: {old_file}")
                except Exception as e:
                    logger.warning(f"Could not delete {old_file}: {str(e)}")
            
            logger.info(f"Cleaned {deleted_count} old export files")
            
            return deleted_count
        
        except Exception as e:
            logger.error(f"Error cleaning old exports: {str(e)}")
            raise
