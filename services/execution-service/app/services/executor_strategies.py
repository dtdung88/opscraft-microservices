"""Execution strategy pattern implementation."""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """Context for script execution."""

    script_id: int
    script_content: str
    script_type: str
    parameters: dict[str, Any]
    environment: dict[str, str]
    user: str
    timeout: int = 3600
    require_approval: bool = False


class ExecutionStrategy(ABC):
    """Abstract execution strategy."""

    @abstractmethod
    async def can_execute(self, context: ExecutionContext) -> tuple[bool, str]:
        """Check if execution is allowed."""
        pass

    @abstractmethod
    async def pre_execute(self, context: ExecutionContext) -> None:
        """Pre-execution hooks."""
        pass

    @abstractmethod
    async def post_execute(
        self,
        context: ExecutionContext,
        success: bool,
        result: Any,
    ) -> None:
        """Post-execution hooks."""
        pass


class DefaultExecutionStrategy(ExecutionStrategy):
    """Default execution strategy with basic validation."""

    async def can_execute(self, context: ExecutionContext) -> tuple[bool, str]:
        """Basic validation checks."""
        if not context.script_content:
            return False, "Script content is empty"

        if context.script_type not in ["bash", "python", "ansible", "terraform"]:
            return False, f"Unsupported script type: {context.script_type}"

        return True, "OK"

    async def pre_execute(self, context: ExecutionContext) -> None:
        """Log execution start."""
        logger.info(
            f"Starting execution of script {context.script_id} "
            f"by user {context.user}"
        )

    async def post_execute(
        self,
        context: ExecutionContext,
        success: bool,
        result: Any,
    ) -> None:
        """Log execution result."""
        status = "succeeded" if success else "failed"
        logger.info(
            f"Execution of script {context.script_id} {status}"
        )


class ApprovalRequiredStrategy(ExecutionStrategy):
    """Strategy requiring approval for certain scripts."""

    def __init__(self, approval_service_url: str) -> None:
        self.approval_service_url = approval_service_url

    async def can_execute(self, context: ExecutionContext) -> tuple[bool, str]:
        """Check if approval is required and granted."""
        if not context.require_approval:
            return True, "No approval required"

        # In production, check with approval service
        logger.info(f"Checking approval for script {context.script_id}")
        # Placeholder - would call approval service
        return True, "Approved"

    async def pre_execute(self, context: ExecutionContext) -> None:
        """Record execution attempt."""
        logger.info(f"Pre-execute hook for approved script {context.script_id}")

    async def post_execute(
        self,
        context: ExecutionContext,
        success: bool,
        result: Any,
    ) -> None:
        """Update approval record with result."""
        logger.info(f"Recording result for approved script {context.script_id}")


class RateLimitedStrategy(ExecutionStrategy):
    """Strategy with rate limiting."""

    def __init__(self, max_executions_per_minute: int = 10) -> None:
        self.max_per_minute = max_executions_per_minute
        self._execution_counts: dict[str, list[float]] = {}

    async def can_execute(self, context: ExecutionContext) -> tuple[bool, str]:
        """Check rate limits."""
        import time

        user = context.user
        current_time = time.time()
        minute_ago = current_time - 60

        # Clean old entries
        if user in self._execution_counts:
            self._execution_counts[user] = [
                t for t in self._execution_counts[user]
                if t > minute_ago
            ]
        else:
            self._execution_counts[user] = []

        # Check limit
        if len(self._execution_counts[user]) >= self.max_per_minute:
            return False, f"Rate limit exceeded: {self.max_per_minute}/minute"

        self._execution_counts[user].append(current_time)
        return True, "OK"

    async def pre_execute(self, context: ExecutionContext) -> None:
        """No pre-execution needed."""
        pass

    async def post_execute(
        self,
        context: ExecutionContext,
        success: bool,
        result: Any,
    ) -> None:
        """No post-execution needed."""
        pass