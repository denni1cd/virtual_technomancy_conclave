 #!/usr/bin/env python3
"""
Repository cleanup utility for Conclave.

Removes generated auth/billing modules and other temporary files
that shouldn't be tracked in version control.
"""

import shutil
import os
from pathlib import Path
from typing import List, Set


def get_generated_directories() -> Set[Path]:
    """Get all generated directories that should be cleaned up."""
    patterns = [
        "auth_module_*",
        "billing_api_*", 
        "reporting_dashboard_*",
        "user_profile_*"
    ]
    
    generated_dirs = set()
    for pattern in patterns:
        for path in Path(".").glob(pattern):
            if path.is_dir():
                generated_dirs.add(path)
    
    return generated_dirs


def get_temp_files() -> Set[Path]:
    """Get temporary files that should be cleaned up."""
    temp_files = set()
    
    # Usage logs
    usage_log = Path("conclave_usage.jsonl")
    if usage_log.exists():
        temp_files.add(usage_log)
    
    # Failed milestone archives
    failed_dir = Path("failed")
    if failed_dir.exists():
        temp_files.add(failed_dir)
    
    # Python cache
    for cache_dir in Path(".").rglob("__pycache__"):
        if cache_dir.is_dir():
            temp_files.add(cache_dir)
    
    # Test cache
    pytest_cache = Path(".pytest_cache")
    if pytest_cache.exists():
        temp_files.add(pytest_cache)
    
    return temp_files


def cleanup_directories(directories: Set[Path], dry_run: bool = False) -> None:
    """Remove directories."""
    for directory in sorted(directories):
        if dry_run:
            print(f"[DRY RUN] Would remove directory: {directory}")
        else:
            try:
                shutil.rmtree(directory)
                print(f"✓ Removed directory: {directory}")
            except Exception as e:
                print(f"✗ Failed to remove {directory}: {e}")


def cleanup_files(files: Set[Path], dry_run: bool = False) -> None:
    """Remove files."""
    for file_path in sorted(files):
        if dry_run:
            print(f"[DRY RUN] Would remove file: {file_path}")
        else:
            try:
                if file_path.is_dir():
                    shutil.rmtree(file_path)
                else:
                    file_path.unlink()
                print(f"✓ Removed: {file_path}")
            except Exception as e:
                print(f"✗ Failed to remove {file_path}: {e}")


def main():
    """Main cleanup function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Clean up generated files and directories from Conclave repository"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be removed without actually removing anything"
    )
    parser.add_argument(
        "--force",
        action="store_true", 
        help="Skip confirmation prompt"
    )
    
    args = parser.parse_args()
    
    print("🧹 Conclave Repository Cleanup")
    print("=" * 40)
    
    # Find items to clean up
    generated_dirs = get_generated_directories()
    temp_files = get_temp_files()
    
    if not generated_dirs and not temp_files:
        print("✓ Repository is already clean!")
        return
    
    # Show what will be cleaned up
    print("\nGenerated directories to remove:")
    for directory in sorted(generated_dirs):
        print(f"  - {directory}")
    
    print("\nTemporary files to remove:")
    for file_path in sorted(temp_files):
        print(f"  - {file_path}")
    
    # Confirm unless --force is used
    if not args.force and not args.dry_run:
        response = input(f"\nRemove {len(generated_dirs)} directories and {len(temp_files)} files? (y/N): ")
        if response.lower() != 'y':
            print("Cleanup cancelled.")
            return
    
    # Perform cleanup
    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Cleaning up...")
    
    cleanup_directories(generated_dirs, dry_run=args.dry_run)
    cleanup_files(temp_files, dry_run=args.dry_run)
    
    if args.dry_run:
        print(f"\n[DRY RUN] Would have removed {len(generated_dirs)} directories and {len(temp_files)} files")
    else:
        print(f"\n✓ Cleanup complete! Removed {len(generated_dirs)} directories and {len(temp_files)} files")


if __name__ == "__main__":
    main() 