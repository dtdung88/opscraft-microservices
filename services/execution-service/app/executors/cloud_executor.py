from abc import ABC, abstractmethod

class CloudExecutor(ABC):
    @abstractmethod
    async def execute(self, script: Script, params: dict):
        pass

class AWSLambdaExecutor(CloudExecutor):
    async def execute(self, script: Script, params: dict):
        """Execute script on AWS Lambda"""
        pass

class GCPCloudRunExecutor(CloudExecutor):
    async def execute(self, script: Script, params: dict):
        """Execute script on Google Cloud Run"""
        pass

class AzureFunctionsExecutor(CloudExecutor):
    async def execute(self, script: Script, params: dict):
        """Execute script on Azure Functions"""
        pass