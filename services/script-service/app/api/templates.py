"""Script template marketplace API."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


class TemplateVariable(BaseModel):
    """Variable definition for script templates."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=500)
    default: Optional[str] = None
    required: bool = True
    validation_regex: Optional[str] = None


class ScriptTemplate(BaseModel):
    """Script template definition."""

    id: int
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., max_length=1000)
    category: str
    script_type: str
    template_content: str
    variables: list[TemplateVariable]
    tags: list[str]
    author: str
    downloads: int = 0
    rating: float = 0.0
    is_official: bool = False


class TemplateCreateRequest(BaseModel):
    """Request to create a new template."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., max_length=1000)
    category: str = Field(..., max_length=50)
    script_type: str = Field(..., pattern="^(bash|python|ansible|terraform)$")
    template_content: str = Field(..., min_length=1)
    variables: list[TemplateVariable] = []
    tags: list[str] = []


class UseTemplateRequest(BaseModel):
    """Request to create script from template."""

    variables: dict[str, str] = {}
    script_name: Optional[str] = None


# In-memory storage (replace with database in production)
TEMPLATES: dict[int, ScriptTemplate] = {}
_template_counter = 0


def _get_default_templates() -> list[ScriptTemplate]:
    """Return default built-in templates."""
    return [
        ScriptTemplate(
            id=1,
            name="Health Check Script",
            description="Basic health check script for services",
            category="monitoring",
            script_type="bash",
            template_content="""#!/bin/bash
set -euo pipefail

SERVICE_URL="${service_url}"
TIMEOUT="${timeout:-5}"

echo "Checking health of $SERVICE_URL..."
response=$(curl -sf --max-time "$TIMEOUT" "$SERVICE_URL/health" || echo "failed")

if [ "$response" = "failed" ]; then
    echo "Health check FAILED for $SERVICE_URL"
    exit 1
fi

echo "Health check PASSED: $response"
exit 0
""",
            variables=[
                TemplateVariable(
                    name="service_url",
                    description="URL of the service to check",
                    required=True,
                ),
                TemplateVariable(
                    name="timeout",
                    description="Request timeout in seconds",
                    default="5",
                    required=False,
                ),
            ],
            tags=["health", "monitoring", "curl"],
            author="system",
            downloads=150,
            rating=4.5,
            is_official=True,
        ),
        ScriptTemplate(
            id=2,
            name="Database Backup",
            description="PostgreSQL database backup script",
            category="backup",
            script_type="bash",
            template_content="""#!/bin/bash
set -euo pipefail

DB_HOST="${db_host}"
DB_NAME="${db_name}"
DB_USER="${db_user}"
BACKUP_DIR="${backup_dir:-/tmp/backups}"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_$DATE.sql.gz"

echo "Starting backup of $DB_NAME..."
PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

echo "Backup completed: $BACKUP_FILE"
ls -lh "$BACKUP_FILE"
""",
            variables=[
                TemplateVariable(name="db_host", description="Database host", required=True),
                TemplateVariable(name="db_name", description="Database name", required=True),
                TemplateVariable(name="db_user", description="Database user", required=True),
                TemplateVariable(name="backup_dir", description="Backup directory", default="/tmp/backups", required=False),
            ],
            tags=["backup", "database", "postgresql"],
            author="system",
            downloads=89,
            rating=4.8,
            is_official=True,
        ),
    ]


# Initialize with defaults
for tmpl in _get_default_templates():
    TEMPLATES[tmpl.id] = tmpl
_template_counter = max(TEMPLATES.keys()) if TEMPLATES else 0


@router.get("", response_model=list[ScriptTemplate])
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    script_type: Optional[str] = Query(None, description="Filter by script type"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    official_only: bool = Query(False, description="Show only official templates"),
) -> list[ScriptTemplate]:
    """Browse available script templates."""
    results = list(TEMPLATES.values())

    if category:
        results = [t for t in results if t.category == category]

    if script_type:
        results = [t for t in results if t.script_type == script_type]

    if official_only:
        results = [t for t in results if t.is_official]

    if search:
        search_lower = search.lower()
        results = [
            t for t in results
            if search_lower in t.name.lower()
            or search_lower in t.description.lower()
            or any(search_lower in tag.lower() for tag in t.tags)
        ]

    return sorted(results, key=lambda t: t.downloads, reverse=True)


@router.get("/{template_id}", response_model=ScriptTemplate)
async def get_template(template_id: int) -> ScriptTemplate:
    """Get a specific template by ID."""
    if template_id not in TEMPLATES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )
    return TEMPLATES[template_id]


@router.post("/{template_id}/use")
async def use_template(
    template_id: int,
    request: UseTemplateRequest,
) -> dict:
    """Create script content from template with variable substitution."""
    if template_id not in TEMPLATES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    template = TEMPLATES[template_id]

    # Validate required variables
    for var in template.variables:
        if var.required and var.name not in request.variables:
            if var.default is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required variable: {var.name}",
                )

    # Substitute variables
    content = template.template_content
    for var in template.variables:
        value = request.variables.get(var.name, var.default or "")
        content = content.replace(f"${{{var.name}}}", value)

    # Increment download count
    TEMPLATES[template_id].downloads += 1

    return {
        "name": request.script_name or f"From template: {template.name}",
        "description": f"Created from template: {template.name}",
        "content": content,
        "script_type": template.script_type,
        "tags": template.tags.copy(),
    }


@router.get("/categories/list")
async def list_categories() -> list[str]:
    """Get all available template categories."""
    categories = {t.category for t in TEMPLATES.values()}
    return sorted(categories)