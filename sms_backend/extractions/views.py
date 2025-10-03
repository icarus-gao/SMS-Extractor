"""
Views for Data Extraction functionality
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views import View
import time

from .models import Extraction
from projects.models import Project, Schema
from papers.models import Paper
from .extraction_engine import mock_extract_data, manual_extract_data


# ==================== Extraction Management ====================

@require_POST
def run_extraction(request, project_id):
    """Run data extraction on selected papers with selected schema"""
    project = get_object_or_404(Project, project_id=project_id)
    
    # Get form data
    schema_id = request.POST.get('schema_id')
    paper_ids = request.POST.getlist('paper_ids')
    extraction_method = request.POST.get('extraction_method', 'ai')
    
    # Validation
    if not schema_id:
        messages.error(request, 'Please select a schema!')
        return redirect('dashboard:project-detail', project_id=project_id)
    
    if not paper_ids:
        messages.error(request, 'Please select at least one paper!')
        return redirect('dashboard:project-detail', project_id=project_id)
    
    schema = get_object_or_404(Schema, schema_id=schema_id)
    
    # Check if schema fields are defined
    if not schema.get_fields():
        messages.error(request, f'Schema "{schema.name}" has no fields defined!')
        return redirect('dashboard:project-detail', project_id=project_id)
    
    # Run extraction for each paper
    success_count = 0
    error_count = 0
    batch_id = f"batch_{int(time.time())}"
    
    for idx, paper_id in enumerate(paper_ids):
        try:
            paper = Paper.objects.get(paper_id=paper_id, project=project)
            
            # Check if extraction already exists
            existing = Extraction.objects.filter(
                project=project,
                paper=paper,
                schema=schema,
                status__in=['completed', 'verified']
            ).first()
            
            if existing:
                messages.warning(request, f'Extraction already exists for paper "{paper.citation_key or paper.paper_id}" with schema "{schema.name}". Skipped.')
                continue
            
            # Create extraction record
            extraction = Extraction.objects.create(
                project=project,
                paper=paper,
                schema=schema,
                extraction_method=extraction_method,
                status='processing',
                batch_id=batch_id,
                part_index=idx + 1,
                part_total=len(paper_ids),
                created_at=int(time.time() * 1000)
            )
            
            # Run extraction based on method
            try:
                if extraction_method == 'ai':
                    # Use mock AI extraction
                    extracted_data = mock_extract_data(paper, schema)
                    extraction.set_extracted_data(extracted_data)
                    extraction.status = 'completed'
                    extraction.save()
                    success_count += 1
                    
                elif extraction_method == 'manual':
                    # Create empty structure for manual entry
                    extracted_data = manual_extract_data(schema)
                    extraction.set_extracted_data(extracted_data)
                    extraction.status = 'pending'
                    extraction.save()
                    success_count += 1
                    
                elif extraction_method == 'hybrid':
                    # Run AI extraction first, then allow manual review
                    extracted_data = mock_extract_data(paper, schema)
                    extraction.set_extracted_data(extracted_data)
                    extraction.status = 'completed'  # Will need manual verification
                    extraction.save()
                    success_count += 1
                    
            except Exception as e:
                extraction.status = 'failed'
                extraction.error_msg = str(e)
                extraction.save()
                error_count += 1
                
        except Paper.DoesNotExist:
            messages.error(request, f'Paper "{paper_id}" not found!')
            error_count += 1
        except Exception as e:
            messages.error(request, f'Error processing paper "{paper_id}": {str(e)}')
            error_count += 1
    
    # Show results
    if success_count > 0:
        messages.success(request, f'Successfully created {success_count} extraction(s)!')
    if error_count > 0:
        messages.error(request, f'Failed to create {error_count} extraction(s).')
    
    # If manual extraction for single paper, redirect to edit page
    if extraction_method == 'manual' and len(paper_ids) == 1 and success_count == 1:
        # Find the created extraction
        created_extraction = Extraction.objects.filter(
            project=project,
            schema=schema,
            status='pending',
            batch_id=batch_id
        ).first()
        if created_extraction:
            messages.info(request, f'Please fill in the extraction data below.')
            return redirect('extractions:edit', extraction_id=created_extraction.id)
    
    return redirect('dashboard:project-detail', project_id=project_id)


def extraction_detail(request, extraction_id):
    """View extraction details and results"""
    extraction = get_object_or_404(Extraction, id=extraction_id)
    
    # Get extracted data
    extracted_data = extraction.get_extracted_data()
    fields_data = extracted_data.get('fields', {})
    metadata = extracted_data.get('metadata', {})
    
    # Get schema fields with their definitions
    schema_fields = extraction.schema.get_fields() if extraction.schema else []
    
    # Combine schema definitions with extracted values
    fields_with_data = []
    for field_def in schema_fields:
        field_id = field_def.get('field_id')
        field_data = fields_data.get(field_id, {})
        
        fields_with_data.append({
            'definition': field_def,
            'extraction': field_data,
            'field_id': field_id,
        })
    
    context = {
        'extraction': extraction,
        'fields_with_data': fields_with_data,
        'metadata': metadata,
        'extracted_data': extracted_data,
    }
    
    return render(request, 'extractions/detail.html', context)


@require_http_methods(["GET", "POST"])
def extraction_edit(request, extraction_id):
    """Edit extraction data"""
    extraction = get_object_or_404(Extraction, id=extraction_id)
    
    if request.method == 'POST':
        # Get extracted data structure
        extracted_data = extraction.get_extracted_data()
        fields_data = extracted_data.get('fields', {})
        
        # Update field values from form
        for field in extraction.schema.get_fields():
            field_id = field.get('field_id')
            field_type = field.get('field_type', field.get('type', 'text'))  # Support both field_type and type
            
            # Get value from form
            if field_type == 'boolean':
                value = request.POST.get(f'field_{field_id}') == 'true'
            elif field_type == 'multiselect':
                value = request.POST.getlist(f'field_{field_id}')
            elif field_type == 'number':
                value_str = request.POST.get(f'field_{field_id}', '')
                if value_str:
                    try:
                        value = float(value_str) if '.' in value_str else int(value_str)
                    except ValueError:
                        value = None
                else:
                    value = None
            else:
                value = request.POST.get(f'field_{field_id}', '')
            
            # Get confidence score
            confidence_str = request.POST.get(f'confidence_{field_id}', '100')
            try:
                confidence = float(confidence_str) / 100.0  # Convert percentage to 0-1
            except ValueError:
                confidence = 1.0
            
            # Get evidence (证据)
            evidence = request.POST.get(f'evidence_{field_id}', '')
            
            # Update or create field data
            if field_id not in fields_data:
                fields_data[field_id] = {}
            
            fields_data[field_id]['value'] = value
            fields_data[field_id]['field_name'] = field.get('name', field_id)
            fields_data[field_id]['source'] = 'Manual Edit'
            fields_data[field_id]['confidence'] = confidence
            fields_data[field_id]['evidence'] = evidence  # ⭐ Save evidence
        
        # Save updated data
        extracted_data['fields'] = fields_data
        extraction.set_extracted_data(extracted_data)
        
        # Update status and error message
        new_status = request.POST.get('status', extraction.status)
        extraction.status = new_status
        extraction.error_msg = request.POST.get('error_msg', '')
        
        extraction.save()
        
        messages.success(request, 'Extraction data updated successfully!')
        return redirect('extractions:detail', extraction_id=extraction_id)
    
    # GET request - show edit form
    extracted_data = extraction.get_extracted_data()
    fields_data = extracted_data.get('fields', {})
    
    # Prepare field values, confidences, and evidences for template
    field_values = {}
    field_confidences = {}
    field_evidences = {}  # ⭐ New: evidence data
    
    for field_id, field_data in fields_data.items():
        field_values[field_id] = field_data.get('value')
        confidence = field_data.get('confidence', 1.0)
        field_confidences[field_id] = int(confidence * 100)  # Convert to percentage
        field_evidences[field_id] = field_data.get('evidence', '')  # ⭐ Get evidence
    
    context = {
        'extraction': extraction,
        'field_values': field_values,
        'field_confidences': field_confidences,
        'field_evidences': field_evidences,  # ⭐ Pass to template
    }
    
    return render(request, 'extractions/edit.html', context)


@require_POST
@require_POST
def extraction_delete(request, extraction_id):
    """Delete extraction"""
    extraction = get_object_or_404(Extraction, id=extraction_id)
    project_id = extraction.project.project_id if extraction.project else None
    
    extraction.delete()
    
    messages.success(request, 'Extraction deleted successfully!')
    
    if project_id:
        return redirect('dashboard:project-detail', project_id=project_id)
    else:
        return redirect('dashboard:home')


@require_POST
def extraction_verify(request, extraction_id):
    """Mark extraction as verified"""
    extraction = get_object_or_404(Extraction, id=extraction_id)
    
    extraction.mark_verified()
    
    messages.success(request, 'Extraction marked as verified!')
    return redirect('extractions:detail', extraction_id=extraction_id)


# ==================== API Views (for AJAX) ====================

class ExtractionListView(View):
    """API endpoint to list extractions"""
    def get(self, request):
        qs = Extraction.objects.all().values(
            "id",
            "paper_id",
            "project_id",
            "schema_id",
            "status",
            "extraction_method",
            "created_at",
        )
        return JsonResponse({"extractions": list(qs)})


class ExtractionDetailView(View):
    """API endpoint to get extraction details"""
    def get(self, request, extraction_id: int):
        try:
            extraction = Extraction.objects.get(pk=extraction_id)
        except Extraction.DoesNotExist:
            return JsonResponse({"error": "Extraction not found"}, status=404)

        data = {
            "id": extraction.id,
            "paper_id": extraction.paper_id,
            "project_id": extraction.project_id,
            "schema_id": extraction.schema_id,
            "extraction_method": extraction.extraction_method,
            "status": extraction.status,
            "extracted_data": extraction.extracted_data,
            "error_msg": extraction.error_msg,
            "created_at": extraction.created_at,
            "updated_at": extraction.updated_at.isoformat() if extraction.updated_at else None,
        }
        return JsonResponse(data)
