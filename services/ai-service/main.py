"""
AI Service - Script Analysis and Suggestions
Port: 8011
Provides AI-powered script analysis, security scanning, and optimization suggestions.
"""
import asyncio
import logging
import re
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    SERVICE_NAME: str = "ai-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8011
    MODEL_CACHE_SIZE: int = 100
    ANALYSIS_TIMEOUT_SECONDS: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SuggestionType(str, Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    BEST_PRACTICE = "best_practice"
    READABILITY = "readability"


@dataclass
class SecurityPattern:
    pattern: str
    description: str
    risk_level: RiskLevel
    suggestion: str


@dataclass
class Suggestion:
    type: SuggestionType
    title: str
    description: str
    line_number: Optional[int] = None
    original_code: Optional[str] = None
    suggested_code: Optional[str] = None
    priority: int = 5


@dataclass
class AnalysisResult:
    security_score: float = 0.0
    quality_score: float = 0.0
    performance_score: float = 0.0
    overall_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    suggestions: list[Suggestion] = field(default_factory=list)
    security_issues: list[dict] = field(default_factory=list)
    best_practices: list[str] = field(default_factory=list)


SECURITY_PATTERNS: list[SecurityPattern] = [
    SecurityPattern(
        pattern=r"\brm\s+-rf\s+/",
        description="Recursive deletion of root directory",
        risk_level=RiskLevel.CRITICAL,
        suggestion="Avoid rm -rf with root path. Use specific paths.",
    ),
    SecurityPattern(
        pattern=r":()\{\s*:\|\:&\s*\};:",
        description="Fork bomb detected",
        risk_level=RiskLevel.CRITICAL,
        suggestion="Remove fork bomb pattern.",
    ),
    SecurityPattern(
        pattern=r"\bdd\s+if=/dev/",
        description="Direct disk device access",
        risk_level=RiskLevel.HIGH,
        suggestion="Avoid direct disk access unless necessary.",
    ),
    SecurityPattern(
        pattern=r"\beval\s*\(",
        description="Dynamic code execution with eval",
        risk_level=RiskLevel.HIGH,
        suggestion="Avoid eval(); use safer alternatives.",
    ),
    SecurityPattern(
        pattern=r"\bexec\s*\(",
        description="Dynamic code execution with exec",
        risk_level=RiskLevel.HIGH,
        suggestion="Avoid exec(); use subprocess with shell=False.",
    ),
    SecurityPattern(
        pattern=r"subprocess\..*shell\s*=\s*True",
        description="Shell injection vulnerability",
        risk_level=RiskLevel.HIGH,
        suggestion="Use shell=False and pass arguments as list.",
    ),
    SecurityPattern(
        pattern=r"\bchmod\s+777\b",
        description="World-writable permissions",
        risk_level=RiskLevel.MEDIUM,
        suggestion="Use more restrictive permissions (e.g., 755 or 644).",
    ),
    SecurityPattern(
        pattern=r"password\s*=\s*['\"][^'\"]+['\"]",
        description="Hardcoded password detected",
        risk_level=RiskLevel.HIGH,
        suggestion="Use environment variables or secret management.",
    ),
    SecurityPattern(
        pattern=r"api[_-]?key\s*=\s*['\"][^'\"]+['\"]",
        description="Hardcoded API key detected",
        risk_level=RiskLevel.HIGH,
        suggestion="Use environment variables or secret management.",
    ),
    SecurityPattern(
        pattern=r"\bcurl\s+.*\|\s*bash",
        description="Piping curl to bash",
        risk_level=RiskLevel.HIGH,
        suggestion="Download script first, review, then execute.",
    ),
    SecurityPattern(
        pattern=r"\bwget\s+.*\|\s*sh",
        description="Piping wget to shell",
        risk_level=RiskLevel.HIGH,
        suggestion="Download script first, review, then execute.",
    ),
    SecurityPattern(
        pattern=r"os\.system\s*\(",
        description="Using os.system for command execution",
        risk_level=RiskLevel.MEDIUM,
        suggestion="Use subprocess.run() with shell=False instead.",
    ),
]

BASH_BEST_PRACTICES = [
    ("set -e", "Add 'set -e' to exit on first error"),
    ("set -u", "Add 'set -u' to treat unset variables as errors"),
    ("set -o pipefail", "Add 'set -o pipefail' for pipeline error handling"),
    ('#!/bin/bash', "Include proper shebang"),
]

PYTHON_BEST_PRACTICES = [
    ("if __name__", "Add main guard: if __name__ == '__main__'"),
    ("import logging", "Use logging instead of print for production"),
    ("try:", "Add proper exception handling"),
    ("with open", "Use context managers for file operations"),
]


class ScriptAnalyzer:
    """AI-powered script analysis and suggestions."""

    def __init__(self):
        self._analysis_cache: dict[str, AnalysisResult] = {}

    async def analyze_script(
        self, content: str, script_type: str
    ) -> AnalysisResult:
        """Comprehensive script analysis."""
        cache_key = f"{hash(content)}:{script_type}"
        if cache_key in self._analysis_cache:
            return self._analysis_cache[cache_key]

        security_result = await self._analyze_security(content)
        quality_result = await self._analyze_quality(content, script_type)
        suggestions = await self._generate_suggestions(content, script_type)
        best_practices = await self._check_best_practices(content, script_type)

        overall = (
            security_result["score"] * 0.4
            + quality_result["score"] * 0.3
            + (100 - len(suggestions) * 5) * 0.3
        )

        result = AnalysisResult(
            security_score=security_result["score"],
            quality_score=quality_result["score"],
            performance_score=quality_result.get("performance", 80.0),
            overall_score=max(0, min(100, overall)),
            risk_level=security_result["risk_level"],
            suggestions=suggestions,
            security_issues=security_result["issues"],
            best_practices=best_practices,
        )

        if len(self._analysis_cache) < settings.MODEL_CACHE_SIZE:
            self._analysis_cache[cache_key] = result

        return result

    async def _analyze_security(self, content: str) -> dict:
        """Analyze script for security vulnerabilities."""
        issues: list[dict] = []
        max_risk = RiskLevel.LOW
        risk_weights = {
            RiskLevel.LOW: 5,
            RiskLevel.MEDIUM: 15,
            RiskLevel.HIGH: 30,
            RiskLevel.CRITICAL: 50,
        }
        total_penalty = 0

        for pattern in SECURITY_PATTERNS:
            matches = list(re.finditer(pattern.pattern, content, re.IGNORECASE))
            for match in matches:
                line_num = content[: match.start()].count("\n") + 1
                issues.append({
                    "pattern": pattern.description,
                    "risk_level": pattern.risk_level.value,
                    "line": line_num,
                    "suggestion": pattern.suggestion,
                    "matched_text": match.group()[:50],
                })
                total_penalty += risk_weights[pattern.risk_level]
                if risk_weights[pattern.risk_level] > risk_weights[max_risk]:
                    max_risk = pattern.risk_level

        score = max(0, 100 - total_penalty)
        return {"score": score, "risk_level": max_risk, "issues": issues}

    async def _analyze_quality(self, content: str, script_type: str) -> dict:
        """Analyze code quality metrics."""
        lines = content.split("\n")
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = sum(
            1 for line in lines
            if line.strip().startswith("#") or line.strip().startswith("//")
        )
        code_lines = total_lines - blank_lines - comment_lines

        comment_ratio = comment_lines / max(code_lines, 1)
        long_lines = sum(1 for line in lines if len(line) > 120)
        long_line_ratio = long_lines / max(total_lines, 1)

        quality_score = 100.0
        if comment_ratio < 0.1:
            quality_score -= 10
        if long_line_ratio > 0.1:
            quality_score -= 15
        if total_lines > 500:
            quality_score -= 10

        functions = len(re.findall(r"\bdef\s+\w+|function\s+\w+|\w+\s*\(\)\s*\{", content))
        if functions == 0 and code_lines > 50:
            quality_score -= 15

        performance_score = 100.0
        if re.search(r"for.*for.*for", content):
            performance_score -= 20
        if re.search(r"while\s+True|while\s+1", content):
            performance_score -= 10

        return {
            "score": max(0, quality_score),
            "performance": max(0, performance_score),
            "metrics": {
                "total_lines": total_lines,
                "code_lines": code_lines,
                "comment_ratio": round(comment_ratio, 2),
                "functions": functions,
            },
        }

    async def _generate_suggestions(
        self, content: str, script_type: str
    ) -> list[Suggestion]:
        """Generate improvement suggestions."""
        suggestions: list[Suggestion] = []

        for pattern in SECURITY_PATTERNS:
            if re.search(pattern.pattern, content, re.IGNORECASE):
                suggestions.append(Suggestion(
                    type=SuggestionType.SECURITY,
                    title=pattern.description,
                    description=pattern.suggestion,
                    priority=1 if pattern.risk_level == RiskLevel.CRITICAL else 2,
                ))

        if script_type == "bash":
            if "set -e" not in content:
                suggestions.append(Suggestion(
                    type=SuggestionType.BEST_PRACTICE,
                    title="Missing error handling",
                    description="Add 'set -euo pipefail' at the beginning",
                    suggested_code="set -euo pipefail",
                    priority=3,
                ))
            if not content.strip().startswith("#!"):
                suggestions.append(Suggestion(
                    type=SuggestionType.BEST_PRACTICE,
                    title="Missing shebang",
                    description="Add proper shebang line",
                    suggested_code="#!/usr/bin/env bash",
                    priority=4,
                ))

        if script_type == "python":
            if "import logging" not in content and "print(" in content:
                suggestions.append(Suggestion(
                    type=SuggestionType.BEST_PRACTICE,
                    title="Consider using logging",
                    description="Replace print statements with logging",
                    priority=5,
                ))
            if "if __name__" not in content:
                suggestions.append(Suggestion(
                    type=SuggestionType.BEST_PRACTICE,
                    title="Missing main guard",
                    description="Add if __name__ == '__main__' guard",
                    suggested_code="if __name__ == '__main__':\n    main()",
                    priority=4,
                ))

        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                suggestions.append(Suggestion(
                    type=SuggestionType.READABILITY,
                    title="Line too long",
                    description=f"Line {i} exceeds 120 characters",
                    line_number=i,
                    priority=6,
                ))

        return sorted(suggestions, key=lambda s: s.priority)

    async def _check_best_practices(
        self, content: str, script_type: str
    ) -> list[str]:
        """Check adherence to best practices."""
        followed: list[str] = []

        practices = (
            BASH_BEST_PRACTICES if script_type == "bash" else PYTHON_BEST_PRACTICES
        )
        for check, description in practices:
            if check in content:
                followed.append(description)

        return followed


class AnalyzeRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1_000_000)
    script_type: str = Field(..., pattern="^(bash|python|ansible|terraform)$")


class AnalyzeResponse(BaseModel):
    security_score: float
    quality_score: float
    performance_score: float
    overall_score: float
    risk_level: str
    suggestions: list[dict]
    security_issues: list[dict]
    best_practices: list[str]


analyzer = ScriptAnalyzer()
router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_script(request: AnalyzeRequest):
    """Analyze script for security, quality, and best practices."""
    try:
        result = await asyncio.wait_for(
            analyzer.analyze_script(request.content, request.script_type),
            timeout=settings.ANALYSIS_TIMEOUT_SECONDS,
        )
        return AnalyzeResponse(
            security_score=result.security_score,
            quality_score=result.quality_score,
            performance_score=result.performance_score,
            overall_score=result.overall_score,
            risk_level=result.risk_level.value,
            suggestions=[
                {
                    "type": s.type.value,
                    "title": s.title,
                    "description": s.description,
                    "line_number": s.line_number,
                    "suggested_code": s.suggested_code,
                    "priority": s.priority,
                }
                for s in result.suggestions
            ],
            security_issues=result.security_issues,
            best_practices=result.best_practices,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Analysis timed out",
        )
    except Exception as e:
        logger.exception("Analysis failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
    yield
    logger.info(f"Shutting down {settings.SERVICE_NAME}")


app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1/ai", tags=["ai"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.SERVICE_NAME}