"""
Network Security Service for Restore app name
Implements network security controls and connection blocking.
"""

import json
import logging
import socket
import urllib.parse
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import re

\
try:
    from utils.path_utils import get_network_security_config_path
except ImportError:
    \
    import sys
    def get_base_dir() -> str:
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
        return os.path.dirname(os.path.dirname(__file__))
    def get_network_security_config_path() -> Path:
        return Path(get_base_dir()) / "config" / "network_security.json"

logger = logging.getLogger(__name__)

class NetworkSecurityService:
    """Service for managing network security and connection blocking"""

    def __init__(self, config_path: str = "config/network_security.json"):
        self.config_path = get_network_security_config_path()
        self.config = self._load_config()
        self.blocked_connections = []
        self.allowed_connections = []

    def _load_config(self) -> Dict:
        """Load network security configuration"""
        if not self.config_path.exists():
            logger.warning(f"Network security config not found: {self.config_path}")
            return self._get_default_config()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load network security config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Get default network security configuration"""
        return {
            "network_security": {
                "enabled": True,
                "block_external_connections": True,
                "allowed_domains": [],
                "blocked_domains": [],
                "allowed_ips": ["127.0.0.1", "localhost", "::1"],
                "blocked_ips": [],
                "allowed_ports": [5000],
                "blocked_ports": []
            }
        }

    def is_connection_allowed(self, host: str, port: int, protocol: str = "tcp") -> Tuple[bool, str]:
        """
        Check if a connection is allowed based on security rules

        Args:
            host: Target hostname or IP
            port: Target port
            protocol: Connection protocol (tcp, udp)

        Returns:
            Tuple of (is_allowed, reason)
        """
        if not self.config.get("network_security", {}).get("enabled", True):
            return True, "Network security disabled"

        if self.config.get("network_security", {}).get("block_external_connections", True):
            if not self._is_local_connection(host):
                return False, f"External connections blocked: {host}"

        if self._is_domain_blocked(host):
            return False, f"Domain blocked: {host}"

        if self._is_ip_blocked(host):
            return False, f"IP blocked: {host}"

        if self._is_port_blocked(port):
            return False, f"Port blocked: {port}"

        if not self._is_domain_allowed(host):
            return False, f"Domain not in allowed list: {host}"

        if not self._is_ip_allowed(host):
            return False, f"IP not in allowed list: {host}"

        if not self._is_port_allowed(port):
            return False, f"Port not in allowed list: {port}"

        return True, "Connection allowed"

    def _is_local_connection(self, host: str) -> bool:
        """Check if connection is to localhost"""
        local_hosts = ["localhost", "127.0.0.1", "::1", "0.0.0.0"]
        return host.lower() in local_hosts

    def _is_domain_blocked(self, host: str) -> bool:
        """Check if domain is in blocked list"""
        blocked_domains = self.config.get("network_security", {}).get("blocked_domains", [])

        for blocked_domain in blocked_domains:
            if blocked_domain.startswith("*"):
                \
                pattern = blocked_domain.replace("*", ".*")
                if re.match(pattern, host):
                    return True
            elif blocked_domain.lower() in host.lower():
                return True

        return False

    def _is_ip_blocked(self, host: str) -> bool:
        """Check if IP is in blocked list"""
        blocked_ips = self.config.get("network_security", {}).get("blocked_ips", [])
        return host in blocked_ips

    def _is_port_blocked(self, port: int) -> bool:
        """Check if port is in blocked list"""
        blocked_ports = self.config.get("network_security", {}).get("blocked_ports", [])
        return port in blocked_ports

    def _is_domain_allowed(self, host: str) -> bool:
        """Check if domain is in allowed list"""
        allowed_domains = self.config.get("network_security", {}).get("allowed_domains", [])

        \
        if not allowed_domains:
            return True

        for allowed_domain in allowed_domains:
            if allowed_domain.startswith("*"):
                \
                pattern = allowed_domain.replace("*", ".*")
                if re.match(pattern, host):
                    return True
            elif allowed_domain.lower() in host.lower():
                return True

        return False

    def _is_ip_allowed(self, host: str) -> bool:
        """Check if IP is in allowed list"""
        allowed_ips = self.config.get("network_security", {}).get("allowed_ips", [])

        \
        if not allowed_ips:
            return True

        return host in allowed_ips

    def _is_port_allowed(self, port: int) -> bool:
        """Check if port is in allowed list"""
        allowed_ports = self.config.get("network_security", {}).get("allowed_ports", [])

        \
        if not allowed_ports:
            return True

        return port in allowed_ports

    def block_connection(self, host: str, port: int, reason: str = ""):
        """Block a connection and log it"""
        self.blocked_connections.append({
            "host": host,
            "port": port,
            "reason": reason,
            "timestamp": self._get_timestamp()
        })

        logger.warning(f"Connection blocked: {host}:{port} - {reason}")

    def allow_connection(self, host: str, port: int, reason: str = ""):
        """Allow a connection and log it"""
        self.allowed_connections.append({
            "host": host,
            "port": port,
            "reason": reason,
            "timestamp": self._get_timestamp()
        })

        logger.info(f"Connection allowed: {host}:{port} - {reason}")

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_security_stats(self) -> Dict:
        """Get network security statistics"""
        return {
            "blocked_connections": len(self.blocked_connections),
            "allowed_connections": len(self.allowed_connections),
            "total_connections": len(self.blocked_connections) + len(self.allowed_connections),
            "block_rate": len(self.blocked_connections) / max(1, len(self.blocked_connections) + len(self.allowed_connections)) * 100
        }

    def is_url_allowed(self, url: str) -> Tuple[bool, str]:
        """Check if URL is allowed to be accessed"""
        try:
            parsed = urllib.parse.urlparse(url)
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)

            return self.is_connection_allowed(host, port)
        except Exception as e:
            return False, f"Invalid URL: {e}"

    def validate_request(self, request_host: str, request_port: int = None) -> Tuple[bool, str]:
        """Validate incoming request"""
        if request_port is None:
            request_port = 5000
        is_allowed, reason = self.is_connection_allowed(request_host, request_port)

        if is_allowed:
            self.allow_connection(request_host, request_port, "Request validation passed")
        else:
            self.block_connection(request_host, request_port, reason)

        return is_allowed, reason

network_security = NetworkSecurityService()
