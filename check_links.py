#!/usr/bin/env python3
"""Check for broken internal links in markdown files."""

import os
import re
from pathlib import Path
from typing import Set, Dict, List, Tuple

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

def extract_links(content: str, file_path: Path) -> List[Tuple[str, int]]:
    """Extract markdown links from content with line numbers."""
    links = []
    # Match [text](link) style links
    pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    
    for line_num, line in enumerate(content.split('\n'), 1):
        for match in re.finditer(pattern, line):
            link = match.group(2)
            # Only check internal links (not http/https/mailto)
            if not link.startswith(('http://', 'https://', 'mailto:', '#')):
                links.append((link, line_num))
    
    return links

def resolve_link(link: str, source_file: Path) -> Path:
    """Resolve a relative link from a source file."""
    # Remove anchor fragments
    link = link.split('#')[0]
    if not link:  # Pure anchor link
        return source_file
    
    # Resolve relative to source file's directory
    source_dir = source_file.parent
    target = (source_dir / link).resolve()
    return target

def check_links() -> Dict[str, List[Tuple[str, int, str]]]:
    """Check all markdown files for broken links."""
    broken_links = {}
    md_files = find_markdown_files()
    
    print(f"Found {len(md_files)} markdown files")
    print("Checking for broken links...\n")
    
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {md_file}: {e}")
            continue
        
        links = extract_links(content, md_file)
        file_broken_links = []
        
        for link, line_num in links:
            target = resolve_link(link, md_file)
            
            if not target.exists():
                file_broken_links.append((link, line_num, str(target)))
        
        if file_broken_links:
            broken_links[str(md_file)] = file_broken_links
    
    return broken_links

def main():
    broken_links = check_links()
    
    if not broken_links:
        print("✅ No broken internal links found!")
        return 0
    
    print(f"❌ Found broken links in {len(broken_links)} files:\n")
    
    for file_path, links in sorted(broken_links.items()):
        print(f"\n{file_path}:")
        for link, line_num, target in links:
            print(f"  Line {line_num}: {link}")
            print(f"    → Resolves to: {target} (NOT FOUND)")
    
    print(f"\n\nTotal: {sum(len(links) for links in broken_links.values())} broken links")
    return 1

if __name__ == "__main__":
    exit(main())
