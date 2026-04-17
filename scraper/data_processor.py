"""
Data Processing Module
Handles data transformation, cleaning, and preparation using Pandas
"""

import logging
import pandas as pd
from typing import List, Dict, Optional, Any
import re

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Data processing and transformation using Pandas
    Handles DataFrame creation, cleaning, validation, and formatting
    """
    
    def __init__(self, max_rows: int = 1000):
        """
        Initialize data processor
        
        Args:
            max_rows (int): Maximum rows to display/process
        """
        self.max_rows = max_rows
    
    def create_dataframe(self, raw_data: List[Any], column_name: str = 'Data') -> pd.DataFrame:
        """
        Create DataFrame from raw extracted data
        
        Args:
            raw_data (List): List of extracted items (strings or dicts)
            column_name (str): Name for the data column
            
        Returns:
            pd.DataFrame: Created DataFrame
            
        Raises:
            ValueError: If data is empty or invalid
        """
        try:
            if not raw_data:
                raise ValueError("Data list is empty")
            
            logger.info(f"Creating DataFrame with {len(raw_data)} items")
            
            # If data contains dictionaries, use them directly
            if isinstance(raw_data[0], dict):
                df = pd.DataFrame(raw_data)
            else:
                # Create DataFrame from list
                df = pd.DataFrame({column_name: raw_data})
            
            logger.info(f"DataFrame created: {df.shape[0]} rows, {df.shape[1]} columns")
            
            return df
        
        except Exception as e:
            logger.error(f"Error creating DataFrame: {str(e)}")
            raise ValueError(f"Failed to create DataFrame: {str(e)}")
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and normalize DataFrame
        
        Args:
            df (pd.DataFrame): DataFrame to clean
            
        Returns:
            pd.DataFrame: Cleaned DataFrame
        """
        try:
            logger.info("Starting data cleaning process")
            
            # Make a copy to avoid modifying original
            df = df.copy()
            
            # Remove leading/trailing whitespace from all string columns
            for col in df.select_dtypes(include=['object']).columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.strip()
            
            # Handle special characters and normalize
            for col in df.select_dtypes(include=['object']).columns:
                if df[col].dtype == 'object':
                    # Remove multiple spaces
                    df[col] = df[col].astype(str).str.replace(r'\s+', ' ', regex=True)
                    
                    # Remove null/None strings
                    df[col] = df[col].replace(['None', 'none', 'null', 'NULL', ''], pd.NA)
            
            logger.info("Data cleaning completed")
            
            return df
        
        except Exception as e:
            logger.error(f"Error cleaning DataFrame: {str(e)}")
            raise
    
    def remove_duplicates(self, df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Remove duplicate rows
        
        Args:
            df (pd.DataFrame): DataFrame to process
            subset (List[str]): Column names to consider for duplicates (None = all)
            
        Returns:
            pd.DataFrame: DataFrame with duplicates removed
        """
        try:
            original_count = len(df)
            
            if subset:
                df = df.drop_duplicates(subset=subset, keep='first')
            else:
                df = df.drop_duplicates(keep='first')
            
            removed_count = original_count - len(df)
            
            logger.info(f"Removed {removed_count} duplicate rows. Remaining: {len(df)}")
            
            return df
        
        except Exception as e:
            logger.error(f"Error removing duplicates: {str(e)}")
            raise
    
    def handle_missing_values(self, df: pd.DataFrame, 
                             method: str = 'drop', 
                             fill_value: Any = None) -> pd.DataFrame:
        """
        Handle missing values in DataFrame
        
        Args:
            df (pd.DataFrame): DataFrame to process
            method (str): 'drop' to remove rows with NaN, 'fill' to replace with value
            fill_value (Any): Value to fill missing data with (if method='fill')
            
        Returns:
            pd.DataFrame: DataFrame with missing values handled
        """
        try:
            original_rows = len(df)
            
            if method == 'drop':
                df = df.dropna()
                removed = original_rows - len(df)
                logger.info(f"Dropped {removed} rows with missing values")
            
            elif method == 'fill':
                if fill_value is None:
                    fill_value = 'N/A'
                df = df.fillna(fill_value)
                logger.info(f"Filled missing values with: {fill_value}")
            
            return df
        
        except Exception as e:
            logger.error(f"Error handling missing values: {str(e)}")
            raise
    
    def detect_data_types(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Detect and return data types of columns
        
        Args:
            df (pd.DataFrame): DataFrame to analyze
            
        Returns:
            Dict[str, str]: Column names and their detected types
        """
        try:
            data_types = {}
            
            for col in df.columns:
                dtype = str(df[col].dtype)
                data_types[col] = dtype
            
            logger.info(f"Detected data types: {data_types}")
            
            return data_types
        
        except Exception as e:
            logger.error(f"Error detecting data types: {str(e)}")
            raise
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get summary statistics of DataFrame
        
        Args:
            df (pd.DataFrame): DataFrame to summarize
            
        Returns:
            Dict: Summary information
        """
        try:
            summary = {
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': list(df.columns),
                'data_types': {col: str(dtype) for col, dtype in df.dtypes.items()},
                'missing_values': {col: int(count) for col, count in df.isnull().sum().items()},
                'memory_usage': str(df.memory_usage(deep=True).sum() / 1024) + ' KB'
            }
            
            logger.info(f"Data summary: {summary}")
            
            return summary
        
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            raise
    
    def validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate DataFrame for data quality
        
        Args:
            df (pd.DataFrame): DataFrame to validate
            
        Returns:
            Dict: Validation results
        """
        try:
            validation_result = {
                'is_valid': True,
                'issues': [],
                'warnings': [],
                'stats': {}
            }
            
            # Check if DataFrame is empty
            if df.empty:
                validation_result['is_valid'] = False
                validation_result['issues'].append('DataFrame is empty')
            
            # Check for columns
            if len(df.columns) == 0:
                validation_result['is_valid'] = False
                validation_result['issues'].append('No columns found')
            
            # Check for missing values
            missing_count = df.isnull().sum().sum()
            if missing_count > 0:
                validation_result['warnings'].append(
                    f'Found {missing_count} missing values'
                )
            
            # Check for duplicates
            duplicate_count = df.duplicated().sum()
            if duplicate_count > 0:
                validation_result['warnings'].append(
                    f'Found {duplicate_count} duplicate rows'
                )
            
            # Add stats
            validation_result['stats'] = {
                'rows': len(df),
                'columns': len(df.columns),
                'missing_values': int(missing_count),
                'duplicate_rows': int(duplicate_count)
            }
            
            logger.info(f"Data validation completed: {validation_result}")
            
            return validation_result
        
        except Exception as e:
            logger.error(f"Error validating data: {str(e)}")
            raise
    
    def format_for_export(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Format DataFrame for CSV export
        
        Args:
            df (pd.DataFrame): DataFrame to format
            
        Returns:
            pd.DataFrame: Formatted DataFrame
        """
        try:
            logger.info("Formatting DataFrame for export")
            
            df = df.copy()
            
            # Convert all columns to string to ensure compatibility
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str)
            
            # Limit rows if necessary
            if len(df) > self.max_rows:
                logger.warning(f"DataFrame has {len(df)} rows, limiting to {self.max_rows}")
                df = df.head(self.max_rows)
            
            logger.info("DataFrame formatted successfully")
            
            return df
        
        except Exception as e:
            logger.error(f"Error formatting DataFrame: {str(e)}")
            raise
    
    def process_scrape_data(self, scrape_result: Dict) -> pd.DataFrame:
        """
        Process complete scrape result into clean DataFrame
        
        Args:
            scrape_result (Dict): Result from scraper with 'data' key
            
        Returns:
            pd.DataFrame: Processed and cleaned DataFrame
        """
        try:
            logger.info("Processing scrape data")
            
            # Extract data
            raw_data = scrape_result.get('data', [])
            
            if not raw_data:
                raise ValueError("No data to process")
            
            # Get column name from selector if available
            selector = scrape_result.get('selector', 'Data').split('.')[-1].split('#')[-1] or 'Data'
            
            # Create DataFrame
            df = self.create_dataframe(raw_data, column_name=selector)
            
            # Clean data
            df = self.clean_dataframe(df)
            
            # Remove duplicates
            df = self.remove_duplicates(df)
            
            # Handle missing values
            df = self.handle_missing_values(df, method='drop')
            
            # Format for export
            df = self.format_for_export(df)
            
            logger.info("Data processing completed successfully")
            
            return df
        
        except Exception as e:
            logger.error(f"Error processing scrape data: {str(e)}")
            raise
    
    def get_preview(self, df: pd.DataFrame, rows: int = 10) -> Dict[str, Any]:
        """
        Get preview of DataFrame
        
        Args:
            df (pd.DataFrame): DataFrame to preview
            rows (int): Number of rows to show
            
        Returns:
            Dict: Preview data in JSON-serializable format
        """
        try:
            preview_df = df.head(rows)
            
            return {
                'total_rows': len(df),
                'columns': list(df.columns),
                'preview': preview_df.to_dict('records'),
                'data_types': {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
        
        except Exception as e:
            logger.error(f"Error getting preview: {str(e)}")
            raise
