#!/usr/bin/env python3
"""Find all Chinese characters in the codebase"""
import re
from pathlib import Path

def find_chinese_in_file(filepath):
    """Find Chinese characters in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            chinese_lines = []
            for i, line in enumerate(lines, 1):
                if re.search(r'[\u4e00-\u9fff]', line):
                    chinese_lines.append((i, line.rstrip()))
            return chinese_lines
    except Exception as e:
        return None

# Check key files
files_to_check = [
    'ui/project_creation.py',
    'ui/papers.py', 
    'ui/extraction.py',
    'ui/settings.py',
    'ui/analytics.py',
    'core/utils.py',
    'core/citations.py',
    'utils/db.py',
    'utils/extractor.py',
]

print("Scanning for Chinese characters...\n")
total_found = 0

for filepath in files_to_check:
    path = Path(filepath)
    if not path.exists():
        continue
    
    chinese_lines = find_chinese_in_file(filepath)
    if chinese_lines:
        print(f"{'='*60}")
        print(f"File: {filepath}")
        print(f"{'='*60}")
        for line_num, line in chinese_lines[:5]:  # Show first 5
            print(f"Line {line_num}: {line[:100]}")
        if len(chinese_lines) > 5:
            print(f"... and {len(chinese_lines) - 5} more lines")
        print()
        total_found += len(chinese_lines)

print(f"\nTotal: Found Chinese in {total_found} lines across checked files")
