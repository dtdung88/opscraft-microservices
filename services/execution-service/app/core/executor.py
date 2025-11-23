"""Script executor with multiple backend support."""
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional

from app.core.docker_client import ExecutionResult, docker_client

logger = logging.getLogger(__name__)


class ExecutorType(str, Enum):
    """Available execution backends."""

    DOCKER = "docker"
    LOCAL = "local"
    KUBERNETES = "kubernetes"
    AWS_LAMBDA = "aws_lambda"


class BaseExecutor(ABC):
    """Abstract base executor."""

    @abstractmethod
    async def execute(
        self,
        script_content: str,
        script_type: str,
        parameters: dict[str, Any],
        environment: Optional[dict[str, str]] = None,
    ) -> ExecutionResult:
        """Execute script and return result."""
        pass

    @abstractmethod
    async def cancel(self, execution_id: str) -> bool:
        """Cancel running execution."""
        pass


class DockerExecutor(BaseExecutor):
    """Execute scripts in Docker containers."""

    async def execute(
        self,
        script_content: str,
        script_type: str,
        parameters: dict[str, Any],
        environment: Optional[dict[str, str]] = None,
    ) -> ExecutionResult:
        """Execute script in Docker container."""
        # Merge parameters into environment
        env = environment or {}
        for key, value in parameters.items():
            env[f"PARAM_{key.upper()}"] = str(value)

        return await docker_client.execute_script(
            script_content=script_content,
            script_type=script_type,
            environment=env,
        )

    async def cancel(self, execution_id: str) -> bool:
        """Cancel Docker container execution."""
        try:
            container = docker_client.client.containers.get(execution_id)
            container.kill()
            return True
        except Exception as e:
            logger.error(f"Failed to cancel execution {execution_id}: {e}")
            return False


class LocalExecutor(BaseExecutor):
    """Execute scripts locally (for development only)."""

    async def execute(
        self,
        script_content: str,
        script_type: str,
        parameters: dict[str, Any],
        environment: Optional[dict[str, str]] = None,
    ) -> ExecutionResult:
        """Execute script locally using subprocess."""
        import asyncio
        import os
        import time

        start_time = time.time()

        # Build environment
        env = os.environ.copy()
        if environment:
            env.update(environment)
        for key, value in parameters.items():
            env[f"PARAM_{key.upper()}"] = str(value)

        # Determine interpreter
        if script_type == "python":
            cmd = ["python", "-c", script_content]
        elif script_type == "bash":
            cmd = ["bash", "-c", script_content]
        else:
            cmd = ["sh", "-c", script_content]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=300,
            )

            return ExecutionResult(
                exit_code=proc.returncode or 0,
                output=stdout.decode("utf-8", errors="replace"),
                error=stderr.decode("utf-8", errors="replace"),
                duration_ms=int((time.time() - start_time) * 1000),
            )

        except asyncio.TimeoutError:
            proc.kill()
            return ExecutionResult(
                exit_code=-1,
                output="",
                error="Execution timed out",
                duration_ms=int((time.time() - start_time) * 1000),
            )

    async def cancel(self, execution_id: str) -> bool:
        """Local execution cancellation not supported."""
        return False


def get_executor(executor_type: ExecutorType = ExecutorType.DOCKER) -> BaseExecutor:
    """Factory function to get appropriate executor."""
    executors = {
        ExecutorType.DOCKER: DockerExecutor,
        ExecutorType.LOCAL: LocalExecutor,
    }

    executor_class = executors.get(executor_type)
    if not executor_class:
        raise ValueError(f"Unknown executor type: {executor_type}")

    return executor_class()