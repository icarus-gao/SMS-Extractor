# Data Extraction Feature Guide

## 📋 Overview

The Data Extraction feature seamlessly integrates with Schemas to provide a visual and intuitive way to track data extraction progress across all papers in your project.

## ✨ Key Features

### 1. **Schema-Based Progress Tracking**

Each schema in your project now displays:

**Elegant Progress Bar**  
Visual representation of extraction completion

**Real-time Statistics**  
  - Total papers vs. extracted papers
  - Completion percentage
  - Status breakdown (Completed, Verified, Failed, Pending, Processing)

**Color-Coded Progress**  
  - 🔴 Red (0-24%): Just started
  - 🟠 Orange (25-49%): Making progress
  - 🔵 Blue (50-74%): More than halfway
  - 🟢 Green (75-99%): Nearly complete
  - ✅ Success (100%): All done!

### 2. **Quick Extract Button**

**One-Click Extraction**  
"Extract All" button for each schema

**Automatic Configuration**  
Automatically selects all papers and the schema

**Pre-configured Modal**  
Opens the extraction modal pre-configured

**Paper Count Display**  
Shows remaining paper count

### 3. **Extraction Modal**

**Select What to Extract:**
- ✅ Schema dropdown (from project schemas)
- ✅ Paper multi-select with "Select All" checkbox
- ✅ Extraction method:

**AI Extraction**  
Automatic extraction using mock AI

**Manual Entry**  
Create empty forms for manual data entry

**Hybrid**  
AI extraction with manual review

### 4. **Status Badges**

Visual indicators for extraction status:
- 🟢 **Completed**: Extraction finished successfully
- 🔵 **Verified**: Data reviewed and confirmed
- 🟡 **Pending**: Awaiting manual input
- 🔄 **Processing**: Extraction in progress
- 🔴 **Failed**: Extraction encountered errors

## 🎯 User Workflow

### Step 1: Add Schema to Project
1. Navigate to project detail page
2. Go to "Schemas" tab
3. Click "Add Schema" button
4. Select from library or create new

### Step 2: Run Extraction

**Option A: Quick Extract (Recommended)**
1. In Schemas tab, find your schema
2. Click "Extract All (X papers)" button
3. Confirm in modal
4. Click "Start Extraction"

**Option B: Manual Selection**
1. Click "Run Extraction" button in Extractions tab
2. Select schema from dropdown
3. Check papers to extract
4. Choose extraction method
5. Click "Start Extraction"

### Step 3: Monitor Progress
- Return to Schemas tab
- Watch progress bars update
- See status breakdown in badges
- Track remaining papers

### Step 4: Review & Edit
1. Go to Extractions tab
2. View extraction cards
3. Click "View" to see extracted data
4. Click "Edit" to modify values
5. Click "Verify" to mark as reviewed

## 🎨 UI Design Highlights

### Schema List Layout
- **Left Column**: Schema info (name, description, status, field count)
- **Middle Column**: Progress bar with status badges
- **Right Column**: Action buttons (Extract All, View, Remove)

### Progress Bar Features
- Animated striped pattern
- Dynamic color based on completion
- Shows fraction (extracted/total)
- Smooth transitions

### Interactive Elements
- Hover effects on list items
- Badge tooltips for status details
- Smooth animations on interactions

## 🔧 Technical Implementation

### Backend Statistics
```python
# For each schema, calculate:
- total_papers: Total papers in project
- total_extracted: Papers with extractions
- remaining: Papers without extractions
- completed: Extractions with 'completed' status
- verified: Extractions with 'verified' status
- failed: Extractions with 'failed' status
- pending: Extractions with 'pending' status
- processing: Extractions with 'processing' status
- progress_percentage: (total_extracted / total_papers) * 100
```

### Mock AI Extraction
- Generates sample data based on schema field types
- Random confidence scores (70-99%)
- Supports all field types (text, number, boolean, select, etc.)
- Can be replaced with real AI integration

## 📊 Example Use Cases

### Use Case 1: Literature Review
- Schema: "Paper Characteristics"
- Extract: Title, Authors, Year, Methods, Results
- Track: Which papers have been reviewed
- Goal: Complete extraction for 50 papers

### Use Case 2: Systematic Review
- Schema: "Quality Assessment"
- Extract: Study design, Sample size, Risk of bias
- Track: Review progress across team members
- Goal: Verify all extractions

### Use Case 3: Meta-Analysis
- Schema: "Effect Sizes"
- Extract: Mean, SD, Sample size, p-value
- Track: Statistical data collection progress
- Goal: Extract quantitative data from all included studies

## 🚀 Future Enhancements

- Real AI integration (GPT-4, Claude, etc.)
- Bulk export to Excel/CSV
- Team collaboration with assignment
- Inter-rater reliability calculations
- Automated quality checks
- Template-based extraction
- PDF annotation integration

## 💡 Tips & Best Practices

1. **Lock Schemas**: Lock schemas before mass extraction to prevent accidental changes
2. **Hybrid Method**: Use hybrid extraction for best balance of speed and accuracy
3. **Verify Critical Data**: Always verify extractions for critical analyses
4. **Batch Processing**: Extract in batches to monitor quality
5. **Progress Monitoring**: Use Schemas tab to track overall project completion

## 🐛 Troubleshooting

**Problem**: Progress bar not updating
- **Solution**: Refresh the page after running extraction

**Problem**: Extract All button disabled
- **Solution**: Ensure papers are added to the project

**Problem**: Extraction failed
- **Solution**: Check schema has fields defined, verify paper data is accessible

## 📝 Notes

- Extractions are linked to schemas - if you remove a schema, extractions remain
- You can run extraction multiple times (duplicates are checked)
- Manual edits override AI extractions
- Verified status is the final state in the workflow

---

**Last Updated**: October 2, 2025
**Version**: 1.0.0
