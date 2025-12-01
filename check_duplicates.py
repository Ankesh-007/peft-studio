#!/usr/bin/env python3
"""Check for duplicate documentation content."""

import os
import re
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

def find_markdown_files(root_dir: str = ".") -> List[Path]:
    """Find all markdown files in the repository."""
    md_files = []
    for root, dirs, files in os.walk(root_dir):
        # Skip node_modules, .git, and other non-documentation directories
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', 'dist', 'build', '.hypothesis', '.pytest_cache', '__pycache__']]
        
        for file in files:
            if file.endswith('.md'):
                md_files.append(Path(root) / file)
    return md_files

def extract_title(content: str) -> str:
    """Extract the main title from markdown content."""
    lines = content.split('\n')
    for line in lines:
        if line.startswith('# '):
            return line[2:].strip()
    return ""

def normalize_title(title: str) -> str:
    """Normalize title for comparison."""
    # Remove common suffixes/prefixes
    title = re.sub(r'\s+(Implementation|Summary|Guide|Documentation|Complete|API|Service)$', '', title, flags=re.IGNORECASE)
    title = title.lower().strip()
    return title

def check_duplicates():
    """Check for duplicate documentation."""
    md_files = find_markdown_files()
    
    # Group by normalized title
    title_groups = defaultdict(list)
    
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            continue
        
        title = extract_title(content)
        if title:
            normalized = normalize_title(title)
            if normalized:  # Only track non-empty titles
                title_groups[normalized].append((str(md_file), title))
    
    # Find duplicates
    duplicates = {k: v for k, v in title_groups.items() if len(v) > 1}
    
    return duplicates

def main():
    duplicates = check_duplicates()
    
    if not duplicates:
        print("✅ No duplicate documentation titles found!")
        return 0
    
    print(f"⚠️  Found {len(duplicates)} sets of potentially duplicate documentation:\n")
    
    for normalized_title, files in sorted(duplicates.items()):
        print(f"\nNormalized title: '{normalized_title}'")
        print(f"Found in {len(files)} files:")
        for file_path, original_title in files:
            print(f"  - {file_path}")
            print(f"    Title: {original_title}")
    
    print(f"\n\nNote: These may be legitimate separate documents. Manual review recommended.")
    return 0

if __name__ == "__main__":
    exit(main())
