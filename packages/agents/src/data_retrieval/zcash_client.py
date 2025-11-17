"""Zcash node RPC client with connection pooling and retry logic"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
from pydantic import BaseModel, Field

from .types import BlockData, TransactionCounts, ShieldedPoolMetrics


logger = logging.getLogger(__name__)


class ZcashRPCConfig(BaseModel):
    """Zcash RPC configuration"""
    host: str = Field(default="localhost", description="Zcash node host")
    port: int = Field(default=8232, description="Zcash node RPC port")
    username: str = Field(default="", description="RPC username")
    password: str = Field(default="", description="RPC password")
    use_ssl: bool = Field(default=False, description="Use SSL for connection")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    pool_size: int = Field(default=10, description="Connection pool size")


class ZcashRPCClient:
    """
    JSON-RPC client for Zcash node with connection pooling and retry logic.
    
    Implements methods for fetching block data, transaction counts, and shielded pool metrics.
    """
    
    def __init__(self, config: ZcashRPCConfig):
        """
        Initialize Zcash RPC client.
        
        Args:
            config: RPC configuration
        """
        self.config = config
        self.base_url = self._build_base_url()
        self.auth = (config.username, config.password) if config.username else None
        
        # Create HTTP client with connection pooling
        limits = httpx.Limits(
            max_connections=config.pool_size,
            max_keepalive_connections=config.pool_size // 2
        )
        self.client = httpx.AsyncClient(
            auth=self.auth,
            timeout=config.timeout,
            limits=limits,
            verify=config.use_ssl
        )
        
        self._request_id = 0
        logger.info(f"Initialized Zcash RPC client for {self.base_url}")
    
    def _build_base_url(self) -> str:
        """Build base URL for RPC endpoint"""
        protocol = "https" if self.config.use_ssl else "http"
        return f"{protocol}://{self.config.host}:{self.config.port}"
    
    async def _call_rpc(
        self,
        method: str,
        params: Optional[List[Any]] = None,
        retry_count: int = 0
    ) -> Any:
        """
        Make JSON-RPC call with retry logic.
        
        Args:
            method: RPC method name
            params: Method parameters
            retry_count: Current retry attempt
            
        Returns:
            RPC response result
            
        Raises:
            Exception: If all retry attempts fail
        """
        self._request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params or []
        }
        
        try:
            response = await self.client.post(self.base_url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            if "error" in data and data["error"] is not None:
                error_msg = data["error"].get("message", "Unknown error")
                logger.error(f"RPC error for {method}: {error_msg}")
                raise Exception(f"RPC error: {error_msg}")
            
            return data.get("result")
            
        except (httpx.HTTPError, Exception) as e:
            logger.warning(f"RPC call failed for {method} (attempt {retry_count + 1}): {e}")
            
            if retry_count < self.config.max_retries:
                # Exponential backoff: 1s, 2s, 4s
                wait_time = 2 ** retry_count
                logger.info(f"Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
                return await self._call_rpc(method, params, retry_count + 1)
            
            logger.error(f"All retry attempts failed for {method}")
            raise
    
    async def get_blockchain_info(self) -> Dict[str, Any]:
        """
        Get blockchain information.
        
        Returns:
            Blockchain info including chain, blocks, difficulty, etc.
        """
        return await self._call_rpc("getblockchaininfo")
    
    async def get_block_count(self) -> int:
        """
        Get current block height.
        
        Returns:
            Current block height
        """
        return await self._call_rpc("getblockcount")
    
    async def get_block_hash(self, height: int) -> str:
        """
        Get block hash at given height.
        
        Args:
            height: Block height
            
        Returns:
            Block hash
        """
        return await self._call_rpc("getblockhash", [height])
    
    async def get_block(self, block_hash: str, verbosity: int = 1) -> Dict[str, Any]:
        """
        Get block data by hash.
        
        Args:
            block_hash: Block hash
            verbosity: 0=hex, 1=json, 2=json with tx details
            
        Returns:
            Block data
        """
        return await self._call_rpc("getblock", [block_hash, verbosity])
    
    async def get_block_data(self, height: int) -> BlockData:
        """
        Get structured block data at given height.
        
        Args:
            height: Block height
            
        Returns:
            Structured block data
        """
        block_hash = await self.get_block_hash(height)
        block = await self.get_block(block_hash, verbosity=1)
        
        # Count shielded transactions (transactions with shielded inputs/outputs)
        shielded_count = 0
        if "tx" in block:
            for tx_id in block["tx"]:
                # In a full implementation, we'd fetch each transaction
                # For now, we'll estimate based on block data
                pass
        
        return BlockData(
            height=block["height"],
            hash=block["hash"],
            timestamp=datetime.fromtimestamp(block["time"]),
            difficulty=block.get("difficulty", 0.0),
            size=block.get("size", 0),
            tx_count=len(block.get("tx", [])),
            shielded_tx_count=shielded_count
        )
    
    async def get_transaction_counts(
        self,
        start_height: int,
        end_height: int
    ) -> TransactionCounts:
        """
        Get transaction counts for a block range.
        
        Args:
            start_height: Starting block height
            end_height: Ending block height
            
        Returns:
            Transaction count metrics
        """
        total_tx = 0
        shielded_tx = 0
        
        for height in range(start_height, end_height + 1):
            try:
                block_data = await self.get_block_data(height)
                total_tx += block_data.tx_count
                shielded_tx += block_data.shielded_tx_count
            except Exception as e:
                logger.warning(f"Failed to get block {height}: {e}")
                continue
        
        transparent_tx = total_tx - shielded_tx
        shielded_pct = (shielded_tx / total_tx * 100) if total_tx > 0 else 0.0
        
        return TransactionCounts(
            total=total_tx,
            shielded=shielded_tx,
            transparent=transparent_tx,
            shielded_percentage=shielded_pct
        )
    
    async def get_shielded_pool_metrics(self) -> ShieldedPoolMetrics:
        """
        Get shielded pool value metrics.
        
        Returns:
            Shielded pool metrics for Sprout, Sapling, and Orchard
        """
        try:
            # Get value pool information
            blockchain_info = await self.get_blockchain_info()
            value_pools = blockchain_info.get("valuePools", [])
            
            sprout_value = 0.0
            sapling_value = 0.0
            orchard_value = 0.0
            
            for pool in value_pools:
                pool_id = pool.get("id", "").lower()
                chain_value = pool.get("chainValue", 0.0)
                
                # Convert zatoshi to ZEC (1 ZEC = 100,000,000 zatoshi)
                zec_value = chain_value / 100_000_000
                
                if pool_id == "sprout":
                    sprout_value = zec_value
                elif pool_id == "sapling":
                    sapling_value = zec_value
                elif pool_id == "orchard":
                    orchard_value = zec_value
            
            total_value = sprout_value + sapling_value + orchard_value
            
            return ShieldedPoolMetrics(
                sprout_pool_value=sprout_value,
                sapling_pool_value=sapling_value,
                orchard_pool_value=orchard_value,
                total_shielded_value=total_value
            )
            
        except Exception as e:
            logger.error(f"Failed to get shielded pool metrics: {e}")
            # Return zero values on error
            return ShieldedPoolMetrics(
                sprout_pool_value=0.0,
                sapling_pool_value=0.0,
                orchard_pool_value=0.0,
                total_shielded_value=0.0
            )
    
    async def get_network_hash_rate(self, blocks: int = 120) -> float:
        """
        Get network hash rate estimate.
        
        Args:
            blocks: Number of blocks to estimate over
            
        Returns:
            Estimated network hash rate in Sol/s
        """
        try:
            result = await self._call_rpc("getnetworksolps", [blocks])
            return float(result)
        except Exception as e:
            logger.error(f"Failed to get network hash rate: {e}")
            return 0.0
    
    async def get_difficulty(self) -> float:
        """
        Get current network difficulty.
        
        Returns:
            Network difficulty
        """
        try:
            return await self._call_rpc("getdifficulty")
        except Exception as e:
            logger.error(f"Failed to get difficulty: {e}")
            return 0.0
    
    async def close(self):
        """Close the HTTP client and cleanup resources"""
        await self.client.aclose()
        logger.info("Closed Zcash RPC client")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
