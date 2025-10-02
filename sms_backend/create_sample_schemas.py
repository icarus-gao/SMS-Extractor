"""创建示例 Schema 的脚本"""

import os
import django
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sms_backend.settings')
django.setup()

from projects.models import Schema

# ML Methods Comparison Schema
ml_methods_schema = {
    "schema_meta": {
        "name": "ML Methods Comparison",
        "description": "Compare machine learning methods for Related Work section",
        "category": "Machine Learning",
        "version": "1.0",
    },
    "export_config": {
        "default_format": "excel",
        "include_metadata": True,
        "include_confidence": False,
    },
    "fields": [
        {
            "field_id": "paper_id",
            "order": 1,
            "name": "Paper ID",
            "type": "auto",
            "description": "Automatically filled from paper ID",
            "required": True,
            "system_field": True,
            "export": {
                "enabled": True,
                "column_name": "Paper ID",
                "width": 80,
                "align": "left"
            }
        },
        {
            "field_id": "citation_key",
            "order": 2,
            "name": "Citation",
            "type": "auto",
            "description": "Automatically filled from citation key",
            "required": True,
            "system_field": True,
            "export": {
                "enabled": True,
                "column_name": "Citation",
                "width": 120,
                "align": "left"
            }
        },
        {
            "field_id": "method_name",
            "order": 3,
            "name": "Method Name",
            "name_zh": "方法名称",
            "type": "text",
            "description": "Name of the ML method or model",
            "placeholder": "e.g., CNN, LSTM, ResNet-50",
            "required": True,
            "validation": {
                "max_length": 100,
            },
            "extraction": {
                "mode": "ai",
                "allow_manual": True,
                "prompt": "What is the name of the machine learning method or model used in this paper? Provide the specific name (e.g., CNN, LSTM, ResNet).",
                "strategy": "semantic_search",
                "confidence_threshold": 0.7,
            },
            "export": {
                "enabled": True,
                "column_name": "Method",
                "width": 150,
                "align": "left",
            }
        },
        {
            "field_id": "dataset",
            "order": 4,
            "name": "Dataset",
            "name_zh": "数据集",
            "type": "text",
            "description": "Dataset used for training or evaluation",
            "placeholder": "e.g., MNIST, ImageNet, COCO",
            "required": True,
            "validation": {
                "max_length": 200,
            },
            "extraction": {
                "mode": "ai",
                "allow_manual": True,
                "prompt": "What dataset is used for training or evaluation in this paper?",
                "strategy": "semantic_search",
                "confidence_threshold": 0.7,
            },
            "export": {
                "enabled": True,
                "column_name": "Dataset",
                "width": 120,
                "align": "left",
            }
        },
        {
            "field_id": "accuracy",
            "order": 5,
            "name": "Accuracy",
            "name_zh": "准确率",
            "type": "number",
            "description": "Model accuracy (percentage)",
            "placeholder": "e.g., 98.5",
            "required": False,
            "validation": {
                "min": 0,
                "max": 100,
                "decimal_places": 2,
            },
            "unit": "%",
            "extraction": {
                "mode": "ai",
                "allow_manual": True,
                "prompt": "What is the accuracy of the model? Provide a number (percentage).",
                "strategy": "table_and_text",
                "confidence_threshold": 0.6,
            },
            "export": {
                "enabled": True,
                "column_name": "Accuracy (%)",
                "width": 100,
                "align": "right",
                "format": "0.00",
            }
        },
        {
            "field_id": "model_type",
            "order": 6,
            "name": "Model Type",
            "name_zh": "模型类型",
            "type": "select",
            "description": "Type of ML model",
            "required": True,
            "options": [
                {"value": "cnn", "label": "CNN"},
                {"value": "rnn", "label": "RNN"},
                {"value": "lstm", "label": "LSTM"},
                {"value": "transformer", "label": "Transformer"},
                {"value": "gan", "label": "GAN"},
                {"value": "other", "label": "Other"},
            ],
            "extraction": {
                "mode": "ai",
                "allow_manual": True,
                "prompt": "What type of model is used? Choose from: CNN, RNN, LSTM, Transformer, GAN, or Other.",
                "strategy": "classification",
                "confidence_threshold": 0.8,
            },
            "export": {
                "enabled": True,
                "column_name": "Model Type",
                "width": 120,
                "align": "left",
            }
        },
        {
            "field_id": "year",
            "order": 7,
            "name": "Year",
            "name_zh": "年份",
            "type": "year",
            "description": "Publication year",
            "required": False,
            "validation": {
                "min": 2000,
                "max": 2030,
            },
            "extraction": {
                "mode": "ai",
                "allow_manual": True,
                "prompt": "What year was this paper published?",
                "confidence_threshold": 0.9,
            },
            "export": {
                "enabled": True,
                "column_name": "Year",
                "width": 80,
                "align": "center",
            }
        },
        {
            "field_id": "strengths",
            "order": 8,
            "name": "Strengths",
            "name_zh": "优势",
            "type": "long-text",
            "description": "Main strengths of the method",
            "placeholder": "Summarize in 2-3 sentences",
            "required": False,
            "validation": {
                "max_length": 1000,
            },
            "extraction": {
                "mode": "ai",
                "allow_manual": True,
                "prompt": "What are the main strengths or advantages of this method? Summarize in 2-3 sentences.",
                "confidence_threshold": 0.7,
            },
            "export": {
                "enabled": True,
                "column_name": "Strengths",
                "width": 300,
                "align": "left",
                "format": "wrap_text",
            }
        },
        {
            "field_id": "notes",
            "order": 9,
            "name": "Notes",
            "name_zh": "备注",
            "type": "long-text",
            "description": "Additional notes",
            "required": False,
            "extraction": {
                "mode": "manual",
                "allow_manual": True,
            },
            "export": {
                "enabled": True,
                "column_name": "Notes",
                "width": 250,
                "align": "left",
                "format": "wrap_text",
            }
        },
    ]
}

# Create Schema
def create_sample_schemas():
    print("Creating sample schemas...")
    
    # 1. ML Methods Comparison
    schema1, created = Schema.objects.get_or_create(
        name="ML Methods Comparison",
        defaults={
            "name_zh": "机器学习方法对比",
            "description": "用于系统性文献综述的机器学习方法对比表，提取模型名称、数据集、准确率等关键信息",
            "category": "Machine Learning",
            "fields_definition": json.dumps(ml_methods_schema, ensure_ascii=False, indent=2),
            "version": "1.0",
            "created_by": "system",
        }
    )
    
    if created:
        print(f"✓ Created: {schema1.name} ({schema1.schema_id})")
    else:
        print(f"✓ Already exists: {schema1.name} ({schema1.schema_id})")
    
    # 2. Study Characteristics (for systematic review)
    study_characteristics_schema = {
        "schema_meta": {
            "name": "Study Characteristics",
            "description": "Extract study characteristics for systematic review",
            "category": "Systematic Review",
            "version": "1.0",
        },
        "export_config": {
            "default_format": "excel",
            "include_metadata": True,
            "include_confidence": False,
        },
        "fields": [
            {
                "field_id": "paper_id",
                "order": 1,
                "name": "Paper ID",
                "type": "auto",
                "required": True,
                "system_field": True,
                "export": {"enabled": True, "column_name": "ID", "width": 80, "align": "left"}
            },
            {
                "field_id": "study_design",
                "order": 2,
                "name": "Study Design",
                "name_zh": "研究设计",
                "type": "select",
                "required": True,
                "options": [
                    {"value": "rct", "label": "RCT"},
                    {"value": "cohort", "label": "Cohort Study"},
                    {"value": "case_control", "label": "Case-Control"},
                    {"value": "cross_sectional", "label": "Cross-sectional"},
                    {"value": "review", "label": "Review"},
                ],
                "extraction": {
                    "mode": "ai",
                    "prompt": "What is the study design?",
                },
                "export": {"enabled": True, "column_name": "Study Design", "width": 150, "align": "left"}
            },
            {
                "field_id": "sample_size",
                "order": 3,
                "name": "Sample Size",
                "name_zh": "样本量",
                "type": "number",
                "required": False,
                "validation": {"min": 1},
                "extraction": {
                    "mode": "ai",
                    "prompt": "What is the sample size of this study?",
                },
                "export": {"enabled": True, "column_name": "N", "width": 100, "align": "right"}
            },
            {
                "field_id": "intervention",
                "order": 4,
                "name": "Intervention",
                "name_zh": "干预措施",
                "type": "text",
                "required": False,
                "extraction": {
                    "mode": "ai",
                    "prompt": "What is the intervention being studied?",
                },
                "export": {"enabled": True, "column_name": "Intervention", "width": 200, "align": "left"}
            },
            {
                "field_id": "outcome",
                "order": 5,
                "name": "Primary Outcome",
                "name_zh": "主要结局",
                "type": "text",
                "required": False,
                "extraction": {
                    "mode": "ai",
                    "prompt": "What is the primary outcome measured in this study?",
                },
                "export": {"enabled": True, "column_name": "Outcome", "width": 200, "align": "left"}
            },
            {
                "field_id": "conclusion",
                "order": 6,
                "name": "Conclusion",
                "name_zh": "结论",
                "type": "long-text",
                "required": False,
                "extraction": {
                    "mode": "ai",
                    "prompt": "What is the main conclusion of this study?",
                },
                "export": {"enabled": True, "column_name": "Conclusion", "width": 300, "align": "left", "format": "wrap_text"}
            },
        ]
    }
    
    schema2, created = Schema.objects.get_or_create(
        name="Study Characteristics",
        defaults={
            "name_zh": "研究特征提取",
            "description": "用于系统性文献综述的研究特征提取，包括研究设计、样本量、干预措施、结局指标等",
            "category": "Systematic Review",
            "fields_definition": json.dumps(study_characteristics_schema, ensure_ascii=False, indent=2),
            "version": "1.0",
            "created_by": "system",
        }
    )
    
    if created:
        print(f"✓ Created: {schema2.name} ({schema2.schema_id})")
    else:
        print(f"✓ Already exists: {schema2.name} ({schema2.schema_id})")
    
    print("\n✅ Sample schemas created successfully!")
    print(f"\nVisit Schema Library: http://127.0.0.1:8000/projects/schemas/")

if __name__ == "__main__":
    create_sample_schemas()
