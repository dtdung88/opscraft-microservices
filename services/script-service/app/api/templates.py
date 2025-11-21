from fastapi import APIRouter, Depends, Query
from typing import List, Optional

router = APIRouter()

class ScriptTemplate(BaseModel):
    name: str
    description: str
    category: str
    script_type: ScriptType
    template_content: str
    variables: List[TemplateVariable]
    tags: List[str]
    author: str
    downloads: int
    rating: float

@router.get("/templates", response_model=List[ScriptTemplate])
async def list_templates(
    category: Optional[str] = None,
    script_type: Optional[str] = None,
    search: Optional[str] = None
):
    """Browse script template marketplace"""
    pass

@router.post("/templates/{template_id}/use")
async def create_from_template(
    template_id: int,
    variables: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Create script from template with variable substitution"""
    pass