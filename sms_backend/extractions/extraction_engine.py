"""
Mock AI Extraction Engine
This is a placeholder that generates sample extracted data based on schema fields.
In production, this would be replaced with actual AI/LLM integration.
"""

import random
import json
from typing import Dict, List, Any


def mock_extract_data(paper, schema) -> Dict[str, Any]:
    """
    Mock function to extract data from a paper using a schema.
    Generates random sample data based on schema field types.
    
    Args:
        paper: Paper model instance
        schema: Schema model instance
    
    Returns:
        Dictionary with extracted data in the format:
        {
            'fields': {
                'field_id': {
                    'value': '...',
                    'confidence': 0.95,
                    'source': 'AI',
                    'notes': ''
                },
                ...
            },
            'metadata': {
                'extraction_time': '2025-10-02T12:00:00',
                'model': 'mock-gpt-4',
                'paper_id': '...',
                'schema_id': '...'
            }
        }
    """
    from datetime import datetime
    
    fields = schema.get_fields()
    extracted_fields = {}
    
    # Sample data generators based on field type
    sample_data = {
        'text': [
            'Machine learning algorithm for classification',
            'Deep neural network with attention mechanism',
            'Supervised learning approach',
            'Random forest classifier',
            'Support vector machine'
        ],
        'number': lambda: round(random.uniform(0.5, 0.99), 2),
        'select': ['Option A', 'Option B', 'Option C', 'Yes', 'No'],
        'multiselect': [
            ['Method 1', 'Method 2'],
            ['Technique A', 'Technique B', 'Technique C'],
            ['Approach 1'],
        ],
        'boolean': [True, False],
        'date': ['2023-01-15', '2024-03-20', '2025-10-02'],
    }
    
    for field in fields:
        field_id = field.get('field_id')
        field_type = field.get('type', 'text')
        field_name = field.get('name', 'Unknown Field')
        
        # Generate mock value based on field type
        if field_type == 'text' or field_type == 'textarea':
            value = random.choice(sample_data['text'])
        elif field_type == 'number':
            value = sample_data['number']()
        elif field_type == 'select':
            options = field.get('options', sample_data['select'])
            value = random.choice(options)
        elif field_type == 'multiselect':
            options = field.get('options', ['Option 1', 'Option 2', 'Option 3'])
            num_selected = random.randint(1, min(3, len(options)))
            value = random.sample(options, num_selected)
        elif field_type == 'boolean':
            value = random.choice(sample_data['boolean'])
        elif field_type == 'date':
            value = random.choice(sample_data['date'])
        else:
            value = f"Sample value for {field_name}"
        
        # Generate confidence score (AI extractions have varying confidence)
        confidence = round(random.uniform(0.70, 0.99), 2)
        
        extracted_fields[field_id] = {
            'value': value,
            'confidence': confidence,
            'source': 'AI (Mock)',
            'notes': f'Automatically extracted from paper {paper.paper_id}'
        }
    
    result = {
        'fields': extracted_fields,
        'metadata': {
            'extraction_time': datetime.now().isoformat(),
            'model': 'mock-gpt-4-turbo',
            'paper_id': paper.paper_id,
            'paper_title': paper.title or 'N/A',
            'schema_id': schema.schema_id,
            'schema_name': schema.name,
            'field_count': len(fields)
        }
    }
    
    return result


def manual_extract_data(schema) -> Dict[str, Any]:
    """
    Generate empty structure for manual data entry.
    
    Args:
        schema: Schema model instance
    
    Returns:
        Dictionary with empty fields ready for manual input
    """
    from datetime import datetime
    
    fields = schema.get_fields()
    extracted_fields = {}
    
    for field in fields:
        field_id = field.get('field_id')
        field_type = field.get('type', 'text')
        
        # Provide default values based on type
        if field_type == 'boolean':
            default_value = False
        elif field_type == 'multiselect':
            default_value = []
        elif field_type == 'number':
            default_value = 0
        else:
            default_value = ''
        
        extracted_fields[field_id] = {
            'value': default_value,
            'confidence': 1.0,  # Manual entries are 100% confident
            'source': 'Manual',
            'notes': ''
        }
    
    result = {
        'fields': extracted_fields,
        'metadata': {
            'extraction_time': datetime.now().isoformat(),
            'model': 'manual-entry',
            'schema_id': schema.schema_id,
            'schema_name': schema.name,
            'field_count': len(fields)
        }
    }
    
    return result
