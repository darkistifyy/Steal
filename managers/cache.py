import asyncio
from typing import Any, Optional


class Cache:
    def __init__(self):
        self.cache_inventory = {}

    def __repr__(self) -> str:
        return str(self.cache_inventory)

    async def do_expiration(self, key: str, expiration: int) -> None:
        await asyncio.sleep(expiration)
        self.cache_inventory.pop(key)

    def get(self, key: str) -> Any:
        """Get the object that is associated with the given key"""
        return self.cache_inventory.get(key)

    async def set(self, key: str, object: Any, expiration: Optional[int] = None) -> Any:
        """Set any object associatng with the given key"""
        self.cache_inventory[key] = object
        if expiration:
            asyncio.ensure_future(self.do_expiration(key, expiration))
        return object

    def remove(self, key: str) -> None:
        """An alias for delete method"""
        return self.delete(key)

    def delete(self, key: str) -> None:
        """Delete a key from the cache"""
        if self.get(key):
            del self.cache_inventory[key]
            return None
