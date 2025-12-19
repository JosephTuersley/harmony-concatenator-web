"""
Harmony Data Processor - Core processing logic
Concatenates Harmony high-content imaging output files from multiple plates.
"""
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

import pandas as pd
import yaml


# =============================================================================
# Constants
# =============================================================================

# Column names used in output
COL_PLATE_ID = 'Plate_ID'
COL_PLATE_NUMBER = 'Plate_number'
COL_REPLICATE = 'Replicate'
COL_WELL_ID = 'Well_ID'
COL_ROW = 'Row'
COL_COLUMN = 'Column'

# Plate format configurations: (rows, columns, total_wells)
PLATE_FORMATS: Dict[int, Tuple[int, int, int]] = {
    96: (8, 12, 96),
    384: (16, 24, 384),
    1536: (32, 48, 1536),
}

# Folders to skip during processing
SKIP_FOLDER_PREFIXES = ('.', '__')

# Required config fields
REQUIRED_CONFIG_FIELDS = ('plate_format', 'plates', 'input_files')


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ProcessingResult:
    """Result of processing a single file type."""
    success: bool
    file: str
    output: Optional[str] = None
    rows: int = 0
    columns: int = 0
    plates_processed: int = 0
    plates_skipped: int = 0
    reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'success': self.success,
            'file': self.file,
            'output': self.output,
            'rows': self.rows,
            'columns': self.columns,
            'plates_processed': self.plates_processed,
            'plates_skipped': self.plates_skipped,
            'reason': self.reason,
        }


@dataclass
class JobResult:
    """Result of a complete processing job."""
    files_processed: int
    files_failed: int
    plates_found: int
    results: List[ProcessingResult]
    logs: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'files_processed': self.files_processed,
            'files_failed': self.files_failed,
            'plates_found': self.plates_found,
            'results': [r.to_dict() for r in self.results],
            'logs': self.logs,
        }


# =============================================================================
# Helper Functions
# =============================================================================

def get_row_mapping(plate_format: int) -> Dict[int, str]:
    """
    Create row number to letter mapping based on plate format.
    
    Args:
        plate_format: Plate format (96, 384, or 1536)
        
    Returns:
        Dictionary mapping row numbers (1-indexed) to letters
        
    Raises:
        ValueError: If plate format is not supported
    """
    if plate_format not in PLATE_FORMATS:
        supported = ', '.join(str(f) for f in PLATE_FORMATS.keys())
        raise ValueError(f"Unsupported plate format: {plate_format}. Supported: {supported}")
    
    max_rows = PLATE_FORMATS[plate_format][0]
    
    row_map = {}
    for i in range(1, max_rows + 1):
        if i <= 26:
            # A-Z for rows 1-26
            row_map[i] = chr(64 + i)
        else:
            # AA, AB, AC... for rows 27+
            row_map[i] = 'A' + chr(64 + i - 26)
    
    return row_map


def create_well_id(row: int, col: int, row_mapping: Dict[int, str]) -> str:
    """
    Create Well_ID from row and column numbers.
    
    Args:
        row: Row number (1-indexed)
        col: Column number (1-indexed)
        row_mapping: Dictionary mapping row numbers to letters
        
    Returns:
        Well ID string (e.g., 'A01', 'P24')
    """
    row_letter = row_mapping.get(int(row), "?")
    return f"{row_letter}{int(col):02d}"


def find_data_start_row(filepath: str) -> int:
    """
    Find the row number where [Data] marker appears in a Harmony file.
    
    Harmony files have metadata at the top, followed by a [Data] marker,
    then the actual data with headers.
    
    Args:
        filepath: Path to the Harmony output file
        
    Returns:
        Row index (0-indexed) where data starts (line after [Data])
    """
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for i, line in enumerate(f):
            if line.strip().lower().startswith('[data]'):
                return i + 1
    
    # No [Data] marker found - assume data starts at row 0
    return 0


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load and validate configuration from YAML file.
    
    Args:
        config_path: Path to config.yml
        
    Returns:
        Configuration dictionary
        
    Raises:
        ValueError: If required fields are missing
        yaml.YAMLError: If YAML is invalid
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Validate required fields
    for field in REQUIRED_CONFIG_FIELDS:
        if field not in config:
            raise ValueError(f"Missing required config field: {field}")
    
    # Validate plate format
    if config['plate_format'] not in PLATE_FORMATS:
        supported = ', '.join(str(f) for f in PLATE_FORMATS.keys())
        raise ValueError(f"Invalid plate_format. Supported: {supported}")
    
    # Ensure plate barcodes are strings
    config['plates'] = {str(k): v for k, v in config['plates'].items()}
    
    return config


def should_skip_folder(folder_name: str) -> bool:
    """Check if a folder should be skipped during processing."""
    return any(folder_name.startswith(prefix) for prefix in SKIP_FOLDER_PREFIXES)


def is_plate_folder(folder_name: str) -> bool:
    """Check if a folder name matches the plate folder pattern (contains '__')."""
    return '__' in folder_name


def extract_barcode(folder_name: str) -> str:
    """Extract plate barcode from folder name (part before '__')."""
    return folder_name.split('__')[0]


# =============================================================================
# Main Processor Class
# =============================================================================

class HarmonyProcessor:
    """
    Process and concatenate Harmony high-content imaging data files.
    
    This class handles reading Harmony output files from multiple plates,
    concatenating them, and adding metadata columns (Plate_ID, Well_ID, etc.).
    """
    
    def __init__(self):
        """Initialize processor with empty log."""
        self._logs: List[str] = []
    
    @property
    def logs(self) -> List[str]:
        """Get processing logs."""
        return self._logs.copy()
    
    def _log(self, message: str) -> None:
        """Add a log message and print it."""
        self._logs.append(message)
        print(message)
    
    def _read_harmony_file(
        self, 
        filepath: str, 
        column_names: Optional[List[str]] = None
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Read a Harmony output file, auto-detecting the data start row.
        
        Args:
            filepath: Path to the file
            column_names: Expected column names (None for first file)
            
        Returns:
            Tuple of (DataFrame, column_names)
        """
        data_start = find_data_start_row(filepath)
        is_first_file = column_names is None
        
        if is_first_file:
            df = pd.read_csv(filepath, sep='\t', skiprows=data_start)
            column_names = df.columns.tolist()
        else:
            df = pd.read_csv(filepath, sep='\t', skiprows=data_start + 1, header=None)
            
            # Handle column count mismatch
            if len(df.columns) != len(column_names):
                self._log(f"    Warning: Column count mismatch. Expected {len(column_names)}, got {len(df.columns)}")
                
                if len(df.columns) > len(column_names):
                    df = df.iloc[:, :len(column_names)]
                else:
                    for i in range(len(df.columns), len(column_names)):
                        df[i] = pd.NA
            
            df.columns = column_names
        
        return df, column_names
    
    def _find_evaluation_folder(self, plate_folder: str) -> Optional[str]:
        """
        Find the first Evaluation folder within a plate folder.
        
        Args:
            plate_folder: Path to the plate folder
            
        Returns:
            Name of the Evaluation folder, or None if not found
        """
        try:
            eval_folders = [
                d for d in os.listdir(plate_folder)
                if d.startswith("Evaluation") and os.path.isdir(os.path.join(plate_folder, d))
            ]
            return sorted(eval_folders)[0] if eval_folders else None
        except OSError:
            return None
    
    def _add_metadata_columns(
        self,
        df: pd.DataFrame,
        plate_barcode: str,
        plate_number: int,
        replicate: int,
        row_mapping: Dict[int, str]
    ) -> pd.DataFrame:
        """
        Add metadata columns to a DataFrame.
        
        Adds Plate_ID, Plate_number, Replicate at the start,
        and Well_ID after the Column column (if Row and Column exist).
        """
        # Add plate identification columns at the start
        df.insert(0, COL_PLATE_ID, plate_barcode)
        df.insert(1, COL_PLATE_NUMBER, plate_number)
        df.insert(2, COL_REPLICATE, replicate)
        
        # Add Well_ID if Row and Column exist
        if COL_ROW in df.columns and COL_COLUMN in df.columns:
            df[COL_WELL_ID] = df.apply(
                lambda x: create_well_id(x[COL_ROW], x[COL_COLUMN], row_mapping), 
                axis=1
            )
            
            # Move Well_ID after Column
            cols = df.columns.tolist()
            cols.remove(COL_WELL_ID)
            col_idx = cols.index(COL_COLUMN) + 1
            cols.insert(col_idx, COL_WELL_ID)
            df = df[cols]
        
        return df
    
    def _process_file_type(
        self,
        input_dir: str,
        output_dir: str,
        file_pattern: str,
        config: Dict[str, Any],
        folder_mapping: Dict[str, str]
    ) -> ProcessingResult:
        """
        Process and concatenate a specific file type across all plates.
        
        Args:
            input_dir: Input directory containing plate folders
            output_dir: Output directory for concatenated file
            file_pattern: Name of file to look for (e.g., 'PlateResults.txt')
            config: Configuration dictionary
            folder_mapping: Mapping of folder names to plate barcodes
            
        Returns:
            ProcessingResult with success status and statistics
        """
        self._log(f"\nProcessing: {file_pattern}")
        
        plate_format = config['plate_format']
        plates_config = config['plates']
        row_mapping = get_row_mapping(plate_format)
        expected_wells = PLATE_FORMATS[plate_format][2]
        
        all_data: List[pd.DataFrame] = []
        column_names: Optional[List[str]] = None
        files_processed = 0
        files_skipped = 0
        
        for folder_name in sorted(folder_mapping.keys()):
            plate_barcode = folder_mapping[folder_name]
            folder_path = os.path.join(input_dir, folder_name)
            
            # Find evaluation folder
            eval_folder = self._find_evaluation_folder(folder_path)
            if eval_folder is None:
                self._log(f"  No Evaluation folders found in {folder_name}")
                continue
            
            target_file = os.path.join(folder_path, eval_folder, file_pattern)
            
            if not os.path.exists(target_file):
                files_skipped += 1
                continue
            
            self._log(f"  Processing: {folder_name}/{eval_folder}/{file_pattern}")
            
            try:
                # Read the file
                df, column_names = self._read_harmony_file(target_file, column_names)
                
                # Get plate info from config
                plate_info = plates_config.get(plate_barcode, {})
                plate_number = plate_info.get('plate_number', 0)
                replicate = plate_info.get('replicate', 0)
                
                if plate_barcode not in plates_config:
                    self._log(f"    Warning: Barcode {plate_barcode} not in config, using defaults")
                
                # Add metadata columns
                df = self._add_metadata_columns(df, plate_barcode, plate_number, replicate, row_mapping)
                
                self._log(f"    Shape: {df.shape[0]} rows x {df.shape[1]} columns")
                
                if df.shape[0] < expected_wells:
                    self._log(f"    Note: Partial plate ({df.shape[0]}/{expected_wells} wells)")
                
                all_data.append(df)
                files_processed += 1
                
            except Exception as e:
                self._log(f"    Error reading file: {e}")
                files_skipped += 1
        
        # Check if we have any data
        if not all_data:
            self._log(f"\nNo data found for {file_pattern}")
            return ProcessingResult(
                success=False,
                file=file_pattern,
                reason="No data found"
            )
        
        # Concatenate all dataframes
        self._log(f"\nConcatenating {files_processed} files...")
        concatenated = pd.concat(all_data, ignore_index=True)
        
        # Remove any unnamed columns
        unnamed_cols = [c for c in concatenated.columns if str(c).startswith('Unnamed')]
        if unnamed_cols:
            concatenated = concatenated.drop(columns=unnamed_cols)
        
        # Sort by Plate_number, Replicate, then Well_ID (or Row/Column)
        sort_cols = [COL_PLATE_NUMBER, COL_REPLICATE]
        if COL_WELL_ID in concatenated.columns:
            sort_cols.append(COL_WELL_ID)
        elif COL_ROW in concatenated.columns and COL_COLUMN in concatenated.columns:
            sort_cols.extend([COL_ROW, COL_COLUMN])
        
        concatenated = concatenated.sort_values(by=sort_cols)
        
        # Save to file
        output_filename = f"concatenated_{Path(file_pattern).stem}.csv"
        output_path = os.path.join(output_dir, output_filename)
        concatenated.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        self._log(f"\nSaved to: {output_path}")
        
        return ProcessingResult(
            success=True,
            file=file_pattern,
            output=output_filename,
            rows=concatenated.shape[0],
            columns=concatenated.shape[1],
            plates_processed=files_processed,
            plates_skipped=files_skipped
        )
    
    def _scan_input_directory(
        self, 
        input_dir: str, 
        plates_config: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Scan input directory and build folder to barcode mapping.
        
        Args:
            input_dir: Input directory to scan
            plates_config: Plate configuration from config file
            
        Returns:
            Dictionary mapping folder names to barcodes
        """
        self._log(f"\nScanning input directory: {input_dir}")
        folder_mapping: Dict[str, str] = {}
        
        for item in os.listdir(input_dir):
            item_path = os.path.join(input_dir, item)
            
            if not os.path.isdir(item_path):
                continue
            
            # Skip system/hidden folders
            if should_skip_folder(item):
                self._log(f"  Skipping system folder: {item}")
                continue
            
            # Skip non-plate folders
            if not is_plate_folder(item):
                self._log(f"  Skipping non-plate folder: {item}")
                continue
            
            barcode = extract_barcode(item)
            folder_mapping[item] = barcode
            
            if barcode not in plates_config:
                self._log(f"  Warning: Barcode {barcode} from folder {item} not defined in config")
        
        self._log(f"\nFound {len(folder_mapping)} plate folders")
        return folder_mapping
    
    def process(self, input_dir: str, output_dir: str, config_path: str) -> Dict[str, Any]:
        """
        Main processing function - concatenate all specified file types.
        
        Args:
            input_dir: Input directory containing plate folders
            output_dir: Output directory for concatenated files
            config_path: Path to configuration YAML file
            
        Returns:
            Dictionary with processing results (for JSON serialization)
        """
        # Reset logs for new job
        self._logs = []
        
        # Load configuration
        self._log("Loading configuration...")
        config = load_config(config_path)
        self._log(f"  Plate format: {config['plate_format']}-well")
        self._log(f"  Plates defined: {len(config['plates'])}")
        self._log(f"  Files to process: {config['input_files']}")
        
        # Validate input directory
        if not os.path.isdir(input_dir):
            raise ValueError(f"Input directory does not exist: {input_dir}")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Scan for plate folders
        folder_mapping = self._scan_input_directory(input_dir, config['plates'])
        
        # Process each file type
        results: List[ProcessingResult] = []
        for file_pattern in config['input_files']:
            result = self._process_file_type(
                input_dir, output_dir, file_pattern, config, folder_mapping
            )
            results.append(result)
        
        # Build final result
        successful = sum(1 for r in results if r.success)
        job_result = JobResult(
            files_processed=successful,
            files_failed=len(results) - successful,
            plates_found=len(folder_mapping),
            results=results,
            logs=self._logs
        )
        
        return job_result.to_dict()