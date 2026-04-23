# Utility script for offline HTML/PDF generation from local JSON records.

import json
import os

def generate_tailored_md(data: dict) -> str:
    """Generates consistent Markdown formatting for the resume data."""
    md_lines = []
    resume = data.get("resume", {})

    header = resume.get("header", {})
    full_name = header.get("full_name", "Unknown Name")
    email = header.get("email", "")
    location = header.get("location", "")
    links = header.get("links", [])

    md_lines.append(f"# {full_name}")
    contact_parts = [p for p in [location, email] if p]
    for l in links:
        contact_parts.append(f"[{l}]({l if l.startswith('http') else 'https://'+l})")
    if contact_parts:
        md_lines.append(" | ".join(contact_parts))
    md_lines.append("\n---")

    summary = resume.get("summary", [])
    if summary:
        md_lines.append("\n### SUMMARY")
        for s in summary:
            md_lines.append(f"* {s}")

    def process_section_md(section_data, title_text):
        if not section_data: return
        md_lines.append(f"\n### {title_text}")
        for item in section_data:
            md_lines.append(f"**{item.get('subtitle', '')}** | {item.get('date_range', '')}")
            md_lines.append(f"*{item.get('title', '')}* | {item.get('location', '')}")
            for bullet in item.get("bullets", []):
                md_lines.append(f"* {bullet}")
            md_lines.append("")

    process_section_md(resume.get("education", []), "EDUCATION")
    process_section_md(resume.get("professional_experience", []), "PROFESSIONAL EXPERIENCE")

    skills = resume.get("skills", [])
    if skills:
        md_lines.append("### SKILLS")
        for sg in skills:
            md_lines.append(f"**{sg.get('label', '')}:** {'; '.join(sg.get('items', []))}")
        md_lines.append("")

    process_section_md(resume.get("activities", []), "ACTIVITIES")
    return "\n".join(md_lines).replace("\n\n\n", "\n\n").strip()


def save_html_preview(data: dict, output_path: str):
    """
    Generates an HTML preview with optimized typography, pagination, and layout margins.
    """
    resume = data.get("resume", {})
    
    links_html = []
    for l in resume['header'].get('links', []):
        clean_link = l.replace("https://", "").replace("www.", "")
        links_html.append(f'<a href="{l}">{clean_link}</a>')
    
    contact_parts = []
    if resume['header'].get('location'): contact_parts.append(resume['header'].get('location'))
    if resume['header'].get('email'): contact_parts.append(resume['header'].get('email'))
    contact_parts.extend(links_html)
    
    contact_html = "&nbsp;&nbsp;&bull;&nbsp;&nbsp;".join(contact_parts)

    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <title>Resume - {resume['header'].get('full_name', '')}</title>
    <style>
        :root {{
            --text-main: #2b2b2b;
            --text-light: #555555;
            --line-color: #000000;
        }}
        
        body {{ 
            background-color: #f4f4f4; 
            margin: 0; 
            padding: 40px 20px; 
            font-family: 'EB Garamond', 'Garamond', 'Times New Roman', serif;
            color: var(--text-main);
            line-height: 1.4;
        }}
        
        .page-container {{
            background-color: #ffffff;
            max-width: 820px;
            margin: 0 auto;
            padding: 50px 60px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            box-sizing: border-box;
        }}

        h1 {{ 
            text-align: center; 
            font-size: 26pt; 
            font-weight: normal;
            margin: 0 0 6px 0; 
            text-transform: uppercase; 
            letter-spacing: 2px;
            color: #000;
        }}
        
        .contact-info {{ 
            text-align: center; 
            font-size: 10pt; 
            color: var(--text-light); 
            margin-bottom: 25px; 
            line-height: 1.6; 
        }}
        
        .contact-info a {{ 
            color: var(--text-light); 
            text-decoration: none; 
        }}

        .section-title {{ 
            font-size: 12.5pt; 
            font-weight: bold;
            border-bottom: 1px solid var(--line-color); 
            margin: 20px 0 10px 0; 
            padding-bottom: 3px; 
            text-transform: uppercase; 
            letter-spacing: 1px;
            color: #000;
            break-after: avoid; 
            page-break-after: avoid;
        }}

        .item-block {{ 
            margin-bottom: 14px; 
            break-inside: avoid; 
            page-break-inside: avoid;
        }}
        
        .row-header {{ 
            display: flex; 
            justify-content: space-between; 
            align-items: baseline; 
            font-weight: bold;
            font-size: 11pt;
            margin-bottom: 2px;
        }}
        
        .row-subheader {{ 
            display: flex; 
            justify-content: space-between; 
            align-items: baseline; 
            font-family: 'Georgia', 'Palatino Linotype', 'Book Antiqua', serif;
            font-style: italic;
            /* Core adjustment: Reduced italic font size from 11pt to 10pt */
            font-size: 10pt;
            margin-bottom: 6px;
            color: #333333; 
        }}

        .date, .location {{ font-weight: normal; font-style: normal; }}

        ul {{ margin: 0 0 0 20px; padding: 0; }}
        
        li {{ 
            margin-bottom: 4px; 
            text-align: justify; 
            font-size: 10.5pt;
        }}

        .skills-row {{ 
            margin-bottom: 6px; 
            font-size: 10.5pt;
            line-height: 1.5;
            break-inside: avoid; 
            page-break-inside: avoid;
        }}
        .skills-label {{ font-weight: bold; }}

        @media print {{
            body {{ background-color: transparent; padding: 0; }}
            .page-container {{ box-shadow: none; padding: 0; max-width: 100%; }}
            @page {{ margin: 20mm; }}
        }}
    </style>
    </head>
    <body>
        <div class="page-container">
            <h1>{resume['header'].get('full_name', '')}</h1>
            <div class="contact-info">{contact_html}</div>
            
            <div class="section-title">Summary</div>
            <ul>{"".join([f'<li>{s}</li>' for s in resume.get('summary', [])])}</ul>

            <div class="section-title">Education</div>
            {"".join([f'''
            <div class="item-block">
                <div class="row-header"><span>{e['subtitle']}</span><span class="date">{e['date_range']}</span></div>
                <div class="row-subheader"><span>{e['title']}</span><span class="location">{e['location']}</span></div>
                <ul>{"".join([f'<li>{b}</li>' for b in e.get('bullets', [])])}</ul>
            </div>''' for e in resume.get('education', [])])}

            <div class="section-title">Professional Experience</div>
            {"".join([f'''
            <div class="item-block">
                <div class="row-header"><span>{ex['subtitle']}</span><span class="date">{ex['date_range']}</span></div>
                <div class="row-subheader"><span>{ex['title']}</span><span class="location">{ex['location']}</span></div>
                <ul>{"".join([f'<li>{b}</li>' for b in ex.get('bullets', [])])}</ul>
            </div>''' for ex in resume.get('professional_experience', [])])}

            <div class="section-title">Skills</div>
            {"".join([f'<div class="skills-row"><span class="skills-label">{s["label"]}:</span> {"; ".join(s["items"])}</div>' for s in resume.get('skills', [])])}

            <div class="section-title">Activities</div>
            {"".join([f'''
            <div class="item-block">
                <div class="row-header"><span>{a['subtitle']}</span><span class="date">{a['date_range']}</span></div>
                <div class="row-subheader"><span>{a['title']}</span><span class="location">{a['location']}</span></div>
                <ul>{"".join([f'<li>{b}</li>' for b in a.get('bullets', [])])}</ul>
            </div>''' for a in resume.get('activities', [])])}
        </div>
    </body>
    </html>
    """
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)


if __name__ == "__main__":
    input_file = "runtime/latest_tailored_resume.json"
    md_output = "runtime/tailored_resume_formatted.md"
    html_output = "runtime/tailored_resume_preview.html"

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        md_content = generate_tailored_md(data)
        with open(md_output, "w", encoding="utf-8") as f:
            f.write(md_content)

        save_html_preview(data, html_output)
        print(f"HTML preview generated: {html_output}")

    except FileNotFoundError:
        print(f"Error: File {input_file} not found. Please ensure the data has been generated via the web interface.")