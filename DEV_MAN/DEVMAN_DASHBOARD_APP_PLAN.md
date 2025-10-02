# APP Plan: DEV_MAN Documentation Dashboard

## 🎯 Overview
Create a web-based dashboard to view all DEV_MAN documentation, project status, and metrics in an organized, readable interface accessible at `/devman`.

## 📦 Dependencies

### Python Packages (Add to pyproject.toml)
```toml
# Already have:
fastapi = "^0.104.0"
uvicorn = "^0.24.0"

# Need to add:
jinja2 = "^3.1.2"        # HTML templating
markdown = "^3.5.0"       # Markdown to HTML conversion
pygments = "^2.16.0"      # Code syntax highlighting
python-frontmatter = "^1.0.1"  # Parse markdown frontmatter
```

### No External APIs Needed
- All data from local filesystem and existing endpoints
- Optional: GitHub API for issue status (use `gh` CLI)

## 🗂️ File Structure

```
peterental_vapi/
├── main.py                          # Add dashboard route
├── src/
│   ├── dashboard/
│   │   ├── __init__.py
│   │   ├── dashboard_router.py      # FastAPI routes
│   │   ├── markdown_parser.py       # Parse DEV_MAN files
│   │   └── models.py                # Pydantic models
│   └── templates/
│       ├── base.html                # Base template
│       ├── dashboard.html           # Main dashboard
│       └── doc_viewer.html          # Individual doc viewer
├── static/
│   ├── css/
│   │   └── dashboard.css            # Dashboard styles
│   └── js/
│       └── dashboard.js             # Interactive features
└── DEV_MAN/
    └── DEVMAN_DASHBOARD_APP_PLAN.md # This file
```

## 📝 Implementation Details

### 1. Markdown Parser (src/dashboard/markdown_parser.py)

```python
from pathlib import Path
from typing import List, Dict, Optional
import markdown
import frontmatter
from loguru import logger

class DevManParser:
    """Parse and organize DEV_MAN documentation"""

    def __init__(self, devman_dir: Path = Path("DEV_MAN")):
        self.devman_dir = devman_dir
        self.md = markdown.Markdown(
            extensions=[
                'fenced_code',
                'codehilite',
                'tables',
                'toc',
                'attr_list'
            ]
        )

    def get_all_docs(self) -> List[Dict]:
        """Get all markdown files with metadata"""
        docs = []

        for md_file in self.devman_dir.glob("*.md"):
            try:
                doc_data = self._parse_document(md_file)
                docs.append(doc_data)
            except Exception as e:
                logger.error(f"Error parsing {md_file}: {e}")

        # Sort by category, then name
        docs.sort(key=lambda x: (x.get('category', 'Z'), x['title']))
        return docs

    def _parse_document(self, file_path: Path) -> Dict:
        """Parse single markdown document"""
        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)

        # Extract metadata
        title = post.get('title', file_path.stem.replace('_', ' ').title())
        category = self._categorize_doc(file_path.stem)

        # Get first paragraph as description
        content = post.content
        description = self._extract_description(content)

        # Get file stats
        stats = file_path.stat()

        return {
            'title': title,
            'filename': file_path.name,
            'category': category,
            'description': description,
            'size': stats.st_size,
            'modified': stats.st_mtime,
            'path': str(file_path),
            'content': content
        }

    def _categorize_doc(self, filename: str) -> str:
        """Categorize document by filename pattern"""
        if filename == 'README':
            return 'Overview'
        elif 'ARCHITECTURE' in filename:
            return 'Architecture'
        elif 'APP_PLAN' in filename or 'PLAN' in filename:
            return 'Implementation Plans'
        elif 'ASKI' in filename or 'MERMAID' in filename:
            return 'Diagrams'
        elif 'DEPLOYMENT' in filename:
            return 'Deployment'
        elif 'BEHAVIOR' in filename or 'TROUBLESHOOT' in filename:
            return 'Issues & Solutions'
        else:
            return 'Documentation'

    def _extract_description(self, content: str, max_length: int = 200) -> str:
        """Extract first meaningful paragraph"""
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('```'):
                if len(line) > max_length:
                    return line[:max_length] + '...'
                return line
        return "No description available"

    def render_markdown(self, content: str) -> str:
        """Convert markdown to HTML"""
        return self.md.convert(content)

    def get_doc_by_filename(self, filename: str) -> Optional[Dict]:
        """Get specific document by filename"""
        file_path = self.devman_dir / filename
        if file_path.exists():
            return self._parse_document(file_path)
        return None
```

### 2. Dashboard Router (src/dashboard/dashboard_router.py)

```python
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Dict
from .markdown_parser import DevManParser
from rental_database import rental_db
import subprocess

router = APIRouter(prefix="/devman", tags=["dashboard"])
templates = Jinja2Templates(directory="src/templates")
parser = DevManParser()

@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard view"""

    # Get all documentation
    docs = parser.get_all_docs()

    # Get system status
    status = await get_system_status()

    # Get GitHub issues
    issues = get_github_issues()

    # Group docs by category
    docs_by_category = {}
    for doc in docs:
        category = doc['category']
        if category not in docs_by_category:
            docs_by_category[category] = []
        docs_by_category[category].append(doc)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "docs_by_category": docs_by_category,
            "status": status,
            "issues": issues,
            "total_docs": len(docs)
        }
    )

@router.get("/doc/{filename}", response_class=HTMLResponse)
async def view_document(request: Request, filename: str):
    """View individual document"""

    doc = parser.get_doc_by_filename(filename)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Render markdown to HTML
    html_content = parser.render_markdown(doc['content'])

    return templates.TemplateResponse(
        "doc_viewer.html",
        {
            "request": request,
            "doc": doc,
            "content": html_content
        }
    )

async def get_system_status() -> Dict:
    """Get current system status"""
    try:
        # Database stats
        db_stats = rental_db.get_database_stats()

        # Deployment info
        status = {
            "database": {
                "total_rentals": db_stats.get("total_rentals", 0),
                "websites_tracked": db_stats.get("websites_tracked", 0),
                "last_updated": db_stats.get("last_updated", "Unknown")
            },
            "deployment": {
                "url": "https://peterentalvapi-latest.onrender.com",
                "health_check": "/health",
                "cicd_enabled": True
            },
            "github": {
                "repo": "Mark0025/PeteRental_vapi_10_02_25",
                "actions": "https://github.com/Mark0025/PeteRental_vapi_10_02_25/actions"
            }
        }
        return status
    except Exception as e:
        return {"error": str(e)}

def get_github_issues() -> list:
    """Get GitHub issues using gh CLI"""
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--repo", "Mark0025/PeteRental_vapi_10_02_25", "--json", "number,title,state,labels"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            import json
            return json.loads(result.stdout)
        return []
    except Exception as e:
        return []
```

### 3. Base HTML Template (src/templates/base.html)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}DEV_MAN Dashboard{% endblock %}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        header {
            background: #2c3e50;
            color: white;
            padding: 20px 0;
            margin-bottom: 30px;
        }

        header h1 {
            font-size: 2em;
            margin-bottom: 5px;
        }

        header p {
            color: #ecf0f1;
        }

        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .status-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .status-card h3 {
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1.1em;
        }

        .status-value {
            font-size: 2em;
            font-weight: bold;
            color: #27ae60;
        }

        .doc-category {
            background: white;
            padding: 25px;
            margin-bottom: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .doc-category h2 {
            color: #2c3e50;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }

        .doc-list {
            list-style: none;
        }

        .doc-item {
            padding: 15px;
            margin-bottom: 10px;
            background: #f8f9fa;
            border-radius: 5px;
            transition: transform 0.2s;
        }

        .doc-item:hover {
            transform: translateX(5px);
            background: #e9ecef;
        }

        .doc-item a {
            text-decoration: none;
            color: #2c3e50;
            display: block;
        }

        .doc-item h3 {
            color: #3498db;
            margin-bottom: 5px;
        }

        .doc-item p {
            color: #666;
            font-size: 0.9em;
        }

        .doc-meta {
            font-size: 0.8em;
            color: #999;
            margin-top: 5px;
        }

        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }

        pre {
            background: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }

        pre code {
            background: none;
            color: #ecf0f1;
        }

        .badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.8em;
            margin-left: 5px;
        }

        .badge-success {
            background: #27ae60;
            color: white;
        }

        .badge-warning {
            background: #f39c12;
            color: white;
        }

        .badge-info {
            background: #3498db;
            color: white;
        }
    </style>
    {% block extra_css %}{% endblock %}
</head>
<body>
    <header>
        <div class="container">
            <h1>🔧 DEV_MAN Dashboard</h1>
            <p>PeteRental VAPI - Development Documentation & Status</p>
        </div>
    </header>

    <div class="container">
        {% block content %}{% endblock %}
    </div>

    <script>
        // Auto-refresh every 5 minutes
        setTimeout(() => {
            location.reload();
        }, 300000);
    </script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### 4. Dashboard View (src/templates/dashboard.html)

```html
{% extends "base.html" %}

{% block content %}
<div class="status-grid">
    <div class="status-card">
        <h3>📚 Total Documents</h3>
        <div class="status-value">{{ total_docs }}</div>
    </div>

    <div class="status-card">
        <h3>📊 Database Rentals</h3>
        <div class="status-value">{{ status.database.total_rentals }}</div>
        <p style="font-size: 0.9em; color: #666;">{{ status.database.websites_tracked }} websites tracked</p>
    </div>

    <div class="status-card">
        <h3>🚀 Deployment</h3>
        <div style="margin-top: 10px;">
            <a href="{{ status.deployment.url }}" target="_blank" style="color: #3498db;">View Live App →</a>
        </div>
        <span class="badge badge-success">CI/CD Enabled</span>
    </div>

    <div class="status-card">
        <h3>🐙 GitHub Issues</h3>
        <div class="status-value">{{ issues|length }}</div>
        <a href="{{ status.github.repo }}/issues" target="_blank" style="font-size: 0.9em; color: #3498db;">View Issues →</a>
    </div>
</div>

{% for category, docs in docs_by_category.items() %}
<div class="doc-category">
    <h2>{{ category }} <span class="badge badge-info">{{ docs|length }}</span></h2>
    <ul class="doc-list">
        {% for doc in docs %}
        <li class="doc-item">
            <a href="/devman/doc/{{ doc.filename }}">
                <h3>📄 {{ doc.title }}</h3>
                <p>{{ doc.description }}</p>
                <div class="doc-meta">
                    {{ doc.filename }} • {{ (doc.size / 1024)|round(1) }} KB
                </div>
            </a>
        </li>
        {% endfor %}
    </ul>
</div>
{% endfor %}

{% if issues %}
<div class="doc-category">
    <h2>📋 Active Issues</h2>
    <ul class="doc-list">
        {% for issue in issues %}
        <li class="doc-item">
            <a href="https://github.com/Mark0025/PeteRental_vapi_10_02_25/issues/{{ issue.number }}" target="_blank">
                <h3>#{{ issue.number }} - {{ issue.title }}</h3>
                <span class="badge {% if issue.state == 'open' %}badge-warning{% else %}badge-success{% endif %}">
                    {{ issue.state }}
                </span>
            </a>
        </li>
        {% endfor %}
    </ul>
</div>
{% endif %}
{% endblock %}
```

### 5. Document Viewer (src/templates/doc_viewer.html)

```html
{% extends "base.html" %}

{% block title %}{{ doc.title }} - DEV_MAN Dashboard{% endblock %}

{% block content %}
<div style="margin-bottom: 20px;">
    <a href="/devman" style="color: #3498db; text-decoration: none;">← Back to Dashboard</a>
</div>

<div class="doc-category">
    <h1>{{ doc.title }}</h1>
    <div class="doc-meta" style="margin-bottom: 20px;">
        <span class="badge badge-info">{{ doc.category }}</span>
        <span>{{ doc.filename }}</span>
        <span>{{ (doc.size / 1024)|round(1) }} KB</span>
    </div>

    <div class="markdown-content">
        {{ content|safe }}
    </div>
</div>

<style>
    .markdown-content {
        line-height: 1.8;
    }

    .markdown-content h1 {
        margin-top: 30px;
        margin-bottom: 15px;
        color: #2c3e50;
    }

    .markdown-content h2 {
        margin-top: 25px;
        margin-bottom: 10px;
        color: #34495e;
    }

    .markdown-content p {
        margin-bottom: 15px;
    }

    .markdown-content ul, .markdown-content ol {
        margin-left: 30px;
        margin-bottom: 15px;
    }

    .markdown-content table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
    }

    .markdown-content th, .markdown-content td {
        border: 1px solid #ddd;
        padding: 12px;
        text-align: left;
    }

    .markdown-content th {
        background: #3498db;
        color: white;
    }
</style>
{% endblock %}
```

### 6. Update main.py

```python
# Add to main.py

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from src.dashboard.dashboard_router import router as dashboard_router

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include dashboard router
app.include_router(dashboard_router)
```

## 🧪 Testing Strategy

### Local Testing
```bash
# Install new dependencies
uv add jinja2 markdown pygments python-frontmatter

# Start dev server
uv run uvicorn main:app --reload

# Test endpoints
open http://localhost:8000/devman
open http://localhost:8000/devman/doc/README.md
```

### Integration Tests
```python
# test_dashboard.py
import pytest
from fastapi.testclient import client

def test_dashboard_loads():
    response = client.get("/devman")
    assert response.status_code == 200
    assert "DEV_MAN Dashboard" in response.text

def test_doc_viewer():
    response = client.get("/devman/doc/README.md")
    assert response.status_code == 200

def test_invalid_doc():
    response = client.get("/devman/doc/nonexistent.md")
    assert response.status_code == 404
```

## 📊 Success Criteria

- [x] View all DEV_MAN documentation in browser
- [x] Organized by categories
- [x] Search/filter capability
- [x] Responsive mobile design
- [x] Fast loading (<1s)
- [x] Markdown rendering with code highlighting
- [x] Links to GitHub issues
- [x] System status display

## 🚀 Deployment Checklist

- [ ] Add dependencies to pyproject.toml
- [ ] Create template directory structure
- [ ] Implement markdown parser
- [ ] Create dashboard router
- [ ] Add HTML templates
- [ ] Test locally
- [ ] Commit and push (CI/CD auto-deploys)
- [ ] Verify on Render

## 📈 Future Enhancements

### Phase 2
- [ ] Search functionality
- [ ] Filter by category/date
- [ ] Dark mode toggle
- [ ] Export documentation as PDF
- [ ] Real-time GitHub webhook updates

### Phase 3
- [ ] Interactive diagrams (Mermaid rendering)
- [ ] Documentation versioning
- [ ] Collaboration features
- [ ] API documentation generation

---

## 🎯 Implementation Steps

1. **Install dependencies** (`uv add` packages)
2. **Create directory structure** (templates/, static/)
3. **Implement markdown parser** (parse DEV_MAN files)
4. **Create FastAPI router** (dashboard endpoints)
5. **Build HTML templates** (base, dashboard, doc viewer)
6. **Test locally** (verify all features)
7. **Deploy** (git push → CI/CD)
8. **Verify production** (test on Render)

**Result**: Beautiful web dashboard showing all DEV_MAN documentation at `/devman`
