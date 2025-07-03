#!/usr/bin/env python3
"""
Generate HTML documentation from Markdown files for MCMV Dashboard v5
"""

import os
import markdown
from datetime import datetime

# HTML template with modern styling
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - MCMV Dashboard v5</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        header {{
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            color: white;
            padding: 2rem 0;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }}
        
        header p {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}
        
        nav {{
            background: white;
            padding: 1rem;
            margin-bottom: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        nav ul {{
            list-style: none;
            display: flex;
            gap: 2rem;
            flex-wrap: wrap;
        }}
        
        nav a {{
            color: #3b82f6;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.2s;
        }}
        
        nav a:hover {{
            color: #1e40af;
            text-decoration: underline;
        }}
        
        .content {{
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            margin-top: 2rem;
            margin-bottom: 1rem;
            color: #1e40af;
        }}
        
        h1 {{ font-size: 2rem; }}
        h2 {{ font-size: 1.75rem; }}
        h3 {{ font-size: 1.5rem; }}
        h4 {{ font-size: 1.25rem; }}
        
        code {{
            background: #f3f4f6;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
        }}
        
        pre {{
            background: #1e293b;
            color: #e2e8f0;
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1rem 0;
        }}
        
        pre code {{
            background: none;
            padding: 0;
            color: inherit;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
        }}
        
        th, td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        th {{
            background: #f9fafb;
            font-weight: 600;
            color: #374151;
        }}
        
        tr:hover {{
            background: #f9fafb;
        }}
        
        blockquote {{
            border-left: 4px solid #3b82f6;
            padding-left: 1rem;
            margin: 1rem 0;
            color: #6b7280;
            font-style: italic;
        }}
        
        ul, ol {{
            margin: 1rem 0;
            padding-left: 2rem;
        }}
        
        li {{
            margin: 0.5rem 0;
        }}
        
        .footer {{
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid #e5e7eb;
            text-align: center;
            color: #6b7280;
            font-size: 0.9rem;
        }}
        
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.5rem;
            background: #3b82f6;
            color: white;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 500;
            margin-left: 0.5rem;
        }}
        
        .current-page {{
            font-weight: bold;
            color: #1e40af;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}
            
            header h1 {{
                font-size: 2rem;
            }}
            
            nav ul {{
                flex-direction: column;
                gap: 0.5rem;
            }}
            
            .content {{
                padding: 1rem;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>MCMV Dashboard v5</h1>
            <p>High-Performance Housing Program Monitoring System</p>
        </div>
    </header>
    
    <div class="container">
        <nav>
            <ul>
                <li><a href="index.html" {index_class}>Overview</a></li>
                <li><a href="architecture.html" {architecture_class}>Architecture</a></li>
                <li><a href="implementation.html" {implementation_class}>Implementation Guide</a></li>
                <li><a href="https://github.com/your-repo/dashboard_v5" target="_blank">GitHub ↗</a></li>
            </ul>
        </nav>
        
        <div class="content">
            {content}
        </div>
        
        <div class="footer">
            <p>Generated on {date} | MCMV Dashboard v5 Documentation</p>
        </div>
    </div>
</body>
</html>
"""

def convert_markdown_to_html(md_file, output_file, title, page_name):
    """Convert a markdown file to HTML with styling"""
    
    # Read markdown content
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert markdown to HTML
    md = markdown.Markdown(extensions=[
        'extra',           # Tables, footnotes, etc.
        'codehilite',      # Code syntax highlighting
        'toc',             # Table of contents
        'sane_lists',      # Better list handling
        'smarty',          # Smart quotes
        'meta'             # Metadata
    ])
    
    html_content = md.convert(md_content)
    
    # Determine current page styling
    index_class = 'class="current-page"' if page_name == 'index' else ''
    architecture_class = 'class="current-page"' if page_name == 'architecture' else ''
    implementation_class = 'class="current-page"' if page_name == 'implementation' else ''
    
    # Generate final HTML
    final_html = HTML_TEMPLATE.format(
        title=title,
        content=html_content,
        date=datetime.now().strftime('%Y-%m-%d %H:%M'),
        index_class=index_class,
        architecture_class=architecture_class,
        implementation_class=implementation_class
    )
    
    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    print(f"✅ Generated: {output_file}")

def main():
    """Generate all documentation files"""
    
    # Create docs directory if it doesn't exist
    docs_dir = '/home/ec2-user/pac-mcmv-mvp/dashboard_v5/docs'
    os.makedirs(docs_dir, exist_ok=True)
    
    # Convert each markdown file
    files_to_convert = [
        ('README.md', 'index.html', 'Overview', 'index'),
        ('ARCHITECTURE.md', 'architecture.html', 'Architecture', 'architecture'),
        ('IMPLEMENTATION_GUIDE.md', 'implementation.html', 'Implementation Guide', 'implementation')
    ]
    
    print("🚀 Generating MCMV Dashboard v5 Documentation...")
    print("-" * 50)
    
    for md_file, html_file, title, page_name in files_to_convert:
        md_path = f'/home/ec2-user/pac-mcmv-mvp/dashboard_v5/{md_file}'
        html_path = f'{docs_dir}/{html_file}'
        
        if os.path.exists(md_path):
            convert_markdown_to_html(md_path, html_path, title, page_name)
        else:
            print(f"❌ Warning: {md_path} not found")
    
    print("-" * 50)
    print(f"📁 Documentation generated in: {docs_dir}")
    print(f"🌐 Open {docs_dir}/index.html to view")

if __name__ == "__main__":
    main()