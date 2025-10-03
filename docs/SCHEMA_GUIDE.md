# Schema Complete Guide - Including Evidence Feature

## 📚 Document Overview

This document is a comprehensive guide for **Schema (Data Extraction Template)** in the SMS Extractor system, covering:
1. The significance and role of Schema in systematic literature reviews
2. Complete Schema JSON format specification (including the new evidence attribute)
3. How to use AI tools to generate Schemas
4. Real-world use cases and best practices

**Last Updated**: October 3, 2025  
**Version**: 3.0 (New Evidence Attribute Feature)

---

## 📖 Table of Contents

1. [What is Schema](#what-is-schema)
2. [Significance of Schema](#significance-of-schema)
3. [Core Functions](#core-functions)
4. [Evidence Attribute Feature ⭐NEW](#evidence-attribute-feature-new)
5. [Complete Schema JSON Format](#complete-schema-json-format)
6. [Field Types Explained](#field-types-explained)
7. [AI-Assisted Schema Generation](#ai-assisted-schema-generation)
8. [Real-World Examples](#real-world-examples)
9. [Best Practices](#best-practices)

---

## What is Schema?

### Simple Definition

**Schema** = Data Extraction Template

Think of it like a survey questionnaire:
- **Survey questions** = Fields defined in Schema
- **Each respondent** = Each research paper
- **Survey answers** = Data extracted from papers

### Why Do We Need Schema?

#### Problems Without Schema ❌

```
Researcher A extracts: Method name, Accuracy, Year
Researcher B extracts: Algorithm, Performance, Author
Researcher C extracts: Title, Results, Page count

Result: Chaotic data format, impossible to compare and analyze!
```

#### With Schema ✅

```json
{
  "fields": [
    {"field_id": "method", "name": "Method Name"},
    {"field_id": "accuracy", "name": "Accuracy (%)"},
    {"field_id": "dataset", "name": "Dataset Used"}
  ]
}
```

**Everyone extracts the same information in the same format!**

---

## Significance of Schema

### In Systematic Literature Reviews

Schema is the **cornerstone** of systematic literature reviews (SLR):

```
Research Question
    ↓
Literature Search
    ↓
Define Schema  ← ⭐ Key step!
    ↓
Extract Data (using Schema)
    ↓
Analyze & Synthesize
    ↓
Draw Conclusions
```

**Without Schema** → Data chaos, cannot be aggregated  
**With Schema** → Standardized data, easy to compare and analyze

### Relationship with Meta-Analysis

Meta-analysis requires:
- **Quantitative data** (effect sizes, confidence intervals, sample sizes)
- **Standardized format** (all papers report the same metrics)
- **Complete information** (no missing critical data)

**Schema ensures you extract exactly what meta-analysis needs!**

### Relationship with Knowledge Graphs

Knowledge graphs need:
- **Structured entities** (methods, datasets, metrics)
- **Relationships** (which method works on which dataset)
- **Attributes** (accuracy, speed, year)

**Schema defines the structure of your knowledge graph!**

---

## Core Functions

### 1. Standardize Data Extraction ⭐⭐⭐⭐⭐

**Problem**: Different people extract different things  
**Solution**: Schema defines exactly what to extract

**Example**:
```json
{
  "field_id": "sample_size",
  "name": "Sample Size",
  "field_type": "number",
  "description": "Total number of participants in the study",
  "required": true
}
```

Everyone extracts the **same** Sample Size field!

### 2. Improve Data Quality ⭐⭐⭐⭐

**Problem**: Human errors in data entry  
**Solution**: Schema includes validation rules

**Example**:
```json
{
  "field_id": "accuracy",
  "field_type": "number",
  "validation": {
    "min": 0,
    "max": 100,
    "decimal_places": 2
  }
}
```

System prevents invalid entries (e.g., accuracy > 100%)!

### 3. Support Team Collaboration ⭐⭐⭐⭐⭐

**Problem**: Team members don't know what to extract  
**Solution**: Schema is the shared "contract"

**Workflow**:
```
1. Team lead defines Schema
2. Team members extract according to Schema
3. Data automatically aggregates
4. No communication overhead!
```

### 4. Accelerate Data Extraction ⭐⭐⭐

**Problem**: Manually deciding what to extract for each paper  
**Solution**: Schema provides a clear checklist

**Time Savings**:
- Without Schema: 30-60 min per paper (figuring out what to extract)
- With Schema: 10-20 min per paper (just fill in the blanks)

### 5. Facilitate Export and Analysis ⭐⭐⭐⭐

**Problem**: Need to reorganize data for analysis  
**Solution**: Schema ensures data is analysis-ready

**Export Formats**:
- Excel (pivot tables, charts)
- CSV (R, Python analysis)
- JSON (web visualization)
- SQL (database queries)

---

## Evidence Attribute Feature ⭐NEW

### What is the Evidence Attribute?

**Evidence** = Record the source and basis of extracted data

For each piece of data extracted from a paper, you can attach:
- 📍 **Location**: Section, page, table/figure number
- 📝 **Quote**: Direct quote from the paper
- 💡 **Notes**: Any clarifying remarks

### Why Evidence is Important

#### 1. Traceability ⭐⭐⭐⭐⭐

**Problem**: Reviewers question data sources  
**Solution**: Every data point has clear textual support

**Example**:
```
Field: Sample Size
Value: 1,250

Evidence:
Section: Methods > Participants
Page: 4
Quote: "A total of 1,250 participants (mean age 45.3 ± 12.7 years) 
        were recruited from three hospitals."
```

Reviewers can verify directly!

#### 2. Quality Control ⭐⭐⭐⭐

**Problem**: Extractors may misremember or misunderstand  
**Solution**: Requiring quotes forces careful reading

**Comparison**:
```
❌ Without Evidence:
   Accuracy: 95.3%  (might be from abstract, methods, or results?)

✅ With Evidence:
   Accuracy: 95.3%
   Evidence: "Results section, Table 2: Test accuracy 95.3% (CI: 94.1-96.5%)"
```

#### 3. Team Collaboration ⭐⭐⭐⭐

**Problem**: Second reviewer needs to re-locate information  
**Solution**: Evidence provides direct navigation

**Efficiency**:
- Without Evidence: Re-read entire paper (15-30 min)
- With Evidence: Jump to exact location (1-2 min)

### Evidence Format

#### Standard Template

```
Section: [Section name]
Page: [Page number]
Location: [Table/Figure number] (optional)
Quote: "[Direct quote from paper]"
Notes: [Additional context] (optional)
```

#### Examples

**Example 1: Text from Results**
```
Section: Results
Page: 7
Quote: "The proposed method achieved 95.3% accuracy on CIFAR-10."
```

**Example 2: Data from Table**
```
Section: Results
Page: 8
Location: Table 2, Row 'CNN', Column 'Accuracy'
Quote: "CNN Test Accuracy: 95.3% (95% CI: 94.1-96.5%)"
```

**Example 3: Data from Figure**
```
Section: Experiments
Page: 9
Location: Figure 3 caption
Quote: "Training converged after 120 epochs with final accuracy of 95.3%"
```

**Example 4: Multiple Sources**
```
Section: Methods, Page: 4
Quote: "Treatment group n=625"

Section: Methods, Page: 4
Quote: "Control group n=625"

Notes: Total = 625 + 625 = 1,250
```

### Evidence Quality Levels

| Level | Requirements | Example |
|-------|--------------|---------|
| ⭐⭐⭐⭐⭐ | Section + Page + Location + Complete Quote | Section: Results, Page: 7, Table 2, Quote: "..." |
| ⭐⭐⭐⭐ | Section + Page + Quote | Section: Methods, Page: 4, Quote: "..." |
| ⭐⭐⭐ | Section + Page | Section: Results, Page: 6 |
| ⭐⭐ | Section only | Section: Methods |
| ⭐ | No specific location | "Mentioned in the paper..." |

**Recommendation**: All critical data should reach ⭐⭐⭐⭐ or ⭐⭐⭐⭐⭐ level.

---

## Complete Schema JSON Format

### Top-Level Structure

```json
{
  "schema_meta": {
    "schema_name": "Machine Learning Study Extraction",
    "version": "1.0",
    "description": "Extract ML model performance metrics",
    "domain": "Machine Learning",
    "author": "Research Team",
    "created_at": "2025-10-03",
    "tags": ["ML", "performance", "benchmark"]
  },
  
  "export_config": {
    "default_format": "excel",
    "include_metadata": true,
    "include_confidence": false,
    "include_evidence": true,
    "evidence_column_suffix": "_Evidence",
    "date_format": "YYYY-MM-DD",
    "number_format": "0.00"
  },
  
  "fields": [
    // Field definitions here
  ]
}
```

### Field Definition (Complete)

```json
{
  "field_id": "accuracy",
  "name": "Accuracy (%)",
  "name_zh": "准确率",
  "description": "Model accuracy on test set",
  "field_type": "number",
  "required": true,
  
  "validation": {
    "min": 0,
    "max": 100,
    "decimal_places": 2
  },
  
  "evidence": {
    "enabled": true,
    "required": true,
    "format": "location + quote",
    "description": "Find accuracy in Results section and quote original text",
    "template": "Section: [section]\\nPage: [page]\\nQuote: \\\"[quote]\\\""
  },
  
  "export": {
    "enabled": true,
    "column_name": "Accuracy",
    "column_width": 15,
    "format": "0.00",
    "alignment": "center"
  }
}
```

---

## Field Types Explained

### 1. text - Single Line Text

**Use Case**: Short text like names, titles, identifiers

**Definition**:
```json
{
  "field_id": "method_name",
  "name": "Method Name",
  "field_type": "text",
  "placeholder": "e.g., ResNet-50",
  "validation": {
    "max_length": 100
  }
}
```

**Examples**:
- Method Name: "ResNet-50"
- Dataset: "CIFAR-10"
- Author: "Smith et al."

### 2. textarea - Multi-Line Text

**Use Case**: Long text like abstracts, descriptions

**Definition**:
```json
{
  "field_id": "abstract",
  "name": "Abstract",
  "field_type": "textarea",
  "rows": 5,
  "validation": {
    "min_length": 50,
    "max_length": 5000
  }
}
```

**Examples**:
- Abstract
- Key findings
- Methodology description

### 3. number - Numeric Value

**Use Case**: Quantitative metrics, measurements

**Definition**:
```json
{
  "field_id": "sample_size",
  "name": "Sample Size",
  "field_type": "number",
  "validation": {
    "min": 1,
    "max": 1000000,
    "decimal_places": 0
  }
}
```

**Examples**:
- Sample Size: 1250
- Accuracy: 95.3
- Training Time: 12.5 (hours)

### 4. select - Single Choice

**Use Case**: Choose one from predefined options

**Definition**:
```json
{
  "field_id": "study_type",
  "name": "Study Type",
  "field_type": "select",
  "options": [
    {"value": "rct", "label": "Randomized Controlled Trial"},
    {"value": "cohort", "label": "Cohort Study"},
    {"value": "case_control", "label": "Case-Control Study"},
    {"value": "cross_sectional", "label": "Cross-Sectional Study"}
  ]
}
```

**Examples**:
- Study Type
- Model Architecture
- Dataset Type

### 5. multiselect - Multiple Choice

**Use Case**: Select multiple from predefined options

**Definition**:
```json
{
  "field_id": "data_augmentation",
  "name": "Data Augmentation Techniques",
  "field_type": "multiselect",
  "options": [
    {"value": "rotation", "label": "Rotation"},
    {"value": "flip", "label": "Horizontal/Vertical Flip"},
    {"value": "crop", "label": "Random Crop"},
    {"value": "color", "label": "Color Jittering"},
    {"value": "noise", "label": "Gaussian Noise"}
  ]
}
```

**Examples**:
- Data Augmentation: ["rotation", "flip", "crop"]
- Evaluation Metrics: ["accuracy", "precision", "recall", "f1"]

### 6. boolean - Yes/No

**Use Case**: Binary choices

**Definition**:
```json
{
  "field_id": "peer_reviewed",
  "name": "Peer Reviewed",
  "field_type": "boolean",
  "default": true
}
```

**Examples**:
- Peer Reviewed: Yes/No
- Open Source: Yes/No
- Preprint: Yes/No

### 7. date - Date Value

**Use Case**: Temporal information

**Definition**:
```json
{
  "field_id": "publication_date",
  "name": "Publication Date",
  "field_type": "date",
  "validation": {
    "min_date": "2000-01-01",
    "max_date": "2025-12-31",
    "format": "YYYY-MM-DD"
  }
}
```

**Examples**:
- Publication Date: 2024-03-15
- Study Start Date: 2023-01-01

---

## AI-Assisted Schema Generation

### Why Use AI for Schema Generation?

**Benefits**:
1. ⚡ Fast: Generate in seconds instead of hours
2. 🎯 Domain-aware: AI understands different research fields
3. 📋 Comprehensive: AI suggests fields you might miss
4. 🔄 Iterative: Easy to refine and adjust

### Prompt Template

```
You are helping me create a data extraction schema for systematic literature review.

**Research Topic**: [Your research topic]

**Research Question**: [Your specific research question]

**Paper Type**: [e.g., empirical studies, clinical trials, theoretical papers]

**Target Data**: [What kind of data you want to extract]

Please generate a complete Schema JSON following this format:
{
  "schema_meta": {
    "schema_name": "[Descriptive name]",
    "description": "[What this schema is for]",
    "domain": "[Research domain]",
    "version": "1.0"
  },
  "fields": [
    {
      "field_id": "[unique_id]",
      "name": "[Field name]",
      "field_type": "[text|textarea|number|select|multiselect|boolean|date]",
      "description": "[What this field extracts]",
      "required": [true|false],
      "validation": { /* validation rules */ },
      "evidence": {
        "enabled": true,
        "required": [true for critical quantitative data],
        "description": "[Where to find this data in papers]"
      }
    }
  ]
}

**Requirements**:
1. Include essential bibliographic fields (title, authors, year)
2. Include key quantitative metrics (with evidence required)
3. Include methodological fields (study design, sample size)
4. Add appropriate validation rules
5. Enable evidence for all critical data points
6. Provide clear descriptions for each field
```

### Example: Machine Learning Research

**Your Prompt**:
```
Research Topic: Deep Learning for Image Classification
Research Question: What are the state-of-the-art accuracies on standard benchmarks?
Paper Type: Empirical ML papers
Target Data: Model architecture, dataset, accuracy, training details
```

**AI Response** (Example):
```json
{
  "schema_meta": {
    "schema_name": "Image Classification Performance Extraction",
    "description": "Extract DL model performance on image classification benchmarks",
    "domain": "Machine Learning - Computer Vision",
    "version": "1.0"
  },
  "fields": [
    {
      "field_id": "paper_title",
      "name": "Paper Title",
      "field_type": "text",
      "required": true,
      "description": "Full title of the paper"
    },
    {
      "field_id": "model_name",
      "name": "Model Name",
      "field_type": "text",
      "required": true,
      "description": "Name of the proposed model (e.g., ResNet-50, ViT-Large)",
      "evidence": {
        "enabled": true,
        "required": false,
        "description": "Usually in Abstract or Introduction"
      }
    },
    {
      "field_id": "dataset",
      "name": "Dataset",
      "field_type": "select",
      "required": true,
      "options": [
        {"value": "imagenet", "label": "ImageNet"},
        {"value": "cifar10", "label": "CIFAR-10"},
        {"value": "cifar100", "label": "CIFAR-100"},
        {"value": "other", "label": "Other"}
      ]
    },
    {
      "field_id": "test_accuracy",
      "name": "Test Accuracy (%)",
      "field_type": "number",
      "required": true,
      "validation": {
        "min": 0,
        "max": 100,
        "decimal_places": 2
      },
      "evidence": {
        "enabled": true,
        "required": true,
        "description": "Find in Results section, usually in a table",
        "template": "Section: Results\\nPage: [page]\\nLocation: [table/figure]\\nQuote: \\\"[accuracy value]\\\""
      }
    },
    {
      "field_id": "training_epochs",
      "name": "Training Epochs",
      "field_type": "number",
      "required": false,
      "validation": {
        "min": 1,
        "max": 10000
      },
      "evidence": {
        "enabled": true,
        "required": false,
        "description": "Check Methods or Experimental Setup"
      }
    }
  ]
}
```

### Tips for AI Schema Generation

1. **Be Specific**: The more details you provide, the better the schema
2. **Iterate**: Generate, review, refine, regenerate
3. **Domain Knowledge**: AI knows general patterns, but you know your specific needs
4. **Evidence Strategy**: Require evidence for all quantitative and critical qualitative fields
5. **Validation Rules**: Add constraints to prevent data entry errors

---

## Real-World Examples

### Example 1: Clinical Trial Extraction

```json
{
  "schema_meta": {
    "schema_name": "Clinical Trial Data Extraction",
    "domain": "Medicine - Clinical Research",
    "version": "1.0"
  },
  "fields": [
    {
      "field_id": "trial_id",
      "name": "Trial Registration ID",
      "field_type": "text",
      "required": true,
      "description": "ClinicalTrials.gov or similar ID"
    },
    {
      "field_id": "sample_size",
      "name": "Total Sample Size",
      "field_type": "number",
      "required": true,
      "validation": {"min": 1},
      "evidence": {
        "enabled": true,
        "required": true,
        "description": "Find in Methods > Participants section"
      }
    },
    {
      "field_id": "intervention",
      "name": "Intervention",
      "field_type": "textarea",
      "required": true,
      "description": "Description of treatment/intervention",
      "evidence": {
        "enabled": true,
        "required": true
      }
    },
    {
      "field_id": "primary_outcome",
      "name": "Primary Outcome",
      "field_type": "text",
      "required": true,
      "evidence": {
        "enabled": true,
        "required": true,
        "description": "Usually in Methods or Results"
      }
    },
    {
      "field_id": "effect_size",
      "name": "Effect Size (Odds Ratio)",
      "field_type": "number",
      "required": false,
      "validation": {"min": 0, "decimal_places": 2},
      "evidence": {
        "enabled": true,
        "required": true,
        "description": "Find in Results, often in tables"
      }
    },
    {
      "field_id": "p_value",
      "name": "P-value",
      "field_type": "number",
      "required": false,
      "validation": {"min": 0, "max": 1, "decimal_places": 4},
      "evidence": {
        "enabled": true,
        "required": true
      }
    }
  ]
}
```

### Example 2: Software Engineering Study

```json
{
  "schema_meta": {
    "schema_name": "Software Bug Prediction Study",
    "domain": "Software Engineering",
    "version": "1.0"
  },
  "fields": [
    {
      "field_id": "project_name",
      "name": "Software Project",
      "field_type": "text",
      "required": true,
      "description": "Name of the analyzed software project"
    },
    {
      "field_id": "language",
      "name": "Programming Language",
      "field_type": "select",
      "required": true,
      "options": [
        {"value": "java", "label": "Java"},
        {"value": "python", "label": "Python"},
        {"value": "cpp", "label": "C++"},
        {"value": "csharp", "label": "C#"},
        {"value": "other", "label": "Other"}
      ]
    },
    {
      "field_id": "loc",
      "name": "Lines of Code",
      "field_type": "number",
      "required": false,
      "validation": {"min": 0},
      "evidence": {
        "enabled": true,
        "required": false,
        "description": "Usually in Project Characteristics section"
      }
    },
    {
      "field_id": "bug_count",
      "name": "Number of Bugs",
      "field_type": "number",
      "required": true,
      "validation": {"min": 0},
      "evidence": {
        "enabled": true,
        "required": true,
        "description": "Find in Results or Dataset Description"
      }
    },
    {
      "field_id": "prediction_accuracy",
      "name": "Prediction Accuracy (%)",
      "field_type": "number",
      "required": true,
      "validation": {"min": 0, "max": 100, "decimal_places": 2},
      "evidence": {
        "enabled": true,
        "required": true,
        "description": "Usually in Results table"
      }
    }
  ]
}
```

---

## Best Practices

### DO ✅

1. **Start Simple, Iterate**
   - Begin with 5-10 essential fields
   - Add more after extracting a few papers
   - Refine based on what you actually find

2. **Require Evidence for Critical Data**
   ```json
   {
     "field_id": "primary_outcome_value",
     "evidence": {
       "enabled": true,
       "required": true  // ⭐ Critical quantitative data
     }
   }
   ```

3. **Use Validation Rules**
   ```json
   {
     "field_type": "number",
     "validation": {
       "min": 0,
       "max": 100,
       "decimal_places": 2
     }
   }
   ```

4. **Provide Clear Descriptions**
   ```json
   {
     "description": "Total number of participants at baseline (before any dropouts)",
     "evidence": {
       "description": "Usually in Methods > Participants or Results > Baseline Characteristics"
     }
   }
   ```

5. **Use Appropriate Field Types**
   - `number` for metrics (with min/max validation)
   - `select` for categorical data (consistent categories)
   - `boolean` for yes/no questions
   - `date` for temporal data

### DON'T ❌

1. **Don't Make Everything Required**
   - Only mark fields as required if truly essential
   - Papers may not report all data

2. **Don't Over-Complicate**
   ```json
   // ❌ Too granular
   {"field_id": "accuracy_train"},
   {"field_id": "accuracy_val"},
   {"field_id": "accuracy_test"},
   {"field_id": "accuracy_train_epoch_10"},
   // ... (too many variations)
   
   // ✅ Simpler
   {"field_id": "test_accuracy"},
   {"field_id": "validation_accuracy"}
   ```

3. **Don't Forget Evidence for Quantitative Data**
   ```json
   // ❌ No evidence
   {
     "field_id": "effect_size",
     "field_type": "number"
   }
   
   // ✅ With evidence
   {
     "field_id": "effect_size",
     "field_type": "number",
     "evidence": {
       "enabled": true,
       "required": true
     }
   }
   ```

4. **Don't Use Free Text When Categories Exist**
   ```json
   // ❌ Free text (will get messy)
   {
     "field_id": "study_design",
     "field_type": "text"
   }
   // Results: "RCT", "rct", "Randomized trial", "random controlled"...
   
   // ✅ Predefined options
   {
     "field_id": "study_design",
     "field_type": "select",
     "options": [
       {"value": "rct", "label": "Randomized Controlled Trial"},
       {"value": "cohort", "label": "Cohort Study"}
     ]
   }
   ```

5. **Don't Skip Testing**
   - Test your schema on 2-3 papers before large-scale extraction
   - Adjust field definitions based on what you find

---

## FAQ

### Q: How many fields should a Schema have?

**A**: Typically 10-30 fields
- Minimum: 5-10 essential fields
- Sweet spot: 15-20 fields
- Maximum: 30-50 fields (very comprehensive reviews)

### Q: Should every field have evidence enabled?

**A**: No, be strategic:
- ✅ **Require evidence for**: Quantitative metrics, effect sizes, sample sizes, primary outcomes
- ✅ **Optional evidence for**: Methodological details, secondary outcomes
- ❌ **Skip evidence for**: Bibliographic data (title, authors, year)

### Q: Can I modify a Schema after starting extraction?

**A**: Yes, but carefully:
- ✅ **Safe**: Add new fields (won't affect existing data)
- ⚠️ **Caution**: Rename fields (update all references)
- ❌ **Risky**: Change field types (may break existing data)

### Q: How detailed should evidence quotes be?

**A**: Balance detail and practicality:
- **Minimum**: Enough to locate the data (section + page)
- **Recommended**: Short relevant quote (1-2 sentences)
- **Avoid**: Copying entire paragraphs

### Q: Can I use AI to fill in evidence automatically?

**A**: Partially:
- AI can suggest sections/pages
- AI can extract relevant quotes
- **But**: Human should verify accuracy
- **Future**: Full automation is a roadmap item

---

## Summary

### Key Takeaways

1. **Schema = Standardization**: Ensures everyone extracts the same data
2. **Evidence = Credibility**: Makes your data verifiable and trustworthy
3. **Validation = Quality**: Prevents errors at data entry time
4. **AI = Efficiency**: Can generate schemas quickly, but needs human refinement

### Schema Lifecycle

```
1. Define Research Question
2. Generate/Design Schema (with AI help)
3. Test on 2-3 papers
4. Refine Schema
5. Extract data from all papers
6. Export and analyze
7. Report findings
```

### Next Steps

1. **Define your research question clearly**
2. **Use AI to generate a draft schema** (use the prompt template above)
3. **Review and refine** the schema
4. **Test on a few papers** before full extraction
5. **Enable evidence for critical fields**
6. **Start extracting!**

---

**Document Version**: 3.0  
**Last Updated**: October 3, 2025  
**Maintained by**: SMS Extractor Team

For more information:
- Evidence Feature Details: `EVIDENCE_FEATURE.md`
- User Guide: `SCHEMA_USER_GUIDE.md`
- Release Notes: `RELEASE_v1.0.0.md`
