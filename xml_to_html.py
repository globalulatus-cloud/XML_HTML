#!/usr/bin/env python3
"""
Convert medical XML documents to styled HTML.

This script takes an input XML file and converts it to a well-formatted HTML document
with proper styling for medical content, including handling of citations, references,
and special formatting.
"""

import sys
import os
import html as _html
from lxml import etree
from typing import Optional, List, Dict, Any, Sequence

# HTML template with CSS styling
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN", Meiryo, sans-serif;
            line-height: 1.8;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #2c3e50;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            line-height: 1.3;
        }}
        h1 {{ font-size: 2em; border-bottom: 2px solid #eee; padding-bottom: 0.3em; }}
        h2 {{ font-size: 1.7em; border-bottom: 1px solid #eee; padding-bottom: 0.2em; }}
        h3 {{ font-size: 1.4em; }}
        h4 {{ font-size: 1.2em; }}
        p {{
            margin: 0.8em 0;
            text-align: justify;
            text-justify: inter-ideograph;
        }}
        .paragraph {{
            margin-bottom: 1em;
        }}
        .indent-1 {{ margin-left: 2em; }}
        .indent-2 {{ margin-left: 4em; }}
        .bullet::before {{
            content: "• ";
            margin-right: 0.5em;
        }}
        .citation {{ 
            color: #1a5a96;
            text-decoration: underline;
            font-size: 0.9em;
            margin-left: 0.2em;
            cursor: pointer;
        }}
        .citation:hover {{
            color: #0c3b6a;
            text-decoration: underline;
        }}
        .reference {{
            color: #27ae60;
            text-decoration: none;
        }}
        .drug {{
            color: #8e44ad;
            text-decoration: none;
        }}
        .bold {{ font-weight: bold; }}
        .italic {{ font-style: italic; }}
        .underline {{ text-decoration: underline; }}
        /* Removed pseudo class styling as it's no longer needed */
        .subscript {{ vertical-align: sub; font-size: 0.8em; }}
        .superscript {{ vertical-align: super; font-size: 0.8em; }}
        .figure {{
            background-color: #f8f9fa;
            border: 1px solid #eaecf0;
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .figure-label {{
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .separator {{
            color: #7f8c8d;
            margin: 0 0.3em;
        }}
        .content-reference {{
            display: inline-flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.3em;
        }}
        @media print {{
            body {{ 
                font-size: 11pt;
                line-height: 1.6;
                max-width: 100%;
            }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    {content}
</body>
</html>
"""

class XMLToHTMLConverter:
    def __init__(self, input_file: str, output_file: str):
        self.input_file = input_file
        self.output_file = output_file
        self.tree = None
        self.root = None
        self.title = "Document"
        
    def load_xml(self) -> bool:
        """Load and parse the XML file."""
        try:
            parser = etree.XMLParser(remove_blank_text=True)
            self.tree = etree.parse(self.input_file, parser)
            self.root = self.tree.getroot()
            
            # Extract title if available
            heading = self.root.find(".//Heading[@Description]")
            if heading is not None:
                self.title = heading.get("Description")
                
            return True
        except Exception as e:
            print(f"Error loading XML file: {e}", file=sys.stderr)
            return False
    
    def convert_element(self, element: etree._Element) -> str:
        """Convert an XML element to HTML."""
        tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag
        
        # Handle different element types
        if tag == 'Heading':
            return self._convert_heading(element)
        elif tag == 'Paragraph':
            return self._convert_paragraph(element)
        elif tag == 'Text':
            return self._convert_text(element)
        elif tag == 'TextString':
            return self._convert_text_string(element)
        elif tag == 'ContentReferenceGroup':
            return self._convert_content_reference_group(element)
        elif tag == 'GraphicReferenceGroup':
            return self._convert_graphic_reference_group(element)
        elif tag == 'GraphicReference':
            return self._convert_graphic_reference(element)
        elif tag == 'CitationReferenceGroup':
            return self._convert_citation_reference_group(element)
        elif tag == 'CitationReference':
            return self._convert_citation_reference(element)
        elif tag == 'TopicReferenceGroup':
            return self._convert_topic_reference_group(element)
        elif tag == 'TopicReference':
            return self._convert_topic_reference(element)
        elif tag == 'ExternalReference':
            return self._convert_external_reference(element)
        elif tag == 'DrugReference':
            return self._convert_drug_reference(element)
        elif tag == 'GradeReference':
            return self._convert_grade_reference(element)
        elif tag == 'CalculatorReference':
            return self._convert_calculator_reference(element)
        elif tag == 'LineBreak':
            return '<br />'
        elif tag == 'VerticalSpace':
            return '<div style="height: 1em;"></div>'
        else:
            # For unknown elements, process children
            return ''.join(self.convert_element(child) for child in element)
    
    def _convert_heading(self, element: etree._Element) -> str:
        """Convert a heading element to HTML."""
        try:
            level = int(element.get('HeadingLevel', '1'))
        except (ValueError, TypeError):
            level = 1
        # Prefer DescriptionMarkup if present (HTML-escaped), else fall back to Description
        markup = (element.get('DescriptionMarkup') or '').strip()
        if markup:
            text = _html.unescape(markup)
        else:
            text = element.get('Description', '')
        
        # Create appropriate heading level
        if 1 <= level <= 6:
            return f'<h{level} id="H{element.get("HeadingId", "")}">{text}</h{level}>\n'
        return f'<div class="heading">{text}</div>\n'
    
    def _convert_paragraph(self, element: etree._Element) -> str:
        """Convert a paragraph element to HTML."""
        classes = ['paragraph']
        
        # Handle indentation
        indent = element.get('IndentLevel')
        if indent and indent.isdigit():
            indent_level = int(indent)
            if 1 <= indent_level <= 6:
                classes.append(f'indent-{min(indent_level, 3)}')
        
        # Handle bullet points
        if element.get('ShowBullet') == 'true':
            classes.append('bullet')

        # Handle inline formula paragraphs
        if element.get('IsFormula') == 'true':
            classes.append('formula')
        
        # Process paragraph content by delegating each child to convert_element
        content = ''.join(self.convert_element(child) for child in element)
        
        # Handle empty paragraphs
        if not content.strip():
            return '<p>&nbsp;</p>\n'
        return f'<div class="{" ".join(classes)}">{content}</div>\n'
    
    def _convert_text(self, element: etree._Element) -> str:
        """Convert a text element to HTML."""
        return ''.join(self.convert_element(child) for child in element)
    
    def _apply_formatting(self, text: str, tag: str, cls: str = '') -> str:
        """Apply HTML formatting with optional class."""
        if not text.strip():
            return text
            
        if cls:
            return f'<{tag} class="{cls}">{text}</{tag}>'
        return f'<{tag}>{text}</{tag}>'
        
    def _convert_text_string(self, element: etree._Element) -> str:
        """Convert a text string element to HTML."""
        text = element.text or ''
        
        # Handle formatting attributes
        if not text.strip():
            return text
            
        # Apply formatting from innermost to outermost
        if element.get('IsPseudo') == 'true':
            # For pseudo text, just apply bold if specified, don't add any special styling
            if element.get('IsBold') == 'true':
                text = self._apply_formatting(text, 'b')
            return text
            
        # Regular text formatting
        if element.get('IsBold') == 'true':
            text = self._apply_formatting(text, 'b')
            
        if element.get('IsItalic') == 'true' or element.get('IsItalicized') == 'true':
            text = self._apply_formatting(text, 'i')
            
        if element.get('IsUnderline') == 'true':
            text = self._apply_formatting(text, 'u')
            
        if element.get('IsSubscript') == 'true':
            text = self._apply_formatting(text, 'sub')
            
        if element.get('IsSuperscript') == 'true':
            text = self._apply_formatting(text, 'sup')
        
        return text
    
    def _format_citation_range(self, citations: List[str]) -> str:
        """Format a list of citation numbers into ranges (e.g., [1-3] or [1,3-5,7])
        Handles both string numbers and pre-formatted HTML links."""
        if not citations:
            return ""
            
        # Check if we're dealing with HTML links or plain numbers
        is_html = any('<' in c for c in citations)
        
        if is_html:
            # For HTML links, we can't do range formatting, just join with commas
            return ",".join(citations)
            
        try:
            # Convert to integers and sort
            nums = sorted(int(n) for n in citations if n.isdigit())
            if not nums:
                return ""
                
            ranges = []
            start = nums[0]
            
            for i in range(1, len(nums)):
                if nums[i] != nums[i-1] + 1:
                    if start == nums[i-1]:
                        ranges.append(str(start))
                    else:
                        ranges.append(f"{start}-{nums[i-1]}")
                    start = nums[i]
                    
            # Add the last range
            if start == nums[-1]:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{nums[-1]}")
                
            return ",".join(ranges)
        except (ValueError, IndexError):
            # Fallback to simple join if there's any error
            return ",".join(citations)
    
    def _convert_citation_reference_group(self, element: etree._Element) -> str:
        """Convert a citation reference group to HTML.
        
        Always uses the Label attribute if present, otherwise falls back to individual citation numbers.
        Handles both en dash (U+2013) and hyphen (U+002D) in labels.
        """
        label = element.get('Label', '')
        
        # If Label is provided, use it exactly as is
        if label:
            # Normalize en dash to hyphen for the href to ensure links work
            normalized_label = label.replace('–', '-')  # Replace en dash with hyphen
            return f'<a href="#ref-{normalized_label}" class="citation">[{label}]</a>'
            
        # Fallback to individual citation numbers if no Label is provided
        citation_numbers = [ref.get('CitationNumber', '') 
                          for ref in element if ref.tag.endswith('CitationReference')]
        
        if citation_numbers:
            citations = [f'<a href="#ref-{num}" class="citation">{num}</a>' 
                       for num in citation_numbers if num]
            if citations:
                return f'<span class="citation">[{", ".join(citations)}]</span>'
        
        return ''
    
    def _convert_citation_reference(self, element: etree._Element) -> str:
        """Convert a citation reference to HTML."""
        # Inline citations are handled by the parent CitationReferenceGroup
        return ''

    def _convert_topic_reference_group(self, element: etree._Element) -> str:
        """Convert a TopicReferenceGroup to HTML.
        Preserves surrounding text and exposes DisplayTag for QA.
        Example structure:
            <TopicReferenceGroup DisplayTag="2">
              <Text><TextString>(Related Pathway(s): </TextString></Text>
              <TopicReference TopicId="120412" HasQuote="true" />
              <Text><TextString>.)</TextString></Text>
            </TopicReferenceGroup>
        Renders inline, preserving parentheses and spacing.
        """
        display_tag = element.get('DisplayTag', '')
        inner = ''.join(self.convert_element(child) for child in element)
        data_attr = f' data-display-tag="{display_tag}"' if display_tag else ''
        return f'<span class="topic-ref-group"{data_attr}>{inner}</span>'
    
    def _convert_content_reference_group(self, element: etree._Element) -> str:
        """Convert a content reference group to HTML."""
        ref_type = element.get('Type', '')
        separator = element.get('Separator', '、')
        
        # Process all child elements
        refs = []
        citations = []
        
        for child in element:
            if child.tag.endswith('GraphicReferenceGroup'):
                # Handle GraphicReferenceGroup
                label = child.get('Label', '')
                if not label:
                    continue
                    
                # Find the first GraphicReference for the ID
                graphic_ref = next((g for g in child if g.tag.endswith('GraphicReference')), None)
                graphic_id = graphic_ref.get('GraphicId') if graphic_ref is not None else ''
                
                if graphic_id:
                    refs.append(f'<a href="#fig-{graphic_id}" class="graphic-ref">{label}</a>')
                else:
                    refs.append(f'<span class="graphic-ref">{label}</span>')
                    
            elif child.tag.endswith('CitationReferenceGroup'):
                # Handle nested citation references; prefer Label if present
                child_label = (child.get('Label') or '').strip()
                if child_label:
                    citations.append(f'[{child_label}]')
                else:
                    citation_nums = [ref.get('CitationNumber', '').strip()
                                     for ref in child if ref.tag.endswith('CitationReference')]
                    if citation_nums:
                        # Create clickable links for each citation
                        for num in citation_nums:
                            if num:
                                citations.append(f'<a href="#ref-{num}" class="citation">{num}</a>')
        
        # Build the content
        content_parts = []
        
        # Add references if any
        if refs:
            refs_html = f'<span class="content-reference">({separator.join(refs)})</span>'
            content_parts.append(refs_html)
        
        # Add citations if any
        if citations:
            # If we already wrapped labels with brackets, avoid double brackets
            rendered = []
            for c in citations:
                if c.startswith('[') and c.endswith(']'):
                    rendered.append(c)
                else:
                    rendered.append(c)
            formatted_citations = ', '.join(rendered)
            content_parts.append(f'<span class="citation">{formatted_citations}</span>')
        
        # Check for adjacent CitationReferenceGroup
        next_sibling = element.getnext()
        if next_sibling is not None and next_sibling.tag.endswith('CitationReferenceGroup'):
            next_label = (next_sibling.get('Label') or '').strip()
            if next_label:
                content_parts.append(f'<span class="citation">[{next_label}]</span>')
                next_sibling.tag = 'ProcessedCitationReferenceGroup'
            else:
                citation_nums = [ref.get('CitationNumber', '').strip()
                                 for ref in next_sibling if ref.tag.endswith('CitationReference')]
                if citation_nums:
                    citations = [f'<a href="#ref-{num}" class="citation">{num}</a>'
                                 for num in citation_nums if num]
                    if citations:
                        formatted = ", ".join(citations)
                        content_parts.append(f'<span class="citation">[{formatted}]</span>')
                        next_sibling.tag = 'ProcessedCitationReferenceGroup'
        
        return ' '.join(content_parts)
    
    def _convert_graphic_reference_group(self, element: etree._Element) -> str:
        """Convert a graphic reference group to HTML."""
        graphic_type = element.get('Type', 'Figure')
        label = element.get('Label', '')
        graphic_id = ''
        
        # Find the first GraphicReference for the ID
        graphic_ref = next((g for g in element if g.tag.endswith('GraphicReference')), None)
        if graphic_ref is not None:
            graphic_id = graphic_ref.get('GraphicId', '')
        
        # Get the caption if it exists
        caption = ''
        caption_elem = element.find('.//{*}Caption')
        if caption_elem is not None and caption_elem.text:
            caption = caption_elem.text
        
        # Build the figure/algorithm HTML
        html_parts = [f'<div class="graphic-container" id="fig-{graphic_id}">']
        
        # Add the graphic label (e.g., "Figure 1")
        if label:
            html_parts.append(f'<div class="graphic-label">{graphic_type} {label}</div>')
        
        # Add a placeholder for the graphic
        html_parts.append('<div class="graphic-placeholder">[Graphic content]</div>')
        
        # Add the caption if it exists
        if caption:
            html_parts.append(f'<div class="graphic-caption">{caption}</div>')
        
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def _convert_grade_reference(self, element: etree._Element) -> str:
        """Convert a grade reference to HTML.
        
        Example:
            <GradeReference GradeId="2" Label="Grade 1B" />
            Renders as: <a href="#references" class="grade" data-grade-id="2">(Grade 1B)</a>
        """
        grade_id = element.get('GradeId', '')
        label = element.get('Label', f'Grade {grade_id}')  # Fallback to 'Grade X' if no label
        
        return f'<a href="#references" class="grade" data-grade-id="{grade_id}">({label})</a>'

    def _convert_topic_reference(self, element: etree._Element) -> str:
        """Convert a topic reference to HTML.
        
        Example:
            <TopicReference TopicId="564" HasQuote="true"/>
            Renders as: <a href="#topic-564" class="topic-ref">[Topic 564]</a>
        """
        topic_id = element.get('TopicId', '')
        label = f'Topic {topic_id}'

        # Check if this reference is wrapped in parentheses (common pattern in the text)
        has_quote = element.get('HasQuote', '').lower() == 'true'

        # Return just the link, let the surrounding text handle parentheses
        return f'<a href="#topic-{topic_id}" class="topic-ref" data-topic-id="{topic_id}">{label}</a>'

    def _convert_external_reference(self, element: etree._Element) -> str:
        """Convert an external reference to HTML.

        Prefers the visible label if available, otherwise falls back to the Location URL.
        """
        location = (element.get('Location') or '').strip()
        ext_type = (element.get('ExternalReferenceType') or '').strip()

        label = ''
        label_elem = element.find('.//{*}Label')
        if label_elem is not None and (label_elem.text or '').strip():
            label = label_elem.text.strip()
        if not label:
            label = location or 'External Link'

        data_type_attr = f' data-external-type="{ext_type}"' if ext_type else ''

        if location:
            return (
                f'<a href="{location}" class="external-ref" target="_blank" rel="noopener"'
                f'{data_type_attr}>{label}</a>'
            )
        return f'<span class="external-ref"{data_type_attr}>{label}</span>'

    def _convert_drug_reference(self, element: etree._Element) -> str:
        """Convert a drug reference to HTML.

        Example:
            <DrugReference Label="経口プレドニゾン" TopicId="9809">
                <Monograph TopicId="9809"/>
                <Monograph TopicId="10992"/>
                <Monograph TopicId="12725"/>
            </DrugReference>
            Renders as: <a href="#drug-9809" class="drug-ref">経口プレドニゾン</a>
        """
        drug_id = element.get('TopicId', '')
        label = element.get('Label', f'Drug {drug_id}')
        
        # Get all monograph IDs for potential linking
        monographs = [m.get('TopicId') for m in element.findall('.//{*}Monograph')]
        
        # Use the first monograph ID if no topic ID is present
        if not drug_id and monographs:
            drug_id = monographs[0]
            
        if drug_id:
            return f'<a href="#drug-{drug_id}" class="drug-ref" data-drug-id="{drug_id}">{label}</a>'
        return f'<span class="drug-ref">{label}</span>'

    def _convert_calculator_reference(self, element: etree._Element) -> str:
        """Convert a calculator reference to HTML.
        Example:
            <CalculatorReference Label="calculator 1" TopicId="142813"/>
            Renders as: <a href="#calc-142813" class="calculator-ref">calculator 1</a>
        """
        calc_id = element.get('TopicId', '')
        label = element.get('Label', f'Calculator {calc_id}')
        if calc_id:
            return f'<a href="#calc-{calc_id}" class="calculator-ref" data-topic-id="{calc_id}">{label}</a>'
        return f'<span class="calculator-ref">{label}</span>'

    def _convert_graphic_reference(self, element: etree._Element) -> str:
        """Convert a graphic reference to HTML."""
        graphic_id = element.get('GraphicId', '')
        
        # This is a reference to a graphic, not the graphic itself
        # The actual graphic should be in a GraphicReferenceGroup
        return f'<a href="#fig-{graphic_id}" class="graphic-ref">[{graphic_id}]</a>'
    
    def convert(self) -> bool:
        """Convert the XML to HTML."""
        if not self.load_xml():
            return False
        
        # Process the main content
        content_parts = []
        main_content = self.root.find('.//MedicalTopicContent')
        if main_content is not None:
            # Normal case: walk children of MedicalTopicContent
            for child in main_content:
                content_parts.append(self.convert_element(child))
        else:
            # Fallback: no MedicalTopicContent wrapper; process direct children of root
            for child in self.root:
                content_parts.append(self.convert_element(child))
        
        # Combine everything into the HTML template
        html_content = HTML_TEMPLATE.format(
            title=self.title,
            content='\n'.join(content_parts)
        )
        
        # Write the output file
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"Successfully converted {self.input_file} to {self.output_file}")
            return True
        except Exception as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            return False

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.xml|input_dir> <output.html|output_dir>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    if os.path.isdir(input_path):
        if os.path.isfile(output_path):
            print("Error: output path must be a directory when input is a directory.", file=sys.stderr)
            sys.exit(2)
        os.makedirs(output_path, exist_ok=True)

        entries: list[tuple[str, str]] = []
        for root_dir, dirnames, filenames in os.walk(input_path):
            dirnames.sort()
            for name in sorted(filenames):
                lower_name = name.lower()
                if not lower_name.endswith('.xml'):
                    continue
                if lower_name.endswith('_meta.xml'):
                    continue
                full_path = os.path.join(root_dir, name)
                rel_dir = os.path.relpath(root_dir, input_path)
                entries.append((full_path, rel_dir))

        if not entries:
            print(f"No XML files found in {input_path}", file=sys.stderr)
            sys.exit(0)

        had_error = False
        for xml_file, rel_dir in entries:
            base = os.path.splitext(os.path.basename(xml_file))[0]
            out_dir = output_path if rel_dir in ('.', '') else os.path.join(output_path, rel_dir)
            os.makedirs(out_dir, exist_ok=True)
            html_out = os.path.join(out_dir, base + '.html')
            converter = XMLToHTMLConverter(xml_file, html_out)
            if converter.convert():
                print(f"Converted {xml_file} -> {html_out}")
            else:
                had_error = True
        if had_error:
            sys.exit(1)
    else:
        if not os.path.isfile(input_path):
            print(f"Error: Input file '{input_path}' does not exist.", file=sys.stderr)
            sys.exit(1)

        if os.path.isdir(output_path):
            base = os.path.splitext(os.path.basename(input_path))[0]
            html_out = os.path.join(output_path, base + '.html')
        else:
            html_out = output_path
            out_dir = os.path.dirname(html_out)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)

        converter = XMLToHTMLConverter(input_path, html_out)
        if not converter.convert():
            sys.exit(1)

if __name__ == "__main__":
    main()
