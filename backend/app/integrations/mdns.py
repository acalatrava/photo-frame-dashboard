"""Advertises the backend as _homehq._tcp so frames can find it on the LAN."""
import logging
import socket

from zeroconf import IPVersion, ServiceInfo, Zeroconf

from ..core.config import APP_VERSION

log = logging.getLogger("homehq.mdns")


def lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


class MdnsAdvertiser:
    def __init__(self, port: int, hostname: str = ""):
        self.port, self.hostname = port, hostname or socket.gethostname()
        self.zc: Zeroconf | None = None
        self.info: ServiceInfo | None = None

    def start(self) -> None:
        ip = lan_ip()
        self.zc = Zeroconf(ip_version=IPVersion.V4Only)
        self.info = ServiceInfo(
            "_homehq._tcp.local.", f"Home HQ ({self.hostname})._homehq._tcp.local.",
            addresses=[socket.inet_aton(ip)], port=self.port,
            properties={"version": APP_VERSION, "api": "/api/v1"}, server=f"{self.hostname}.local.",
        )
        self.zc.register_service(self.info)
        log.info("mDNS: advertising _homehq._tcp on %s:%s", ip, self.port)

    def stop(self) -> None:
        if self.zc and self.info:
            self.zc.unregister_service(self.info)
            self.zc.close()
