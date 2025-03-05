"""
Benchmarking utilities for photometa-restore.

This module provides tools for measuring and analyzing performance metrics.
"""

import time
import psutil
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from PIL import Image
import numpy as np


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    
    start_time: float
    end_time: float
    total_files: int
    processed_files: int
    memory_usage: float
    cpu_usage: float
    processing_rate: float  # files per second
    success_rate: float    # percentage
    operation_type: str    # e.g., "batch_process", "single_file", "template_apply"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "duration_seconds": self.end_time - self.start_time,
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "memory_usage_mb": self.memory_usage,
            "cpu_usage_percent": self.cpu_usage,
            "processing_rate_fps": self.processing_rate,
            "success_rate_percent": self.success_rate,
            "operation_type": self.operation_type,
            "timestamp": datetime.now().isoformat()
        }


class PerformanceMonitor:
    """Monitor and record performance metrics."""
    
    def __init__(self, output_dir: Optional[str] = None):
        """Initialize performance monitor.
        
        Args:
            output_dir: Directory to store benchmark results.
        """
        self.output_dir = Path(output_dir) if output_dir else Path.home() / ".photometa_restore" / "benchmarks"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.process = psutil.Process()
        self.metrics_history: List[Dict[str, Any]] = []
        
    def start_operation(self) -> None:
        """Start monitoring an operation."""
        self.start_time = time.time()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.cpu_times = []
        
    def record_cpu(self) -> None:
        """Record current CPU usage."""
        self.cpu_times.append(self.process.cpu_percent())
        
    def end_operation(
        self,
        total_files: int,
        processed_files: int,
        operation_type: str
    ) -> PerformanceMetrics:
        """End monitoring and calculate metrics.
        
        Args:
            total_files: Total number of files in operation
            processed_files: Number of successfully processed files
            operation_type: Type of operation being monitored
            
        Returns:
            PerformanceMetrics object with calculated metrics
        """
        end_time = time.time()
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        avg_cpu = sum(self.cpu_times) / len(self.cpu_times) if self.cpu_times else 0
        
        duration = end_time - self.start_time
        processing_rate = processed_files / duration if duration > 0 else 0
        success_rate = (processed_files / total_files * 100) if total_files > 0 else 0
        
        metrics = PerformanceMetrics(
            start_time=self.start_time,
            end_time=end_time,
            total_files=total_files,
            processed_files=processed_files,
            memory_usage=final_memory - self.initial_memory,
            cpu_usage=avg_cpu,
            processing_rate=processing_rate,
            success_rate=success_rate,
            operation_type=operation_type
        )
        
        self._save_metrics(metrics)
        return metrics
    
    def _save_metrics(self, metrics: PerformanceMetrics) -> None:
        """Save metrics to file.
        
        Args:
            metrics: PerformanceMetrics object to save
        """
        metrics_dict = metrics.to_dict()
        self.metrics_history.append(metrics_dict)
        
        # Save to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_{metrics.operation_type}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metrics_dict, f, indent=2)
    
    def generate_report(self, operation_type: Optional[str] = None) -> str:
        """Generate a human-readable performance report.
        
        Args:
            operation_type: Optional filter for specific operation type
            
        Returns:
            Formatted report string
        """
        if operation_type:
            relevant_metrics = [m for m in self.metrics_history if m["operation_type"] == operation_type]
        else:
            relevant_metrics = self.metrics_history
        
        if not relevant_metrics:
            return "No metrics available for report generation."
        
        # Calculate averages
        avg_duration = sum(m["duration_seconds"] for m in relevant_metrics) / len(relevant_metrics)
        avg_rate = sum(m["processing_rate_fps"] for m in relevant_metrics) / len(relevant_metrics)
        avg_success = sum(m["success_rate_percent"] for m in relevant_metrics) / len(relevant_metrics)
        avg_memory = sum(m["memory_usage_mb"] for m in relevant_metrics) / len(relevant_metrics)
        avg_cpu = sum(m["cpu_usage_percent"] for m in relevant_metrics) / len(relevant_metrics)
        
        report = [
            "Performance Report",
            "==================",
            f"Operation Type: {operation_type if operation_type else 'All'}",
            f"Number of Operations: {len(relevant_metrics)}",
            "",
            "Average Metrics:",
            f"- Duration: {avg_duration:.2f} seconds",
            f"- Processing Rate: {avg_rate:.2f} files/second",
            f"- Success Rate: {avg_success:.2f}%",
            f"- Memory Usage: {avg_memory:.2f} MB",
            f"- CPU Usage: {avg_cpu:.2f}%",
            "",
            "Individual Operations:",
        ]
        
        # Add individual operation details
        for metrics in relevant_metrics:
            report.extend([
                f"\nTimestamp: {metrics['timestamp']}",
                f"- Duration: {metrics['duration_seconds']:.2f} seconds",
                f"- Files: {metrics['processed_files']}/{metrics['total_files']}",
                f"- Rate: {metrics['processing_rate_fps']:.2f} files/second",
                f"- Success: {metrics['success_rate_percent']:.2f}%"
            ])
        
        return "\n".join(report)


def create_test_dataset(
    base_dir: str,
    num_files: int,
    file_size_kb: int = 100,
    with_metadata: bool = True
) -> str:
    """Create a test dataset for benchmarking.
    
    Args:
        base_dir: Base directory for test files
        num_files: Number of test files to create
        file_size_kb: Size of each test file in KB
        with_metadata: Whether to create corresponding metadata files
        
    Returns:
        Path to the test directory
    """
    test_dir = Path(base_dir) / f"benchmark_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Calculate image dimensions to roughly match desired file size
    # Assuming RGB image (3 channels) and JPEG compression ratio of ~10:1
    target_pixels = (file_size_kb * 1024 * 10) // 3
    img_size = int(np.sqrt(target_pixels))
    
    # Create test files
    for i in range(num_files):
        # Create a random image
        img_array = np.random.randint(0, 256, (img_size, img_size, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        
        # Save image file
        img_path = test_dir / f"test_image_{i}.jpg"
        img.save(img_path, format='JPEG', quality=85)
        
        # Create metadata file if requested
        if with_metadata:
            metadata = {
                "title": f"test_image_{i}.jpg",
                "description": f"Test image {i}",
                "photoTakenTime": {
                    "timestamp": str(int(time.time())),
                    "formatted": datetime.now().isoformat()
                },
                "geoData": {
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                    "altitude": 100.0
                }
            }
            
            # Save metadata with .json extension
            meta_path = test_dir / f"test_image_{i}.jpg.json"
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
    
    return str(test_dir) 