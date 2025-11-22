from fastapi import APIRouter, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.models.script import ScriptType

router = APIRouter()


class TemplateVariable(BaseModel):
    name: str
    description: str
    default: Optional[str] = None
    required: bool = True


class ScriptTemplate(BaseModel):
    name: str
    description: str
    category: str
    script_type: str
    template_content: str
    variables: List[TemplateVariable]
    tags: List[str]
    author: str
    downloads: int
    rating: float


# In-memory template storage (in production, use database)
TEMPLATES: List[ScriptTemplate] = []


@router.get("/templates", response_model=List[ScriptTemplate])
async def list_templates(
    category: Optional[str] = None,
    script_type: Optional[str] = None,
    search: Optional[str] = None
):
    """Browse script template marketplace"""
    results = TEMPLATES

    if category:
        results = [t for t in results if t.category == category]

    if script_type:
        results = [t for t in results if t.script_type == script_type]

    if search:
        search_lower = search.lower()
        results = [
            t for t in results
            if search_lower in t.name.lower() or search_lower in t.description.lower()
        ]

    return results


@router.post("/templates/{template_id}/use")
async def create_from_template(
    template_id: int,
    variables: Dict[str, Any]
):
    """Create script from template with variable substitution"""
    if template_id >= len(TEMPLATES):
        return {"error": "Template not found"}

    template = TEMPLATES[template_id]
    content = template.template_content

    for var_name, var_value in variables.items():
        content = content.replace(f"${{{var_name}}}", str(var_value))

    return {
        "name": f"From template: {template.name}",
        "content": content,
        "script_type": template.script_type
    }