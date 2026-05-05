#!/usr/bin/env python3
"""
Robin AI - Tor Proxy Module
Handles anonymous routing through the Tor network using SOCKS5h proxy.
All dark web traffic is anonymized via Tor for operational security.
"""

import os
import requests
from typing import Dict, Optional
from fake_useragent import UserAgent


class TorProxy:
    """
    Tor proxy handler for anonymous dark web requests.
    Routes all traffic through Tor's SOCKS5h proxy at 127.0.0.1:9050.
    Uses socks5h:// protocol to ensure DNS resolution happens through Tor.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9050,
        protocol: str = "socks5h",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.timeout = timeout
        self.max_retries = max_retries
        self.proxy_url = f"{protocol}://{host}:{port}"
        self.proxies: Dict[str, str] = {
            "http": self.proxy_url,
            "https": self.proxy_url,
        }
        self.ua = UserAgent()
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session configured with Tor proxy."""
        session = requests.Session()
        session.proxies.update(self.proxies)
        session.headers.update({"User-Agent": self.ua.random})
        session.timeout = self.timeout
        return session

    def check_connection(self) -> tuple:
        """Verify Tor proxy is operational by checking IP through Tor."""
        try:
            resp = self.session.get(
                "https://httpbin.org/ip",
                timeout=self.timeout,
            )
            data = resp.json()
            ip = data.get("origin", "unknown")
            return True, ip
        except Exception as e:
            return False, str(e)

    def renew_identity(self) -> bool:
        """
        Request a new Tor circuit (new IP address).
        Requires Tor ControlPort (9051) with auth configured.
        """
        try:
            import socket
            control = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            control.connect(("127.0.0.1", 9051))
            control.sendall(b"AUTHENTICATE\r\n")
            response = control.recv(128)
            if b"250" in response:
                control.sendall(b"SIGNAL NEWNYM\r\n")
                response = control.recv(128)
                control.close()
                if b"250" in response:
                    self.session = self._create_session()
                    return True
            control.close()
            return False
        except Exception:
            return False

    def get(self, url: str, headers: Optional[Dict] = None, **kwargs) -> requests.Response:
        """Make a GET request through Tor proxy with retry logic."""
        req_headers = {"User-Agent": self.ua.random}
        if headers:
            req_headers.update(headers)

        for attempt in range(self.max_retries):
            try:
                resp = self.session.get(
                    url,
                    headers=req_headers,
                    timeout=kwargs.get("timeout", self.timeout),
                )
                return resp
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                continue

    def post(self, url: str, data: Optional[Dict] = None, headers: Optional[Dict] = None, **kwargs) -> requests.Response:
        """Make a POST request through Tor proxy."""
        req_headers = {"User-Agent": self.ua.random}
        if headers:
            req_headers.update(headers)

        for attempt in range(self.max_retries):
            try:
                resp = self.session.post(
                    url,
                    json=data,
                    headers=req_headers,
                    timeout=kwargs.get("timeout", self.timeout),
                )
                return resp
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                continue


# Singleton instance
default_proxy = None


def get_proxy() -> TorProxy:
    """Get or create the default Tor proxy instance."""
    global default_proxy
    if default_proxy is None:
        default_proxy = TorProxy()
    return default_proxy