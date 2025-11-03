from locust import HttpUser, task, between
import random

class OpsCraftUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before starting tasks"""
        # Register user
        username = f"loadtest_{random.randint(1000, 9999)}"
        self.user_data = {
            "username": username,
            "email": f"{username}@example.com",
            "password": "LoadTest123!",
            "full_name": f"Load Test {username}"
        }
        
        self.client.post("/api/v1/auth/register", json=self.user_data)
        
        # Login
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "username": self.user_data["username"],
                "password": self.user_data["password"]
            }
        )
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
    
    @task(3)
    def list_scripts(self):
        """List all scripts"""
        self.client.get("/api/v1/scripts", headers=self.headers)
    
    @task(2)
    def create_script(self):
        """Create a new script"""
        script_name = f"perf_script_{random.randint(1000, 9999)}"
        self.client.post(
            "/api/v1/scripts",
            json={
                "name": script_name,
                "script_type": "bash",
                "content": "echo 'Performance test'",
                "description": "Performance test script"
            },
            headers=self.headers
        )
    
    @task(1)
    def execute_script(self):
        """Execute a script"""
        # Get random script
        response = self.client.get("/api/v1/scripts?limit=10", headers=self.headers)
        
        if response.status_code == 200:
            scripts = response.json()
            if scripts:
                script = random.choice(scripts)
                self.client.post(
                    "/api/v1/executions",
                    json={
                        "script_id": script["id"],
                        "parameters": {}
                    },
                    headers=self.headers
                )
    
    @task(2)
    def list_executions(self):
        """List execution history"""
        self.client.get("/api/v1/executions?limit=20", headers=self.headers)
    
    @task(1)
    def list_secrets(self):
        """List secrets"""
        self.client.get("/api/v1/secrets", headers=self.headers)
    
    @task(1)
    def create_secret(self):
        """Create a secret"""
        secret_name = f"perf_secret_{random.randint(1000, 9999)}"
        self.client.post(
            "/api/v1/secrets",
            json={
                "name": secret_name,
                "value": f"secret_value_{random.randint(1000, 9999)}",
                "category": "api_key"
            },
            headers=self.headers
        )
    
    @task(4)
    def get_current_user(self):
        """Get current user info"""
        self.client.get("/api/v1/auth/me", headers=self.headers)

class AdminUser(HttpUser):
    """Admin-specific load testing"""
    wait_time = between(2, 5)
    
    def on_start(self):
        """Login as admin"""
        # Assume first user is admin
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "Admin123!"
            }
        )
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
    
    @task
    def get_system_stats(self):
        """Get system statistics"""
        self.client.get("/api/v1/admin/stats", headers=self.headers)
    
    @task
    def list_all_users(self):
        """List all users"""
        self.client.get("/api/v1/admin/users", headers=self.headers)