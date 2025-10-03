# Analysis Feature - User Guide

## 📊 Overview

The **Analysis** feature provides comprehensive visualization and export capabilities for extraction results in your SMS Extractor projects. It helps you understand patterns, validate data quality, and export results for further analysis.

## 🎯 Features

### 1. **Data Aggregation by Schema**
- View all extraction results organized by schema
- See total extractions and verification status at a glance
- Collapse/expand each schema for detailed inspection

### 2. **Field-Level Statistics**
- **Data Points Count**: How many papers have data for each field
- **Average Confidence**: Overall confidence score across all extractions
- **Value Distribution**: For select/multiselect fields, see frequency of each option
- **Sample Values**: Preview actual extracted values with confidence scores

### 3. **Detailed Data Matrix**
- Cross-tabulation view showing all papers × all fields
- Expandable table for deep data inspection
- Confidence scores displayed inline
- Status indicators (Completed/Verified)

### 4. **Export Functionality**
- **Multiple Formats**: CSV, JSON
- **Scope Options**: Export all schemas or individual schema
- **UTF-8 with BOM**: Excel-compatible CSV encoding
- **Structured Data**: Flattened structure for easy analysis

## 📖 How to Use

### Accessing Analysis Tab

1. Navigate to your project detail page
2. Click the **"Analysis"** tab (with bar chart icon 📊)
3. View aggregated extraction results

### Understanding the Analysis View

#### Schema Accordion
Each schema is displayed as an expandable card showing:

```
┌─────────────────────────────────────────────────────┐
│ 📊 My Research Schema                               │
│ [23 extractions] [18 verified]          [Download] │
├─────────────────────────────────────────────────────┤
│ Field-Level Statistics Table                        │
│ ┌──────────────┬──────┬────────┬──────────┬────────┐
│ │ Field Name   │ Type │ Points │ Avg Conf │ Distrib│
│ ├──────────────┼──────┼────────┼──────────┼────────┤
│ │ Study Type   │select│  20    │   92%    │ RCT:15 │
│ │ Sample Size  │number│  18    │   85%    │ [vals] │
│ └──────────────┴──────┴────────┴──────────┴────────┘
│                                                       │
│ [Show/Hide] Detailed Extraction Data                │
│ ┌──────────────┬───────────────┬──────────┬────────┐
│ │ Paper        │ Study Type    │ Sample   │ Status │
│ ├──────────────┼───────────────┼──────────┼────────┤
│ │ Smith 2023   │ RCT [95%]     │ 120 [90%]│Verified│
│ │ Jones 2024   │ Cohort [88%]  │ 350 [82%]│Completed│
│ └──────────────┴───────────────┴──────────┴────────┘
└─────────────────────────────────────────────────────┘
```

#### Field Statistics Columns

1. **Field Name**: Schema field identifier
2. **Type**: Field data type (text, number, select, etc.)
3. **Data Points**: Number of papers with extracted values
4. **Avg Confidence**: 
   - 🟢 Green (90%+): High quality
   - 🔵 Blue (70-89%): Good quality
   - 🟡 Yellow (50-69%): Medium quality
   - 🔴 Red (<50%): Needs review
5. **Value Distribution**:
   - For **select/multiselect**: Shows option → count mapping
   - For **other types**: Shows sample values with confidence

### Exporting Data

#### Export All Schemas

1. Click **"Export All"** dropdown button (top right)
2. Choose format:
   - **CSV**: For Excel, statistical software (SPSS, R, Python)
   - **JSON**: For programmatic processing, APIs

#### Export Single Schema

1. Click the **download icon** (📥) next to schema name
2. Data exports immediately as CSV
3. Use query parameter `?format=json` for JSON export

#### CSV Export Structure (Single Schema)

```csv
Paper ID,Paper Title,Status,Method,Field1,Field1 (Confidence),Field2,Field2 (Confidence),...
paper_001,Smith 2023,verified,ai,RCT,95,120,90,...
paper_002,Jones 2024,completed,ai,Cohort,88,350,82,...
```

#### CSV Export Structure (All Schemas)

```csv
Schema ID,Schema Name,Paper ID,Paper Title,Status,Method,Extracted Data,Created At,Updated At
schema_abc,My Schema,paper_001,Smith 2023,verified,ai,"{""field1"":""RCT""}",2025-10-01,2025-10-02
```

#### JSON Export Structure

```json
[
  {
    "extraction_id": 123,
    "paper_id": "paper_001",
    "paper_title": "Smith et al. 2023",
    "schema_id": "schema_abc",
    "schema_name": "My Research Schema",
    "status": "verified",
    "extraction_method": "ai",
    "extracted_data": {
      "fields": {
        "field_study_type": {
          "value": "RCT",
          "confidence": 0.95
        },
        "field_sample_size": {
          "value": 120,
          "confidence": 0.90
        }
      },
      "metadata": {
        "average_confidence": 0.925,
        "extraction_date": "2025-10-01T10:30:00"
      }
    },
    "created_at": 1696154400,
    "updated_at": "2025-10-02T15:45:00"
  }
]
```

## 🔍 Use Cases

### 1. Data Quality Assessment

**Goal**: Identify fields with low confidence scores

**Steps**:
1. Go to Analysis tab
2. Expand each schema
3. Look at "Avg Confidence" column
4. Fields with 🔴 red bars (<50%) need manual review
5. Click "Go to Extraction Tab" to review/edit those records

### 2. Value Distribution Analysis

**Goal**: Understand categorical data patterns

**Steps**:
1. Expand schema with select/multiselect fields
2. Check "Value Distribution" column
3. See frequency counts for each option
4. Example: "Study Type: RCT: 15, Cohort: 5, Case-Control: 3"

### 3. Cross-Paper Comparison

**Goal**: Compare extracted values across papers

**Steps**:
1. Expand schema
2. Click "Show/Hide" under "Detailed Extraction Data"
3. View matrix table with all papers and fields
4. Spot patterns, outliers, or missing data

### 4. Export for Meta-Analysis

**Goal**: Prepare data for statistical analysis in R/SPSS/Python

**Steps**:
1. Complete extractions and verify results
2. Go to Analysis tab
3. Click "Export All" → "Export as CSV"
4. Open in Excel or import to statistical software
5. Use columns with confidence scores to weight data

### 5. Data Completeness Check

**Goal**: Find papers missing specific field values

**Steps**:
1. Check "Data Points" count for each field
2. If count < total papers, some data is missing
3. Calculate: Missing = Total Papers - Data Points
4. Export to CSV to identify which papers need completion

## 📈 Interpreting Statistics

### Average Confidence Score

The confidence score indicates how certain the AI extraction was:

| Score | Meaning | Recommendation |
|-------|---------|----------------|
| 90-100% | 🟢 Very High | Generally reliable, quick spot-check |
| 70-89% | 🔵 High | Review outliers, validate key fields |
| 50-69% | 🟡 Medium | Manual review recommended |
| <50% | 🔴 Low | Requires thorough manual review |

**Note**: Manual extractions always have 100% confidence.

### Data Points Count

- **High count (close to total papers)**: Good coverage
- **Low count**: 
  - Field might not apply to all papers
  - Extraction issues (check failed extractions)
  - Some papers pending extraction

### Value Distribution

For **select fields**, distribution helps identify:
- Most common categories
- Rare categories (may indicate data quality issues)
- Balanced vs imbalanced datasets

**Example**:
```
Study Design:
  RCT: 45          ← Most common
  Cohort: 12
  Case-Control: 3  ← Rare, double-check these
```

## 🛠️ Technical Details

### Backend Implementation

**View Function**: `dashboard.views.prepare_analysis_data()`

**Process**:
1. Query all extractions for project (status: completed/verified)
2. Group by schema
3. For each schema:
   - Get field definitions
   - Iterate through extractions
   - Extract field values and confidence scores
   - Calculate aggregations (avg, count, distribution)
4. Return structured data to template

**Export Function**: `dashboard.views.project_analysis_export()`

**Process**:
1. Filter extractions by project (+ optional schema)
2. For CSV:
   - Single schema: Create column per field + confidence column
   - Multiple schemas: Generic structure with JSON blob
3. For JSON: Full structured data with metadata
4. Set appropriate HTTP headers for download

### Data Structure

**Analysis Data (Context Variable)**:
```python
analysis_data = [
    {
        'schema': Schema object,
        'schema_name': str,
        'schema_id': str,
        'total_extractions': int,
        'verified_count': int,
        'completed_count': int,
        'field_aggregations': [
            {
                'field_id': str,
                'field_name': str,
                'field_type': str,
                'total_values': int,
                'avg_confidence': float (0-100),
                'values': [
                    {
                        'paper_title': str,
                        'paper_id': str,
                        'value': any,
                        'confidence': float (0-1),
                        'status': str
                    },
                    ...
                ],
                'value_distribution': {
                    'option1': count1,
                    'option2': count2,
                    ...
                }
            },
            ...
        ]
    },
    ...
]
```

### URL Endpoints

```python
# View analysis in browser
GET /projects/<project_id>/  # Navigate to Analysis tab

# Export all schemas
GET /projects/<project_id>/analysis/export/?format=csv
GET /projects/<project_id>/analysis/export/?format=json

# Export single schema
GET /projects/<project_id>/analysis/export/<schema_id>/?format=csv
GET /projects/<project_id>/analysis/export/<schema_id>/?format=json
```

## 🎨 UI Components

### Bootstrap Classes Used

- **Accordion**: Collapsible schema sections
- **Tables**: Data display with hover effects
- **Progress Bars**: Confidence visualization
- **Badges**: Counts and status indicators
- **Dropdowns**: Export format selection
- **Cards**: Empty state messaging

### Responsive Design

- **Desktop**: Full table layout with all columns
- **Tablet**: Scrollable tables with fixed headers
- **Mobile**: Stacked layout, collapsible sections

## 🚀 Best Practices

### 1. Data Preparation

✅ **DO**:
- Complete extractions before analysis
- Verify high-priority extractions
- Use consistent schema definitions

❌ **DON'T**:
- Analyze with mostly pending extractions
- Export before reviewing confidence scores
- Change schema fields after extractions

### 2. Export Workflow

✅ **DO**:
- Export single schema for focused analysis
- Use CSV for statistical software
- Use JSON for programmatic processing
- Check exported file before complex analysis

❌ **DON'T**:
- Export all schemas if you only need one
- Import CSV with mixed schemas to Excel
- Forget to handle NULL values in analysis

### 3. Data Quality

✅ **DO**:
- Review fields with low confidence
- Check value distribution for outliers
- Validate rare categories manually
- Re-extract failed extractions before export

❌ **DON'T**:
- Trust low-confidence data blindly
- Ignore missing data patterns
- Export unverified extractions for publication

## 🐛 Troubleshooting

### No Analysis Data Shown

**Symptoms**: "No Analysis Data Available" message

**Causes**:
1. No extractions completed yet
2. All extractions in pending/processing status
3. Extractions failed

**Solutions**:
- Go to Extraction tab
- Run extractions on papers
- Wait for processing to complete
- Check for error messages in extraction records

### Export Downloads Empty File

**Symptoms**: CSV/JSON file has headers but no data

**Causes**:
1. No completed/verified extractions
2. Schema deleted after extractions
3. Database query issue

**Solutions**:
- Verify extractions exist in Extraction tab
- Check extraction status (must be completed/verified)
- Try exporting single schema first

### Confidence Scores Show N/A

**Symptoms**: "N/A" instead of progress bar

**Causes**:
1. Manual extractions (confidence = 100% by default)
2. Old extraction format without metadata
3. Field never extracted

**Solutions**:
- This is normal for manual extractions
- Re-extract with AI to get confidence scores
- Update extraction metadata structure

### Value Distribution Empty

**Symptoms**: No badges shown in distribution column

**Causes**:
1. Field type is not select/multiselect
2. No values extracted for this field
3. All values are NULL

**Solutions**:
- Check field type in schema definition
- View "Sample Values" section instead
- Verify extractions completed successfully

## 📚 Related Documentation

- **EXTRACTION_FEATURE_GUIDE.md** - How to run extractions
- **EXTRACTION_TAB_UNIFIED.md** - Managing schemas and extractions
- **SCHEMA_USER_GUIDE.md** - Creating and editing schemas
- **SCHEMA_EXPORT_IMPLEMENTATION.md** - Schema export features

## 🎯 Future Enhancements

### Planned Features

1. **Interactive Charts**
   - Bar charts for value distribution
   - Line charts for confidence trends
   - Pie charts for categorical breakdowns

2. **Advanced Filtering**
   - Filter by confidence range
   - Filter by extraction date
   - Filter by status
   - Search within values

3. **Statistical Analysis**
   - Correlation between fields
   - Inter-rater reliability (for verified vs AI)
   - Missing data analysis
   - Confidence distribution histograms

4. **Batch Operations**
   - Export multiple schemas at once
   - Compare across projects
   - Merge data from related schemas

5. **Visualization Options**
   - Heatmap view
   - Network graph for relationships
   - Timeline view for temporal data

### Requested Features

- Excel (.xlsx) export with formatting
- SPSS (.sav) export
- R data frame export
- Automated quality reports
- Email scheduled exports

## 💡 Tips & Tricks

### Tip 1: Quick Quality Check
Sort by "Avg Confidence" to find fields needing review.

### Tip 2: Export for Backup
Regularly export as JSON to backup your extraction data.

### Tip 3: Use Detailed Matrix for Outliers
The detailed data table helps spot anomalies across papers.

### Tip 4: Combine with Extraction Tab
Use Analysis for overview, Extraction tab for detailed editing.

### Tip 5: Schema-Specific Exports
Export each schema separately for cleaner data files.

## 🎉 Summary

The Analysis feature transforms raw extraction results into actionable insights through:
- 📊 **Visual aggregation** of extraction statistics
- 🔍 **Field-level analysis** with confidence scoring
- 📋 **Cross-paper comparison** in matrix format
- 💾 **Flexible export** to CSV and JSON
- 🎯 **Quality assessment** tools

Use this feature to validate your extraction workflow, identify data quality issues, and prepare results for meta-analysis or publication!
