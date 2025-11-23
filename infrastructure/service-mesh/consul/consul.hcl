# Consul Configuration for OpsCraft Service Discovery

datacenter = "opscraft-dc1"
data_dir = "/opt/consul/data"
log_level = "INFO"
node_name = "consul-server-1"
server = true
bootstrap_expect = 1

# UI
ui_config {
  enabled = true
}

# Networking
client_addr = "0.0.0.0"
bind_addr = "0.0.0.0"

addresses {
  http = "0.0.0.0"
  grpc = "0.0.0.0"
}

ports {
  http = 8500
  grpc = 8502
  dns = 8600
}

# Service Mesh (Connect)
connect {
  enabled = true
}

# ACL (Access Control)
acl {
  enabled = true
  default_policy = "deny"
  enable_token_persistence = true
  
  tokens {
    initial_management = "opscraft-management-token"
    agent = "opscraft-agent-token"
  }
}

# Encryption
encrypt = "your-gossip-encryption-key"

# TLS (for production)
# verify_incoming = true
# verify_outgoing = true
# verify_server_hostname = true
# ca_file = "/etc/consul.d/certs/consul-agent-ca.pem"
# cert_file = "/etc/consul.d/certs/dc1-server-consul-0.pem"
# key_file = "/etc/consul.d/certs/dc1-server-consul-0-key.pem"

# Performance
performance {
  raft_multiplier = 1
}

# Telemetry
telemetry {
  prometheus_retention_time = "60s"
  disable_hostname = true
}

# DNS
dns_config {
  allow_stale = true
  max_stale = "87600h"
  service_ttl {
    "*" = "5s"
  }
}