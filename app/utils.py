def get_resume_html_string(data: dict) -> str:
    """
    Converts structured resume JSON data into a professionally formatted HTML string.
    Features: Optimized typography, print-friendly page-break protection, 
    and robust null-value filtering.
    """
    resume = data.get("resume", {})
    if not resume:
        return ""
        
    header = resume.get("header", {})
    
    # --- 1. Format Contact Information ---
    links_html = []
    for l in header.get('links') or []:
        if l:
            clean_link = l.replace("https://", "").replace("www.", "")
            links_html.append(f'<a href="{l}" target="_blank">{clean_link}</a>')
    
    contact_parts = []
    if header.get('location'): contact_parts.append(header['location'])
    if header.get('email'): contact_parts.append(header['email'])
    contact_parts.extend(links_html)
    contact_html = "&nbsp;&nbsp;&bull;&nbsp;&nbsp;".join(contact_parts)

    # --- 2. Helper function for dynamic section rendering ---
    def build_section(title, items_list):
        if not items_list:
            return ""
        
        section_html = f'<div class="section-title">{title}</div>'
        has_valid_item = False  # Track if any entry contains substantive data
        
        for item in items_list:
            # Sanitize None/null values to empty strings
            subtitle = item.get('subtitle') or ""
            date_range = item.get('date_range') or ""
            item_title = item.get('title') or ""
            location = item.get('location') or ""
            bullets = item.get('bullets') or []
            
            # Skip rendering if the entry is entirely empty
            if not any([subtitle, date_range, item_title, location, bullets]):
                continue
                
            has_valid_item = True
            section_html += '<div class="item-block">'
            
            # Generate header row only if subtitle or date_range is present
            if subtitle or date_range:
                section_html += f'<div class="row-header"><span>{subtitle}</span><span class="date">{date_range}</span></div>'
            
            # Generate subheader row only if title or location is present
            if item_title or location:
                section_html += f'<div class="row-subheader"><span>{item_title}</span><span class="location">{location}</span></div>'
            
            # Filter empty bullet points and render the list
            valid_bullets = [b for b in bullets if b]
            if valid_bullets:
                section_html += f'<ul>{"".join(f"<li>{b}</li>" for b in valid_bullets)}</ul>'
            
            section_html += '</div>'
            
        # Return formatted section only if valid entries were processed
        return section_html if has_valid_item else ""

    # --- 3. Render specific resume modules ---
    
    # Summary Section
    summary = resume.get('summary') or []
    summary_html = ""
    valid_summary = [s for s in summary if s]
    if valid_summary:
        summary_html = f'<div class="section-title">Summary</div><ul>{"".join(f"<li>{s}</li>" for s in valid_summary)}</ul>'

    # Skills Section
    skills = resume.get('skills') or []
    skills_html = ""
    valid_skills = []
    for s in skills:
        label = s.get('label') or ""
        items = s.get('items') or []
        valid_items = [i for i in items if i]
        if label or valid_items:
            valid_skills.append((label, valid_items))
    
    if valid_skills:
        skills_html = '<div class="section-title">Skills</div>'
        for label, items in valid_skills:
            items_str = "; ".join(items)
            label_html = f'<strong>{label}:</strong> ' if label else ""
            skills_html += f'<div class="skills-row">{label_html}{items_str}</div>'

    # Education, Experience, and Activities Section Rendering
    education_html = build_section("Education", resume.get('education'))
    experience_html = build_section("Professional Experience", resume.get('professional_experience'))
    activities_html = build_section("Activities", resume.get('activities'))

    # --- 4. Assemble final HTML document ---
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <style>
        :root {{ --text-main: #2b2b2b; --text-light: #555555; --line-color: #000000; }}
        body {{ 
            background-color: #f4f4f4; margin: 0; padding: 40px 20px; 
            font-family: 'EB Garamond', 'Garamond', 'Georgia', 'Times New Roman', serif;
            color: var(--text-main); line-height: 1.4;
        }}
        .page-container {{
            background-color: #ffffff; max-width: 820px; margin: 0 auto;
            padding: 50px 60px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); box-sizing: border-box;
        }}
        h1 {{ text-align: center; font-size: 26pt; font-weight: normal; margin: 0 0 6px 0; text-transform: uppercase; letter-spacing: 2px; color: #000; }}
        .contact-info {{ text-align: center; font-size: 10pt; color: var(--text-light); margin-bottom: 25px; line-height: 1.6; }}
        .contact-info a {{ color: var(--text-light); text-decoration: none; }}
        .section-title {{ 
            font-size: 12.5pt; font-weight: bold; border-bottom: 1px solid var(--line-color); 
            margin: 20px 0 10px 0; padding-bottom: 3px; text-transform: uppercase; 
            letter-spacing: 1px; color: #000; break-after: avoid; 
        }}
        .item-block {{ margin-bottom: 14px; break-inside: avoid; page-break-inside: avoid; }}
        .row-header {{ display: flex; justify-content: space-between; align-items: baseline; font-weight: bold; font-size: 11pt; margin-bottom: 2px; }}
        .row-subheader {{ 
            display: flex; justify-content: space-between; align-items: baseline; 
            font-family: 'Georgia', serif; font-style: italic; font-size: 10pt; 
            margin-bottom: 6px; color: #333333; 
        }}
        ul {{ margin: 0 0 0 20px; padding: 0; }}
        li {{ margin-bottom: 4px; text-align: justify; font-size: 10.5pt; }}
        .skills-row {{ margin-bottom: 6px; font-size: 10.5pt; line-height: 1.5; break-inside: avoid; }}
        @media print {{
            body {{ background-color: transparent; padding: 0; }}
            .page-container {{ box-shadow: none; padding: 0; max-width: 100%; }}
            @page {{ margin: 20mm; }}
        }}
    </style>
    </head>
    <body>
        <div class="page-container">
            <h1>{header.get('full_name') or ''}</h1>
            <div class="contact-info">{contact_html}</div>
            
            {summary_html}
            {education_html}
            {experience_html}
            {skills_html}
            {activities_html}
        </div>
    </body>
    </html>
    """ 