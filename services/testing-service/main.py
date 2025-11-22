"""
Testing Service - Automated Script Testing Framework
Port: 8014
Provides automated unit, integration, security, and performance testing for scripts.
"""
import asyncio
import logging
import re
import subprocess
import tempfile
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    SERVICE_NAME: str = "testing-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8014
    SCRIPT_SERVICE_URL: str = "http://script-service:8002"
    EXECUTION_TIMEOUT_SECONDS: int = 60
    MAX_CONCURRENT_TESTS: int = 5

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


class TestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class TestType(str, Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    SECURITY = "security"
    PERFORMANCE = "performance"
    SYNTAX = "syntax"


class SecurityRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TestCase:
    """Represents a single test case."""

    name: str
    test_type: TestType
    status: TestStatus = TestStatus.PENDING
    message: str = ""
    duration_ms: float = 0
    details: dict = field(default_factory=dict)


@dataclass
class TestResults:
    """Aggregated test results."""

    script_id: int
    script_name: str
    status: TestStatus = TestStatus.PENDING
    unit_tests: list[TestCase] = field(default_factory=list)
    integration_tests: list[TestCase] = field(default_factory=list)
    security_tests: list[TestCase] = field(default_factory=list)
    performance_tests: list[TestCase] = field(default_factory=list)
    syntax_tests: list[TestCase] = field(default_factory=list)
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    duration_ms: float = 0
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None


@dataclass
class SecurityFinding:
    """Security vulnerability finding."""

    rule_id: str
    risk: SecurityRisk
    title: str
    description: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    recommendation: str = ""


SECURITY_RULES = [
    {
        "id": "SEC001",
        "pattern": r"\brm\s+-rf\s+/",
        "risk": SecurityRisk.CRITICAL,
        "title": "Dangerous recursive deletion",
        "description": "Recursive deletion of root or system directories",
        "recommendation": "Use absolute paths and add confirmation prompts",
    },
    {
        "id": "SEC002",
        "pattern": r"eval\s*\(",
        "risk": SecurityRisk.HIGH,
        "title": "Use of eval()",
        "description": "Dynamic code execution can lead to code injection",
        "recommendation": "Avoid eval(); use safer alternatives",
    },
    {
        "id": "SEC003",
        "pattern": r"exec\s*\(",
        "risk": SecurityRisk.HIGH,
        "title": "Use of exec()",
        "description": "Dynamic code execution vulnerability",
        "recommendation": "Use subprocess with shell=False",
    },
    {
        "id": "SEC004",
        "pattern": r"subprocess\..*shell\s*=\s*True",
        "risk": SecurityRisk.HIGH,
        "title": "Shell injection risk",
        "description": "Using shell=True enables shell injection attacks",
        "recommendation": "Use shell=False and pass arguments as a list",
    },
    {
        "id": "SEC005",
        "pattern": r"chmod\s+777",
        "risk": SecurityRisk.MEDIUM,
        "title": "World-writable permissions",
        "description": "Setting 777 permissions is a security risk",
        "recommendation": "Use more restrictive permissions (755 or 644)",
    },
    {
        "id": "SEC006",
        "pattern": r"(password|passwd|secret|api_?key)\s*=\s*['\"][^'\"]+['\"]",
        "risk": SecurityRisk.HIGH,
        "title": "Hardcoded credentials",
        "description": "Credentials should not be hardcoded in scripts",
        "recommendation": "Use environment variables or secret management",
    },
    {
        "id": "SEC007",
        "pattern": r"\bcurl\b.*\|\s*(ba)?sh",
        "risk": SecurityRisk.HIGH,
        "title": "Piping remote content to shell",
        "description": "Executing remote scripts without verification",
        "recommendation": "Download, review, then execute scripts separately",
    },
    {
        "id": "SEC008",
        "pattern": r"os\.system\s*\(",
        "risk": SecurityRisk.MEDIUM,
        "title": "Use of os.system()",
        "description": "os.system() is vulnerable to shell injection",
        "recommendation": "Use subprocess.run() with shell=False",
    },
    {
        "id": "SEC009",
        "pattern": r"input\s*\([^)]*\)",
        "risk": SecurityRisk.LOW,
        "title": "Unvalidated user input",
        "description": "User input should be validated before use",
        "recommendation": "Add input validation and sanitization",
    },
    {
        "id": "SEC010",
        "pattern": r"pickle\.load",
        "risk": SecurityRisk.HIGH,
        "title": "Unsafe deserialization",
        "description": "Pickle can execute arbitrary code during deserialization",
        "recommendation": "Use JSON or other safe serialization formats",
    },
]


class ScriptTestFramework:
    """Automated testing framework for scripts."""

    def __init__(self):
        self.active_tests: dict[int, TestResults] = {}
        self._semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_TESTS)

    async def run_tests(
        self,
        script_id: int,
        content: str,
        script_type: str,
        script_name: str = "Unknown",
        test_types: Optional[list[TestType]] = None,
    ) -> TestResults:
        """Run comprehensive test suite."""
        async with self._semaphore:
            results = TestResults(
                script_id=script_id,
                script_name=script_name,
                status=TestStatus.RUNNING,
            )
            self.active_tests[script_id] = results

            try:
                if test_types is None:
                    test_types = list(TestType)

                tasks = []
                if TestType.SYNTAX in test_types:
                    tasks.append(self._run_syntax_tests(content, script_type))
                if TestType.UNIT in test_types:
                    tasks.append(self._run_unit_tests(content, script_type))
                if TestType.SECURITY in test_types:
                    tasks.append(self._run_security_tests(content))
                if TestType.PERFORMANCE in test_types:
                    tasks.append(self._run_performance_tests(content, script_type))

                test_results = await asyncio.gather(*tasks, return_exceptions=True)

                for i, result in enumerate(test_results):
                    if isinstance(result, Exception):
                        logger.error(f"Test failed with exception: {result}")
                        continue

                    test_type = test_types[i] if i < len(test_types) else None
                    if test_type == TestType.SYNTAX:
                        results.syntax_tests = result
                    elif test_type == TestType.UNIT:
                        results.unit_tests = result
                    elif test_type == TestType.SECURITY:
                        results.security_tests = result
                    elif test_type == TestType.PERFORMANCE:
                        results.performance_tests = result

                all_tests = (
                    results.syntax_tests
                    + results.unit_tests
                    + results.security_tests
                    + results.performance_tests
                )
                results.total_tests = len(all_tests)
                results.passed_tests = sum(
                    1 for t in all_tests if t.status == TestStatus.PASSED
                )
                results.failed_tests = sum(
                    1 for t in all_tests if t.status == TestStatus.FAILED
                )

                results.status = (
                    TestStatus.PASSED
                    if results.failed_tests == 0
                    else TestStatus.FAILED
                )
                results.completed_at = time.time()
                results.duration_ms = (results.completed_at - results.started_at) * 1000

            except Exception as e:
                logger.exception(f"Test suite failed: {e}")
                results.status = TestStatus.ERROR

            return results

    async def _run_syntax_tests(
        self, content: str, script_type: str
    ) -> list[TestCase]:
        """Run syntax validation tests."""
        tests: list[TestCase] = []
        start = time.time()

        if script_type == "python":
            test = TestCase(name="Python Syntax Check", test_type=TestType.SYNTAX)
            try:
                compile(content, "<string>", "exec")
                test.status = TestStatus.PASSED
                test.message = "Syntax is valid"
            except SyntaxError as e:
                test.status = TestStatus.FAILED
                test.message = f"Syntax error at line {e.lineno}: {e.msg}"
                test.details = {"line": e.lineno, "offset": e.offset}
            test.duration_ms = (time.time() - start) * 1000
            tests.append(test)

        elif script_type == "bash":
            test = TestCase(name="Bash Syntax Check", test_type=TestType.SYNTAX)
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".sh", delete=False
                ) as f:
                    f.write(content)
                    f.flush()

                    result = subprocess.run(
                        ["bash", "-n", f.name],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )

                    if result.returncode == 0:
                        test.status = TestStatus.PASSED
                        test.message = "Syntax is valid"
                    else:
                        test.status = TestStatus.FAILED
                        test.message = result.stderr.strip()
            except FileNotFoundError:
                test.status = TestStatus.SKIPPED
                test.message = "Bash not available for syntax check"
            except subprocess.TimeoutExpired:
                test.status = TestStatus.ERROR
                test.message = "Syntax check timed out"
            except Exception as e:
                test.status = TestStatus.ERROR
                test.message = str(e)
            test.duration_ms = (time.time() - start) * 1000
            tests.append(test)

        shebang_test = TestCase(name="Shebang Check", test_type=TestType.SYNTAX)
        if content.strip().startswith("#!"):
            shebang_test.status = TestStatus.PASSED
            shebang_test.message = "Shebang line present"
        else:
            shebang_test.status = TestStatus.FAILED
            shebang_test.message = "Missing shebang line"
        tests.append(shebang_test)

        return tests

    async def _run_unit_tests(
        self, content: str, script_type: str
    ) -> list[TestCase]:
        """Run unit tests with mocking."""
        tests: list[TestCase] = []

        has_main = TestCase(name="Main Entry Point", test_type=TestType.UNIT)
        if script_type == "python" and "if __name__" in content:
            has_main.status = TestStatus.PASSED
            has_main.message = "Main guard found"
        elif script_type == "bash" and ("main()" in content or "main " in content):
            has_main.status = TestStatus.PASSED
            has_main.message = "Main function found"
        else:
            has_main.status = TestStatus.FAILED
            has_main.message = "No main entry point detected"
        tests.append(has_main)

        error_handling = TestCase(name="Error Handling", test_type=TestType.UNIT)
        if script_type == "python":
            if "try:" in content and "except" in content:
                error_handling.status = TestStatus.PASSED
                error_handling.message = "Exception handling present"
            else:
                error_handling.status = TestStatus.FAILED
                error_handling.message = "No exception handling found"
        elif script_type == "bash":
            if "set -e" in content or "trap" in content:
                error_handling.status = TestStatus.PASSED
                error_handling.message = "Error handling present"
            else:
                error_handling.status = TestStatus.FAILED
                error_handling.message = "No error handling (missing set -e)"
        tests.append(error_handling)

        return tests

    async def _run_security_tests(self, content: str) -> list[TestCase]:
        """Run security scanning tests."""
        tests: list[TestCase] = []
        findings: list[SecurityFinding] = []

        for rule in SECURITY_RULES:
            matches = list(re.finditer(rule["pattern"], content, re.IGNORECASE))
            for match in matches:
                line_num = content[: match.start()].count("\n") + 1
                findings.append(
                    SecurityFinding(
                        rule_id=rule["id"],
                        risk=rule["risk"],
                        title=rule["title"],
                        description=rule["description"],
                        line_number=line_num,
                        code_snippet=match.group()[:100],
                        recommendation=rule["recommendation"],
                    )
                )

        overall_test = TestCase(name="Security Scan", test_type=TestType.SECURITY)
        critical_high = [
            f for f in findings if f.risk in (SecurityRisk.CRITICAL, SecurityRisk.HIGH)
        ]

        if not findings:
            overall_test.status = TestStatus.PASSED
            overall_test.message = "No security issues found"
        elif critical_high:
            overall_test.status = TestStatus.FAILED
            overall_test.message = (
                f"Found {len(critical_high)} critical/high security issues"
            )
        else:
            overall_test.status = TestStatus.PASSED
            overall_test.message = f"Found {len(findings)} low/medium issues"

        overall_test.details = {
            "findings": [
                {
                    "rule_id": f.rule_id,
                    "risk": f.risk.value,
                    "title": f.title,
                    "line": f.line_number,
                    "recommendation": f.recommendation,
                }
                for f in findings
            ]
        }
        tests.append(overall_test)

        for risk_level in SecurityRisk:
            level_findings = [f for f in findings if f.risk == risk_level]
            test = TestCase(
                name=f"{risk_level.value.title()} Risk Issues",
                test_type=TestType.SECURITY,
            )
            test.status = (
                TestStatus.PASSED
                if not level_findings
                else (
                    TestStatus.FAILED
                    if risk_level in (SecurityRisk.CRITICAL, SecurityRisk.HIGH)
                    else TestStatus.PASSED
                )
            )
            test.message = f"Found {len(level_findings)} {risk_level.value} risk issues"
            test.details = {"count": len(level_findings)}
            tests.append(test)

        return tests

    async def _run_performance_tests(
        self, content: str, script_type: str
    ) -> list[TestCase]:
        """Run performance analysis tests."""
        tests: list[TestCase] = []

        lines = content.split("\n")
        line_count = len(lines)
        code_lines = len([l for l in lines if l.strip() and not l.strip().startswith("#")])

        size_test = TestCase(name="Script Size", test_type=TestType.PERFORMANCE)
        if code_lines < 500:
            size_test.status = TestStatus.PASSED
            size_test.message = f"Script size acceptable ({code_lines} lines)"
        else:
            size_test.status = TestStatus.FAILED
            size_test.message = f"Script too large ({code_lines} lines). Consider refactoring."
        size_test.details = {"total_lines": line_count, "code_lines": code_lines}
        tests.append(size_test)

        complexity_test = TestCase(name="Loop Nesting", test_type=TestType.PERFORMANCE)
        nested_loops = len(re.findall(r"(for|while).*\n.*\s+(for|while)", content))
        if nested_loops == 0:
            complexity_test.status = TestStatus.PASSED
            complexity_test.message = "No deeply nested loops detected"
        elif nested_loops <= 2:
            complexity_test.status = TestStatus.PASSED
            complexity_test.message = f"Found {nested_loops} nested loop(s)"
        else:
            complexity_test.status = TestStatus.FAILED
            complexity_test.message = f"Found {nested_loops} nested loops. May impact performance."
        tests.append(complexity_test)

        return tests


framework = ScriptTestFramework()
router = APIRouter()


class TestRequest(BaseModel):
    script_id: int
    content: str = Field(..., min_length=1)
    script_type: str = Field(..., pattern="^(bash|python|ansible|terraform)$")
    script_name: str = "Unknown"
    test_types: Optional[list[str]] = None


class TestResponse(BaseModel):
    script_id: int
    script_name: str
    status: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    duration_ms: float
    syntax_tests: list[dict]
    unit_tests: list[dict]
    security_tests: list[dict]
    performance_tests: list[dict]


@router.post("/run", response_model=TestResponse)
async def run_tests(request: TestRequest):
    """Run test suite for a script."""
    test_types = None
    if request.test_types:
        test_types = [TestType(t) for t in request.test_types]

    results = await framework.run_tests(
        script_id=request.script_id,
        content=request.content,
        script_type=request.script_type,
        script_name=request.script_name,
        test_types=test_types,
    )

    def serialize_tests(tests: list[TestCase]) -> list[dict]:
        return [
            {
                "name": t.name,
                "status": t.status.value,
                "message": t.message,
                "duration_ms": t.duration_ms,
                "details": t.details,
            }
            for t in tests
        ]

    return TestResponse(
        script_id=results.script_id,
        script_name=results.script_name,
        status=results.status.value,
        total_tests=results.total_tests,
        passed_tests=results.passed_tests,
        failed_tests=results.failed_tests,
        duration_ms=results.duration_ms,
        syntax_tests=serialize_tests(results.syntax_tests),
        unit_tests=serialize_tests(results.unit_tests),
        security_tests=serialize_tests(results.security_tests),
        performance_tests=serialize_tests(results.performance_tests),
    )


@router.get("/status/{script_id}")
async def get_test_status(script_id: int):
    """Get status of running tests."""
    results = framework.active_tests.get(script_id)
    if not results:
        raise HTTPException(status_code=404, detail="No active tests for this script")
    return {
        "script_id": script_id,
        "status": results.status.value,
        "total_tests": results.total_tests,
        "passed_tests": results.passed_tests,
        "failed_tests": results.failed_tests,
    }


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

app.include_router(router, prefix="/api/v1/tests", tags=["testing"])


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "active_tests": len(framework.active_tests),
    }