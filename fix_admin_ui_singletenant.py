import os
import glob
import re

tpl_dir = r"C:\Users\Nebyx\Documents\Proyectos web\Municipios\backend\app\templates\admin"

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # 1. Remove the municipality_id form selector
    content = re.sub(r'<form method="get"><select name="municipality_id".*?</select></form>\s*', '', content, flags=re.DOTALL)
    # Some standalone selects
    content = re.sub(r'<select name="municipality_id" class="input" onchange="this\.form\.submit\(\)".*?</select>', '', content, flags=re.DOTALL)
    # dashboard.html and news_categories.html variant
    content = re.sub(r'<select name="municipality_id"[^>]*>.*?\{% endfor %\}</select>', '', content, flags=re.DOTALL)
    content = re.sub(r'<form method="get"><select name="municipality_id" class="input" onchange="this\.form\.submit\(\)"><option value="">.*?\{% endfor %\}</select></form>', '', content, flags=re.DOTALL)

    # 2. Fix the title {% if muni %}...{% endif %}
    content = re.sub(r' \{% if muni %\}· \{\{ muni\.name \}\}\{% endif %\}', '', content)
    content = re.sub(r' \{% if muni %\}\&middot; \{\{ muni\.name \}\}\{% endif %\}', '', content)
    content = re.sub(r' \{% if muni %\}Ã‚Â· \{\{ muni\.name \}\}\{% endif %\}', '', content)
    content = re.sub(r' \{% if muni %\}Â· \{\{ muni\.name \}\}\{% endif %\}', '', content)

    # 3. Fix the + Nuevo buttons
    # From: {% if muni %}<a class="btn btn-primary" href="{{ url_for('admin.event_new', municipality_id=muni.id) }}">+ Nuevo</a>{% endif %}
    # To: <a class="btn btn-primary" href="{{ url_for('admin.event_new') }}">+ Nuevo</a>
    content = re.sub(r'\{% if muni %\}(<a class="btn btn-primary" href="\{\{ url_for\(\'admin\.([^']+)\', municipality_id=muni\.id\) \}\}">.*?</a>)\{% endif %\}', 
                     lambda m: m.group(1).replace(", municipality_id=muni.id", ""), content)

    # Additional variants
    content = re.sub(r', municipality_id=muni\.id', '', content)
    content = re.sub(r', municipality_id=msg\.municipality_id', '', content)
    content = re.sub(r', municipality_id=form\.municipality_id', '', content)
    
    # Remove hidden inputs for municipality_id
    content = re.sub(r'<input type="hidden" name="municipality_id"[^>]*>', '', content)
    
    # User lists: municipality_id display
    content = re.sub(r'<td>\{% for m in municipalities if m\.id==u\.municipality_id %\}\{\{ m\.name \}\}.*?</select></div>', '', content, flags=re.DOTALL)
    
    # Media list upload select
    content = re.sub(r'<div><label class="label">Municipio</label>.*?</div>', '', content, flags=re.DOTALL)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {os.path.basename(filepath)}")

for f in glob.glob(os.path.join(tpl_dir, '*.html')):
    process_file(f)
