"""
Command-line interface for PhotoMeta Restore.

This module provides a command-line interface for PhotoMeta Restore.
"""

import os
import sys
import argparse
from typing import Optional, List
import click
from tqdm import tqdm

from .config import get_config
from .processor import process_directory, MediaProcessor
from .utils.benchmarking import PerformanceMonitor, create_test_dataset


def cli_progress_callback(progress: float, success_count: int, error_count: int) -> None:
    """Update progress in the console.
    
    Args:
        progress: Progress percentage (0-100).
        success_count: Number of successfully processed files.
        error_count: Number of files with errors.
    """
    # Print progress as a percentage
    sys.stdout.write(f"\rProgress: {progress:.2f}% (Success: {success_count}, Errors: {error_count})")
    sys.stdout.flush()


def show_progress(progress: float, success: int, total: int):
    """Show progress bar for batch processing."""
    with tqdm(total=total) as pbar:
        pbar.update(int(progress * total))
        pbar.set_description(f"Processed: {success}/{total}")


@click.group()
def cli():
    """PhotoMeta Restore - Restore metadata to your photos."""
    pass


@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--edited-suffix', '-e', help='Suffix for edited files')
def process(directory: str, edited_suffix: str):
    """Process a directory to restore metadata."""
    success, errors = process_directory(
        directory,
        edited_suffix=edited_suffix,
        progress_callback=show_progress
    )
    click.echo(f"Processing complete. Success: {success}, Errors: {errors}")


@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.argument('files', nargs=-1, type=click.Path(exists=True))
@click.option('--edited-suffix', '-e', help='Suffix for edited files')
def batch(directory: str, files: List[str], edited_suffix: str):
    """Process a batch of files with automatic backup."""
    processor = MediaProcessor(directory, edited_suffix)
    results = processor.process_batch(list(files), progress_callback=lambda p: show_progress(p, 0, len(files)))
    
    click.echo("\nBatch processing complete:")
    click.echo(f"Successful: {len(results['successful'])}")
    click.echo(f"Failed: {len(results['failed'])}")
    click.echo(f"Backups created: {len(results['backups'])}")
    
    if results['failed']:
        click.echo("\nFailed files:")
        for failure in results['failed']:
            if isinstance(failure, tuple):
                click.echo(f"  {failure[0]}: {failure[1]}")
            else:
                click.echo(f"  {failure}")


@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.argument('template_name', type=str)
@click.argument('files', nargs=-1, type=click.Path(exists=True))
def apply_template(directory: str, template_name: str, files: List[str]):
    """Apply a metadata template to files."""
    processor = MediaProcessor(directory)
    success = 0
    
    with tqdm(total=len(files)) as pbar:
        for file in files:
            if processor.apply_template(file, template_name):
                success += 1
            pbar.update(1)
    
    click.echo(f"\nTemplate application complete. Success: {success}, Failed: {len(files) - success}")


@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.argument('template_name', type=str)
@click.argument('metadata_file', type=click.Path(exists=True))
def save_template(directory: str, template_name: str, metadata_file: str):
    """Save a metadata file as a template."""
    processor = MediaProcessor(directory)
    try:
        with open(metadata_file, 'r') as f:
            metadata = f.read()
        processor.template_handler.save_template(template_name, metadata)
        click.echo(f"Template '{template_name}' saved successfully.")
    except Exception as e:
        click.echo(f"Error saving template: {str(e)}", err=True)


@cli.command()
@click.argument('directory', type=click.Path(exists=True))
def list_templates(directory: str):
    """List available metadata templates."""
    processor = MediaProcessor(directory)
    templates = processor.template_handler.list_templates()
    
    if templates:
        click.echo("Available templates:")
        for template in templates:
            click.echo(f"  - {template}")
    else:
        click.echo("No templates found.")


@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.argument('file', type=click.Path(exists=True))
def backup(directory: str, file: str):
    """Create a backup of file metadata."""
    processor = MediaProcessor(directory)
    backup_path = processor.backup_metadata(file)
    
    if backup_path:
        click.echo(f"Backup created successfully: {backup_path}")
    else:
        click.echo("Failed to create backup.", err=True)


@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.argument('backup_file', type=click.Path(exists=True))
def restore(directory: str, backup_file: str):
    """Restore metadata from a backup file."""
    processor = MediaProcessor(directory)
    if processor.restore_from_backup(backup_file):
        click.echo("Metadata restored successfully.")
    else:
        click.echo("Failed to restore metadata.", err=True)


@cli.group()
def benchmark():
    """Benchmark commands for performance testing."""
    pass


@benchmark.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--num-files', '-n', type=int, default=100, help='Number of test files to create')
@click.option('--file-size', '-s', type=int, default=100, help='Size of each file in KB')
@click.option('--with-metadata/--no-metadata', default=True, help='Create metadata files')
def create_dataset(directory: str, num_files: int, file_size: int, with_metadata: bool):
    """Create a test dataset for benchmarking."""
    test_dir = create_test_dataset(directory, num_files, file_size, with_metadata)
    click.echo(f"Created test dataset at: {test_dir}")
    click.echo(f"Number of files: {num_files}")
    click.echo(f"File size: {file_size}KB")
    click.echo(f"Metadata files: {'Yes' if with_metadata else 'No'}")


@benchmark.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--operation', '-o', type=click.Choice(['batch', 'single', 'template']), default='batch')
@click.option('--iterations', '-i', type=int, default=1, help='Number of test iterations')
def run(directory: str, operation: str, iterations: int):
    """Run performance benchmarks."""
    monitor = PerformanceMonitor()
    
    for i in range(iterations):
        click.echo(f"\nRunning iteration {i+1}/{iterations}...")
        
        # Start monitoring
        monitor.start_operation()
        
        # Get list of files
        json_files = [f for f in os.listdir(directory) if f.endswith('.json')]
        total_files = len(json_files)
        
        if total_files == 0:
            click.echo("No JSON files found in directory.")
            return
        
        processor = MediaProcessor(directory)
        success_count = 0
        
        with tqdm(total=total_files) as pbar:
            if operation == 'batch':
                # Batch processing
                results = processor.process_batch(
                    [os.path.join(directory, f) for f in json_files],
                    progress_callback=lambda p: pbar.update(1)
                )
                success_count = len(results['successful'])
            
            elif operation == 'single':
                # Single file processing
                for json_file in json_files:
                    if processor.process_json_file(os.path.join(directory, json_file)):
                        success_count += 1
                    pbar.update(1)
            
            elif operation == 'template':
                # Template processing
                template_name = "benchmark_template"
                processor.template_handler.save_template(template_name, {
                    "description": "Benchmark template",
                    "photoTakenTime": {
                        "timestamp": "1614729600",
                        "formatted": "March 3, 2021 12:00:00 PM UTC"
                    },
                    "geoData": {
                        "latitude": 48.8566,
                        "longitude": 2.3522,
                        "altitude": 75.0
                    }
                })
                
                for json_file in json_files:
                    if processor.apply_template(os.path.join(directory, json_file), template_name):
                        success_count += 1
                    pbar.update(1)
        
        # Record metrics
        monitor.end_operation(total_files, success_count, f"{operation}_process")
    
    # Generate and display report
    click.echo("\n" + monitor.generate_report(f"{operation}_process"))


@benchmark.command()
@click.option('--operation', '-o', type=str, help='Filter by operation type')
def report(operation: Optional[str]):
    """Display benchmark reports."""
    monitor = PerformanceMonitor()
    click.echo(monitor.generate_report(operation))


if __name__ == '__main__':
    cli() 