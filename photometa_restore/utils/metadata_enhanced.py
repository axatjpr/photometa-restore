"""
Enhanced metadata handling utilities for photometa-restore.

This module provides advanced metadata functionality including:
- Metadata backup and restoration
- Batch processing utilities
- Metadata templates
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Callable
from pathlib import Path


class MetadataBackup:
    """Handles metadata backup and restoration operations."""
    
    def __init__(self, base_path: str):
        """Initialize metadata backup handler.
        
        Args:
            base_path: Base directory for storing backups
        """
        self.base_path = Path(base_path)
        self.backup_dir = self.base_path / "metadata_backups"
        self._ensure_backup_dir()
    
    def _ensure_backup_dir(self):
        """Ensure backup directory exists."""
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, file_path: str, metadata: Dict[str, Any]) -> str:
        """Create a backup of file metadata.
        
        Args:
            file_path: Path to the original file
            metadata: Metadata to backup
            
        Returns:
            Path to the backup file
        """
        file_path = Path(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}.json"
        backup_path = self.backup_dir / backup_name
        
        backup_data = {
            "original_file": str(file_path),
            "backup_date": timestamp,
            "metadata": metadata
        }
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2)
            
        return str(backup_path)
    
    def restore_from_backup(self, backup_path: str) -> Tuple[str, Dict[str, Any]]:
        """Restore metadata from a backup file.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            Tuple of (original file path, metadata)
        """
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        return backup_data["original_file"], backup_data["metadata"]


class MetadataTemplate:
    """Handles metadata templates for consistent metadata application."""
    
    def __init__(self, templates_dir: Optional[str] = None):
        """Initialize metadata template handler.
        
        Args:
            templates_dir: Directory for storing templates
        """
        self.templates_dir = Path(templates_dir) if templates_dir else Path.home() / ".photometa_restore" / "templates"
        self._ensure_templates_dir()
    
    def _ensure_templates_dir(self):
        """Ensure templates directory exists."""
        os.makedirs(self.templates_dir, exist_ok=True)
    
    def save_template(self, name: str, template: Dict[str, Any]):
        """Save a metadata template.
        
        Args:
            name: Template name
            template: Template metadata
        """
        template_path = self.templates_dir / f"{name}.json"
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2)
    
    def load_template(self, name: str) -> Dict[str, Any]:
        """Load a metadata template.
        
        Args:
            name: Template name
            
        Returns:
            Template metadata
        """
        template_path = self.templates_dir / f"{name}.json"
        with open(template_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_templates(self) -> List[str]:
        """List available templates.
        
        Returns:
            List of template names
        """
        return [f.stem for f in self.templates_dir.glob("*.json")]


class BatchProcessor:
    """Handles batch processing of metadata operations."""
    
    def __init__(self, processor, chunk_size: int = 10):
        """Initialize batch processor.
        
        Args:
            processor: MediaProcessor instance
            chunk_size: Number of files to process in each batch
        """
        self.processor = processor
        self.chunk_size = chunk_size
        self.backup_handler = MetadataBackup(processor.base_path)
    
    def process_batch(self, files: List[str], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Process a batch of files.
        
        Args:
            files: List of files to process
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with processing results
        """
        results = {
            "successful": [],
            "failed": [],
            "backups": []
        }
        
        total_files = len(files)
        
        for i, file_path in enumerate(files):
            try:
                # Create backup before processing
                if file_path.endswith('.json'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    backup_path = self.backup_handler.create_backup(file_path, metadata)
                    results["backups"].append(backup_path)
                
                # Process the file
                success = self.processor.process_json_file(file_path)
                
                if success:
                    results["successful"].append(file_path)
                else:
                    results["failed"].append(file_path)
                
                if progress_callback:
                    progress_callback((i + 1) / total_files)
                    
            except Exception as e:
                results["failed"].append((file_path, str(e)))
        
        return results 