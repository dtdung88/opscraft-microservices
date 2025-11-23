"""Secure Docker client for script execution."""
import asyncio
import logging
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Optional

import docker
from docker.errors import APIError, ContainerError, ImageNotFound
from docker.models.containers import Container

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class ExecutionConfig:
    """Configuration for script execution container."""

    image: str
    command: list[str]
    environment: dict[str, str]
    memory_limit: str = "512m"
    cpu_quota: int = 50000
    cpu_period: int = 100000
    timeout: int = 3600
    network_disabled: bool = True
    read_only: bool = True
    user: str = "nobody"


@dataclass
class ExecutionResult:
    """Result of script execution."""

    exit_code: int
    output: str
    error: str
    duration_ms: int
    container_id: Optional[str] = None


class SecureDockerClient:
    """Secure Docker client with isolation and resource limits."""

    SCRIPT_TYPE_IMAGES = {
        "bash": "bash:5-alpine",
        "python": "python:3.12-slim",
        "ansible": "alpine/ansible:latest",
        "terraform": "hashicorp/terraform:latest",
    }

    def __init__(self) -> None:
        self._client: Optional[docker.DockerClient] = None

    def connect(self) -> None:
        """Initialize Docker client."""
        try:
            self._client = docker.from_env()
            self._client.ping()
            logger.info("Docker client connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Docker: {e}")
            raise

    @property
    def client(self) -> docker.DockerClient:
        """Get Docker client instance."""
        if not self._client:
            self.connect()
        return self._client

    def get_image_for_script_type(self, script_type: str) -> str:
        """Get appropriate Docker image for script type."""
        return self.SCRIPT_TYPE_IMAGES.get(script_type, "bash:5-alpine")

    async def execute_script(
        self,
        script_content: str,
        script_type: str,
        environment: Optional[dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> ExecutionResult:
        """Execute script in isolated container."""
        import time

        start_time = time.time()
        container: Optional[Container] = None

        config = ExecutionConfig(
            image=self.get_image_for_script_type(script_type),
            command=self._build_command(script_content, script_type),
            environment=environment or {},
            memory_limit=settings.CONTAINER_MEMORY_LIMIT if hasattr(settings, 'CONTAINER_MEMORY_LIMIT') else "512m",
            timeout=timeout or settings.EXECUTION_TIMEOUT_SECONDS,
        )

        try:
            # Pull image if not present
            await self._ensure_image(config.image)

            # Create and run container
            container = await asyncio.to_thread(
                self._create_container,
                config,
            )

            # Wait for completion with timeout
            exit_code = await asyncio.wait_for(
                asyncio.to_thread(container.wait),
                timeout=config.timeout,
            )

            # Get logs
            output = await asyncio.to_thread(
                container.logs,
                stdout=True,
                stderr=False,
            )
            error = await asyncio.to_thread(
                container.logs,
                stdout=False,
                stderr=True,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            return ExecutionResult(
                exit_code=exit_code.get("StatusCode", -1),
                output=output.decode("utf-8", errors="replace"),
                error=error.decode("utf-8", errors="replace"),
                duration_ms=duration_ms,
                container_id=container.id[:12] if container else None,
            )

        except asyncio.TimeoutError:
            logger.warning(f"Execution timed out after {config.timeout}s")
            if container:
                await asyncio.to_thread(container.kill)
            return ExecutionResult(
                exit_code=-1,
                output="",
                error=f"Execution timed out after {config.timeout} seconds",
                duration_ms=int((time.time() - start_time) * 1000),
            )

        except ContainerError as e:
            logger.error(f"Container error: {e}")
            return ExecutionResult(
                exit_code=e.exit_status,
                output="",
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )

        except Exception as e:
            logger.exception(f"Execution failed: {e}")
            return ExecutionResult(
                exit_code=-1,
                output="",
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )

        finally:
            if container:
                try:
                    await asyncio.to_thread(container.remove, force=True)
                except Exception as e:
                    logger.warning(f"Failed to remove container: {e}")

    def _build_command(self, content: str, script_type: str) -> list[str]:
        """Build command to execute script."""
        if script_type == "python":
            return ["python", "-c", content]
        elif script_type == "bash":
            return ["bash", "-c", content]
        elif script_type == "ansible":
            return ["ansible-playbook", "-i", "localhost,", "-c", "local", "/dev/stdin"]
        else:
            return ["sh", "-c", content]

    def _create_container(self, config: ExecutionConfig) -> Container:
        """Create isolated container with security constraints."""
        return self.client.containers.create(
            image=config.image,
            command=config.command,
            environment=config.environment,
            mem_limit=config.memory_limit,
            cpu_period=config.cpu_period,
            cpu_quota=config.cpu_quota,
            network_disabled=config.network_disabled,
            read_only=config.read_only,
            user=config.user,
            detach=True,
            remove=False,
            security_opt=["no-new-privileges:true"],
            cap_drop=["ALL"],
            pids_limit=100,
        )

    async def _ensure_image(self, image: str) -> None:
        """Pull image if not present locally."""
        try:
            self.client.images.get(image)
        except ImageNotFound:
            logger.info(f"Pulling image: {image}")
            await asyncio.to_thread(self.client.images.pull, image)

    async def stream_logs(
        self,
        container_id: str,
    ) -> AsyncGenerator[str, None]:
        """Stream container logs in real-time."""
        try:
            container = self.client.containers.get(container_id)
            for log in container.logs(stream=True, follow=True):
                yield log.decode("utf-8", errors="replace")
        except Exception as e:
            logger.error(f"Error streaming logs: {e}")
            yield f"Error: {e}"


docker_client = SecureDockerClient()