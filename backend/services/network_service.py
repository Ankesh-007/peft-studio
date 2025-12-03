"""
Network Service

Monitors network connectivity and provides status information.
"""

import asyncio
import aiohttp
from typing import Optional, Callable, List
from datetime import datetime
from enum import Enum


class NetworkStatus(str, Enum):
    """Network connectivity status"""
    ONLINE = "online"
    OFFLINE = "offline"
    CHECKING = "checking"


class NetworkMonitor:
    """
    Monitors network connectivity status.
    
    Features:
    - Periodic connectivity checks
    - Multiple endpoint testing for reliability
    - Callback notifications on status changes
    - Configurable check interval
    """
    
    def __init__(
        self,
        check_interval: int = 30,
        timeout: int = 5,
        test_urls: Optional[List[str]] = None
    ):
        """
        Initialize network monitor.
        
        Args:
            check_interval: Seconds between connectivity checks
            timeout: Timeout for connectivity tests in seconds
            test_urls: URLs to test connectivity (defaults to common endpoints)
        """
        self.check_interval = check_interval
        self.timeout = timeout
        self.test_urls = test_urls or [
            "https://www.google.com",
            "https://www.cloudflare.com",
            "https://1.1.1.1"
        ]
        
        self._status = NetworkStatus.CHECKING
        self._last_check: Optional[datetime] = None
        self._monitor_task: Optional[asyncio.Task] = None
        self._callbacks: List[Callable] = []
        self._is_monitoring = False
    
    @property
    def status(self) -> NetworkStatus:
        """Get current network status"""
        return self._status
    
    @property
    def is_online(self) -> bool:
        """Check if currently online"""
        return self._status == NetworkStatus.ONLINE
    
    @property
    def is_offline(self) -> bool:
        """Check if currently offline"""
        return self._status == NetworkStatus.OFFLINE
    
    @property
    def last_check(self) -> Optional[datetime]:
        """Get timestamp of last connectivity check"""
        return self._last_check
    
    async def check_connectivity(self) -> bool:
        """
        Check network connectivity by testing multiple endpoints.
        
        Returns:
            True if online, False if offline
        """
        self._last_check = datetime.utcnow()
        
        # Try each test URL
        for url in self.test_urls:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status < 500:  # Any non-server-error response means we're online
                            return True
            except (aiohttp.ClientError, asyncio.TimeoutError):
                continue
        
        return False
    
    async def update_status(self) -> NetworkStatus:
        """
        Update network status by checking connectivity.
        
        Returns:
            Current network status
        """
        old_status = self._status
        self._status = NetworkStatus.CHECKING
        
        is_online = await self.check_connectivity()
        new_status = NetworkStatus.ONLINE if is_online else NetworkStatus.OFFLINE
        
        self._status = new_status
        
        # Notify callbacks if status changed
        if old_status != new_status and old_status != NetworkStatus.CHECKING:
            await self._notify_callbacks(old_status, new_status)
        
        return new_status
    
    def add_callback(self, callback: Callable) -> None:
        """
        Add a callback to be notified of status changes.
        
        Args:
            callback: Async function(old_status, new_status)
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable) -> None:
        """Remove a status change callback"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    async def _notify_callbacks(
        self,
        old_status: NetworkStatus,
        new_status: NetworkStatus
    ) -> None:
        """Notify all callbacks of status change"""
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(old_status, new_status)
                else:
                    callback(old_status, new_status)
            except Exception as e:
                print(f"Error in network status callback: {e}")
    
    async def start_monitoring(self) -> None:
        """Start periodic network monitoring"""
        if self._is_monitoring:
            return
        
        self._is_monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def stop_monitoring(self) -> None:
        """Stop network monitoring"""
        self._is_monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
    
    async def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        while self._is_monitoring:
            try:
                await self.update_status()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in network monitor loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    def get_status_info(self) -> dict:
        """Get detailed status information"""
        return {
            "status": self._status.value,
            "is_online": self.is_online,
            "is_offline": self.is_offline,
            "last_check": self._last_check.isoformat() if self._last_check else None,
            "is_monitoring": self._is_monitoring,
            "check_interval": self.check_interval
        }


# Global instance
_network_monitor: Optional[NetworkMonitor] = None


def get_network_monitor() -> NetworkMonitor:
    """Get or create the global network monitor instance"""
    global _network_monitor
    if _network_monitor is None:
        _network_monitor = NetworkMonitor()
    return _network_monitor
