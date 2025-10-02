from django.db import models
from django.core.files.storage import default_storage
import re
import time

from projects.models import Project


class Paper(models.Model):
    CITE_FORMAT_CHOICES = [
        ('bibtex', 'BibTeX'),
        ('ris', 'RIS'),
        ('endnote', 'EndNote'),
        ('other', 'Other'),
    ]
    
    paper_id = models.CharField(max_length=255, primary_key=True)
    project = models.ForeignKey(Project, related_name="papers", on_delete=models.SET_NULL, blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    citation = models.TextField(blank=True, null=True)
    citation_format = models.CharField(max_length=64, blank=True, null=True)
    
    # New fields for enhanced citation management
    citation_key = models.CharField(max_length=255, db_index=True, blank=True, null=True, 
                                    help_text="Citation key extracted from BibTeX or custom")
    bibtex_content = models.TextField(blank=True, null=True, help_text="Full BibTeX entry")
    cite_format = models.CharField(max_length=20, choices=CITE_FORMAT_CHOICES, default='bibtex')
    
    # Authors and metadata
    authors = models.TextField(blank=True, null=True, help_text="Comma-separated authors")
    year = models.IntegerField(blank=True, null=True)
    journal = models.CharField(max_length=500, blank=True, null=True)
    doi = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    
    # PDF management
    pdf_sha256 = models.CharField(max_length=128, blank=True, null=True)
    pdf_path = models.TextField(blank=True, null=True)
    pdf_file = models.FileField(upload_to='papers/pdfs/', blank=True, null=True)
    
    # Timestamps
    created_at = models.BigIntegerField(blank=True, null=True)
    updated_at = models.BigIntegerField(blank=True, null=True)

    class Meta:
        db_table = "papers"
        ordering = ["-updated_at", "paper_id"]
        indexes = [
            models.Index(fields=['citation_key']),
            models.Index(fields=['title']),
            models.Index(fields=['year']),
        ]

    def __str__(self) -> str:
        return self.citation_key or self.paper_id
    
    def save(self, *args, **kwargs):
        # Auto-update timestamps
        current_time = int(time.time())
        if not self.created_at:
            self.created_at = current_time
        self.updated_at = current_time
        
        # Extract citation key from BibTeX if not provided
        if self.bibtex_content and not self.citation_key:
            self.citation_key = self.extract_citation_key_from_bibtex()
        
        # Parse BibTeX to extract metadata
        if self.bibtex_content and self.cite_format == 'bibtex':
            self.parse_bibtex_metadata()
        
        super().save(*args, **kwargs)
    
    def extract_citation_key_from_bibtex(self):
        """Extract citation key from BibTeX entry"""
        if not self.bibtex_content:
            return None
        
        # Match @article{key, or @book{key, etc.
        match = re.search(r'@\w+\{([^,\s]+)', self.bibtex_content)
        if match:
            return match.group(1)
        return None
    
    def parse_bibtex_metadata(self):
        """Parse BibTeX content to extract metadata"""
        if not self.bibtex_content:
            return
        
        content = self.bibtex_content
        
        # Extract title
        title_match = re.search(r'title\s*=\s*[{"](.+?)[}"]', content, re.IGNORECASE | re.DOTALL)
        if title_match and not self.title:
            self.title = title_match.group(1).strip()
        
        # Extract authors
        author_match = re.search(r'author\s*=\s*[{"](.+?)[}"]', content, re.IGNORECASE | re.DOTALL)
        if author_match:
            self.authors = author_match.group(1).strip()
        
        # Extract year
        year_match = re.search(r'year\s*=\s*[{"]?(\d{4})[}"]?', content, re.IGNORECASE)
        if year_match:
            self.year = int(year_match.group(1))
        
        # Extract journal
        journal_match = re.search(r'journal\s*=\s*[{"](.+?)[}"]', content, re.IGNORECASE | re.DOTALL)
        if journal_match:
            self.journal = journal_match.group(1).strip()
        
        # Extract DOI
        doi_match = re.search(r'doi\s*=\s*[{"](.+?)[}"]', content, re.IGNORECASE)
        if doi_match:
            self.doi = doi_match.group(1).strip()
    
    def update_citation_key(self, new_key):
        """Update citation key in BibTeX content"""
        if self.bibtex_content and self.citation_key:
            # Replace old key with new key in BibTeX
            old_pattern = r'(@\w+\{)' + re.escape(self.citation_key)
            self.bibtex_content = re.sub(old_pattern, r'\1' + new_key, self.bibtex_content)
        self.citation_key = new_key
        self.save()
    
    @property
    def display_title(self):
        """Get display title with fallback"""
        return self.title or self.citation_key or self.paper_id or "Untitled"
    
    @property 
    def display_authors(self):
        """Get formatted authors for display"""
        if not self.authors:
            return "Unknown"
        # Simplify author display (first author et al.)
        authors_list = [a.strip() for a in self.authors.split(' and ')]
        if len(authors_list) > 3:
            return f"{authors_list[0]} et al."
        return ", ".join(authors_list[:3])
