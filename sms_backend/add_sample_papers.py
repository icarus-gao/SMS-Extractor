"""
Test script to add sample papers to the Paper Library
Run this to populate your library with example papers
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, '/Users/gaoxiangyu/Desktop/sms_extractor/sms_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sms_backend.settings')
django.setup()

from papers.models import Paper
from projects.models import Project

# Sample BibTeX entries
sample_papers = [
    {
        'paper_id': 'smith2023machine',
        'bibtex': '''@article{smith2023machine,
  title={Machine Learning Applications in Healthcare: A Comprehensive Review},
  author={Smith, John and Doe, Jane and Johnson, Michael},
  journal={Journal of Medical Informatics},
  year={2023},
  volume={45},
  number={3},
  pages={123--145},
  doi={10.1234/jmi.2023.001}
}'''
    },
    {
        'paper_id': 'zhang2024deep',
        'bibtex': '''@article{zhang2024deep,
  title={Deep Learning for Medical Image Analysis: Recent Advances and Future Directions},
  author={Zhang, Wei and Liu, Li and Chen, Ming},
  journal={IEEE Transactions on Medical Imaging},
  year={2024},
  volume={43},
  number={1},
  pages={45--78},
  doi={10.1109/TMI.2024.001}
}'''
    },
    {
        'paper_id': 'garcia2023systematic',
        'bibtex': '''@article{garcia2023systematic,
  title={A Systematic Review of Natural Language Processing in Clinical Decision Support},
  author={Garcia, Maria and Rodriguez, Carlos and Martinez, Ana},
  journal={Artificial Intelligence in Medicine},
  year={2023},
  volume={137},
  pages={102501},
  doi={10.1016/j.artmed.2023.102501}
}'''
    },
    {
        'paper_id': 'brown2022extracting',
        'bibtex': '''@inproceedings{brown2022extracting,
  title={Extracting Medical Information from Clinical Notes Using Transformers},
  author={Brown, Sarah and Wilson, David and Taylor, Emma},
  booktitle={Proceedings of the 2022 Conference on Empirical Methods in Natural Language Processing},
  pages={1234--1245},
  year={2022},
  doi={10.18653/v1/2022.emnlp-main.123}
}'''
    },
    {
        'paper_id': 'kim2024automated',
        'bibtex': '''@article{kim2024automated,
  title={Automated Feature Extraction for Systematic Reviews: A Meta-Analysis},
  author={Kim, Soo-Jin and Park, Ji-Hoon and Lee, Min-Ji},
  journal={BMC Medical Research Methodology},
  year={2024},
  volume={24},
  number={1},
  pages={1--15},
  doi={10.1186/s12874-024-01234-5}
}'''
    }
]

def create_sample_papers():
    """Create sample papers in the database"""
    
    print("Creating sample papers in Paper Library...\n")
    
    created_count = 0
    updated_count = 0
    
    for paper_data in sample_papers:
        paper, created = Paper.objects.update_or_create(
            paper_id=paper_data['paper_id'],
            defaults={
                'bibtex_content': paper_data['bibtex'],
                'cite_format': 'bibtex'
            }
        )
        
        if created:
            created_count += 1
            print(f"✓ Created: {paper.citation_key} - {paper.display_title[:60]}...")
        else:
            updated_count += 1
            print(f"↻ Updated: {paper.citation_key} - {paper.display_title[:60]}...")
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Created: {created_count} papers")
    print(f"  Updated: {updated_count} papers")
    print(f"  Total:   {Paper.objects.count()} papers in library")
    print(f"{'='*60}\n")
    
    print("✓ Sample papers added successfully!")
    print("\nVisit: http://127.0.0.1:8000/papers/ to view your Paper Library")

if __name__ == '__main__':
    create_sample_papers()
