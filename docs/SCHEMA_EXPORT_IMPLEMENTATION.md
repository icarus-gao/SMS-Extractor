# Schema Export Implementation

## 📊 导出功能实现

### 1. Schema 到 Excel 的映射

```python
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
import json

class SchemaExporter:
    """Schema 数据导出器"""
    
    def __init__(self, schema, extractions):
        self.schema_def = json.loads(schema.fields_definition)
        self.extractions = extractions
    
    def export_to_excel(self, filepath):
        """导出为 Excel 文件"""
        
        wb = openpyxl.Workbook()
        
        # Sheet 1: Data
        self._create_data_sheet(wb)
        
        # Sheet 2: Metadata (可选)
        if self.schema_def.get('export_config', {}).get('include_metadata', True):
            self._create_metadata_sheet(wb)
        
        # Sheet 3: AI Confidence (可选)
        if self.schema_def.get('export_config', {}).get('include_confidence', False):
            self._create_confidence_sheet(wb)
        
        wb.save(filepath)
        return filepath
    
    def _create_data_sheet(self, wb):
        """创建数据表"""
        ws = wb.active
        ws.title = "Data"
        
        # 获取要导出的字段
        export_fields = [
            field for field in self.schema_def['fields']
            if field.get('export', {}).get('enabled', True)
        ]
        
        # 按 order 排序
        export_fields.sort(key=lambda f: f.get('order', 999))
        
        # 1. 写入表头
        self._write_headers(ws, export_fields)
        
        # 2. 写入数据
        self._write_data_rows(ws, export_fields)
        
        # 3. 应用样式
        self._apply_styles(ws, export_fields)
        
        # 4. 调整列宽
        self._adjust_column_widths(ws, export_fields)
        
        # 5. 冻结首行
        ws.freeze_panes = 'A2'
    
    def _write_headers(self, ws, fields):
        """写入表头"""
        for col_idx, field in enumerate(fields, start=1):
            export_config = field.get('export', {})
            column_name = export_config.get('column_name', field['name'])
            
            cell = ws.cell(row=1, column=col_idx)
            cell.value = column_name
            
            # 表头样式
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            cell.alignment = Alignment(horizontal='center', vertical='center')
    
    def _write_data_rows(self, ws, fields):
        """写入数据行"""
        for row_idx, extraction in enumerate(self.extractions, start=2):
            extracted_data = json.loads(extraction.extracted_data)
            
            for col_idx, field in enumerate(fields, start=1):
                field_id = field['field_id']
                field_type = field['type']
                export_config = field.get('export', {})
                
                # 获取值
                value = self._get_field_value(
                    extraction, 
                    extracted_data, 
                    field_id, 
                    field_type
                )
                
                # 格式化值
                formatted_value = self._format_value(
                    value, 
                    field_type, 
                    export_config
                )
                
                # 写入单元格
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.value = formatted_value
                
                # 应用条件格式
                self._apply_conditional_formatting(cell, value, export_config)
    
    def _get_field_value(self, extraction, extracted_data, field_id, field_type):
        """获取字段值"""
        
        # 系统字段（自动）
        if field_type == 'auto':
            if field_id == 'paper_id':
                return extraction.paper.paper_id
            elif field_id == 'citation_key':
                return extraction.paper.citation_key
        
        # 提取的字段
        field_data = extracted_data.get('fields', {}).get(field_id, {})
        return field_data.get('value')
    
    def _format_value(self, value, field_type, export_config):
        """格式化值用于导出"""
        
        if value is None:
            return ""
        
        format_type = export_config.get('format')
        
        # Boolean 类型
        if field_type == 'boolean':
            if format_type == 'yes_no':
                return 'Yes' if value else 'No'
            style = export_config.get('style', {})
            return style.get('true' if value else 'false', {}).get('value', str(value))
        
        # Number 类型
        if field_type == 'number':
            if format_type:
                # 应用数字格式，如 "0.00"
                return float(value)
            return value
        
        # Multi-select 类型
        if field_type == 'multi-select':
            if format_type == 'comma_separated':
                separator = export_config.get('separator', ', ')
                # value 是列表，需要映射到 label
                labels = [self._get_option_label(field_id, v) for v in value]
                return separator.join(labels)
            return value
        
        # Select 类型
        if field_type == 'select':
            if format_type == 'label':
                return self._get_option_label(field_id, value)
            return value
        
        # 默认
        return str(value)
    
    def _get_option_label(self, field_id, value):
        """获取选项的 label"""
        for field in self.schema_def['fields']:
            if field['field_id'] == field_id:
                for option in field.get('options', []):
                    if option['value'] == value:
                        return option['label']
        return value
    
    def _apply_conditional_formatting(self, cell, value, export_config):
        """应用条件格式"""
        style = export_config.get('style', {})
        
        # Boolean 样式
        if isinstance(value, bool):
            bool_style = style.get('true' if value else 'false', {})
            if 'color' in bool_style:
                cell.font = Font(color=bool_style['color'].replace('#', ''))
        
        # 条件格式（如准确率颜色）
        conditional_formatting = style.get('conditional_formatting', [])
        for condition in conditional_formatting:
            if self._evaluate_condition(value, condition['condition']):
                cell.fill = PatternFill(
                    start_color=condition['color'].replace('#', ''),
                    end_color=condition['color'].replace('#', ''),
                    fill_type="solid"
                )
                break
    
    def _evaluate_condition(self, value, condition_str):
        """评估条件表达式"""
        try:
            # 简单的条件评估
            # 如 ">= 95", "< 90"
            if '>=' in condition_str:
                threshold = float(condition_str.split('>=')[1].strip())
                return value >= threshold
            elif '<=' in condition_str:
                threshold = float(condition_str.split('<=')[1].strip())
                return value <= threshold
            elif '>' in condition_str:
                threshold = float(condition_str.split('>')[1].strip())
                return value > threshold
            elif '<' in condition_str:
                threshold = float(condition_str.split('<')[1].strip())
                return value < threshold
            elif '==' in condition_str:
                threshold = float(condition_str.split('==')[1].strip())
                return value == threshold
        except:
            return False
        return False
    
    def _apply_styles(self, ws, fields):
        """应用通用样式"""
        
        # 边框
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        for row in ws.iter_rows():
            for cell in row:
                cell.border = thin_border
                
                # 根据字段配置对齐
                col_idx = cell.column - 1
                if col_idx < len(fields):
                    field = fields[col_idx]
                    align = field.get('export', {}).get('align', 'left')
                    cell.alignment = Alignment(
                        horizontal=align,
                        vertical='top',
                        wrap_text=field.get('export', {}).get('format') == 'wrap_text'
                    )
    
    def _adjust_column_widths(self, ws, fields):
        """调整列宽"""
        for col_idx, field in enumerate(fields, start=1):
            width = field.get('export', {}).get('width', 100)
            # Excel 宽度单位转换（像素到字符）
            excel_width = width / 7
            column_letter = get_column_letter(col_idx)
            ws.column_dimensions[column_letter].width = excel_width
    
    def _create_metadata_sheet(self, wb):
        """创建元数据表"""
        ws = wb.create_sheet("Metadata")
        
        metadata = [
            ("Schema Name", self.schema_def['schema_meta']['name']),
            ("Schema ID", self.schema_def['schema_meta']['schema_id']),
            ("Version", self.schema_def['schema_meta']['version']),
            ("Description", self.schema_def['schema_meta'].get('description', '')),
            ("Export Date", datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            ("Total Papers", len(self.extractions)),
            ("Total Fields", len(self.schema_def['fields'])),
        ]
        
        for row_idx, (key, value) in enumerate(metadata, start=1):
            ws.cell(row=row_idx, column=1, value=key).font = Font(bold=True)
            ws.cell(row=row_idx, column=2, value=value)
        
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 50
    
    def _create_confidence_sheet(self, wb):
        """创建置信度表（可选）"""
        ws = wb.create_sheet("AI Confidence")
        
        # 表头：Paper ID, Field1 Conf, Field2 Conf, ...
        headers = ['Paper ID']
        export_fields = [
            f for f in self.schema_def['fields']
            if f.get('export', {}).get('enabled', True) and f['type'] != 'auto'
        ]
        headers.extend([f['name'] for f in export_fields])
        
        for col_idx, header in enumerate(headers, start=1):
            ws.cell(row=1, column=col_idx, value=header)
        
        # 数据行
        for row_idx, extraction in enumerate(self.extractions, start=2):
            extracted_data = json.loads(extraction.extracted_data)
            
            # Paper ID
            ws.cell(row=row_idx, column=1, value=extraction.paper.paper_id)
            
            # 各字段的置信度
            for col_idx, field in enumerate(export_fields, start=2):
                field_data = extracted_data.get('fields', {}).get(field['field_id'], {})
                confidence = field_data.get('confidence', 0)
                
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.value = confidence
                cell.number_format = '0.00%'
                
                # 置信度颜色
                if confidence >= 0.9:
                    cell.fill = PatternFill(start_color="d4edda", end_color="d4edda", fill_type="solid")
                elif confidence >= 0.7:
                    cell.fill = PatternFill(start_color="fff3cd", end_color="fff3cd", fill_type="solid")
                else:
                    cell.fill = PatternFill(start_color="f8d7da", end_color="f8d7da", fill_type="solid")


class CSVExporter:
    """CSV 导出器"""
    
    def __init__(self, schema, extractions):
        self.schema_def = json.loads(schema.fields_definition)
        self.extractions = extractions
    
    def export_to_csv(self, filepath):
        """导出为 CSV"""
        import csv
        
        export_fields = [
            field for field in self.schema_def['fields']
            if field.get('export', {}).get('enabled', True)
        ]
        export_fields.sort(key=lambda f: f.get('order', 999))
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            
            # 写入表头
            headers = [field.get('export', {}).get('column_name', field['name']) 
                      for field in export_fields]
            writer.writerow(headers)
            
            # 写入数据
            for extraction in self.extractions:
                extracted_data = json.loads(extraction.extracted_data)
                row = []
                
                for field in export_fields:
                    field_id = field['field_id']
                    field_type = field['type']
                    
                    # 获取值
                    if field_type == 'auto':
                        if field_id == 'paper_id':
                            value = extraction.paper.paper_id
                        elif field_id == 'citation_key':
                            value = extraction.paper.citation_key
                    else:
                        field_data = extracted_data.get('fields', {}).get(field_id, {})
                        value = field_data.get('value', '')
                    
                    # 格式化
                    if field_type == 'multi-select' and isinstance(value, list):
                        separator = field.get('export', {}).get('separator', ', ')
                        value = separator.join(value)
                    elif field_type == 'boolean':
                        value = 'Yes' if value else 'No'
                    
                    row.append(value)
                
                writer.writerow(row)
        
        return filepath


class LaTeXExporter:
    """LaTeX 表格导出器"""
    
    def __init__(self, schema, extractions):
        self.schema_def = json.loads(schema.fields_definition)
        self.extractions = extractions
    
    def export_to_latex(self):
        """导出为 LaTeX 表格代码"""
        
        export_fields = [
            field for field in self.schema_def['fields']
            if field.get('export', {}).get('enabled', True)
        ]
        export_fields.sort(key=lambda f: f.get('order', 999))
        
        # 表格列定义
        column_spec = '|'.join(['l'] * len(export_fields))
        column_spec = f"|{column_spec}|"
        
        # 表头
        headers = [field.get('export', {}).get('column_name', field['name']) 
                  for field in export_fields]
        header_row = ' & '.join(headers)
        
        # 数据行
        data_rows = []
        for extraction in self.extractions:
            extracted_data = json.loads(extraction.extracted_data)
            row = []
            
            for field in export_fields:
                field_id = field['field_id']
                field_type = field['type']
                
                if field_type == 'auto':
                    if field_id == 'paper_id':
                        value = extraction.paper.paper_id
                    elif field_id == 'citation_key':
                        value = f"\\cite{{{extraction.paper.citation_key}}}"
                else:
                    field_data = extracted_data.get('fields', {}).get(field_id, {})
                    value = field_data.get('value', '-')
                
                # 转义特殊字符
                value = str(value).replace('&', '\\&').replace('%', '\\%').replace('_', '\\_')
                row.append(value)
            
            data_rows.append(' & '.join(row))
        
        # 生成 LaTeX 代码
        latex_code = f"""
\\begin{{table}}[htbp]
\\centering
\\caption{{{self.schema_def['schema_meta']['name']}}}
\\label{{tab:{self.schema_def['schema_meta']['schema_id']}}}
\\begin{{tabular}}{{{column_spec}}}
\\hline
{header_row} \\\\
\\hline
{chr(10).join([row + ' \\\\' for row in data_rows])}
\\hline
\\end{{tabular}}
\\end{{table}}
"""
        
        return latex_code.strip()
```

---

## 使用示例

```python
# 导出为 Excel
from extractions.exporters import SchemaExporter

schema = Schema.objects.get(schema_id='ml_methods_v1')
extractions = Extraction.objects.filter(
    project=project,
    schema=schema,
    status='verified'
).select_related('paper')

exporter = SchemaExporter(schema, extractions)
filepath = exporter.export_to_excel('/path/to/output.xlsx')

# 导出为 CSV
from extractions.exporters import CSVExporter
csv_exporter = CSVExporter(schema, extractions)
csv_exporter.export_to_csv('/path/to/output.csv')

# 导出为 LaTeX
from extractions.exporters import LaTeXExporter
latex_exporter = LaTeXExporter(schema, extractions)
latex_code = latex_exporter.export_to_latex()
```

---

## 导出配置选项

用户可以在导出时自定义：

```python
export_options = {
    'format': 'excel',  # excel, csv, latex
    'include_metadata': True,
    'include_confidence': True,
    'include_sources': False,
    'selected_fields': ['method_name', 'dataset', 'accuracy'],  # 选择字段
    'filter_status': 'verified',  # 只导出已验证的
    'sort_by': 'paper_id',
    'filename': 'ml_methods_comparison.xlsx'
}
```
