"""Example usage of Data Retrieval Agent"""
import asyncio
import logging
from datetime import datetime

from ..config import load_config
from ..messaging.connection import ConnectionPool
from .agent import DataRetrievalAgent
from .zcash_client import ZcashRPCConfig
from .types import DataRetrievalRequest


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Example main function"""
    # Load configuration
    config = load_config()
    
    # Create connection pool
    connection_pool = ConnectionPool(config.rabbitmq)
    
    # Configure Zcash RPC (optional, uses defaults if not provided)
    zcash_config = ZcashRPCConfig(
        host="localhost",
        port=8232,
        username="",
        password="",
        use_ssl=False
    )
    
    # Create Data Retrieval Agent
    agent = DataRetrievalAgent(
        connection_pool=connection_pool,
        config=config,
        zcash_config=zcash_config,
        # Add API credentials from environment or config
        # twitter_token=os.getenv("TWITTER_BEARER_TOKEN"),
        # reddit_client_id=os.getenv("REDDIT_CLIENT_ID"),
        # reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        # github_token=os.getenv("GITHUB_ACCESS_TOKEN"),
    )
    
    try:
        # Initialize agent
        await agent.initialize()
        
        logger.info("Data Retrieval Agent started")
        
        # Start consuming messages
        agent.start_consuming()
        
        # Example: Manually test data retrieval
        logger.info("Testing Zcash client...")
        if agent.zcash_client:
            try:
                blockchain_info = await agent.zcash_client.get_blockchain_info()
                logger.info(f"Blockchain info: {blockchain_info}")
                
                block_count = await agent.zcash_client.get_block_count()
                logger.info(f"Current block height: {block_count}")
                
                pool_metrics = await agent.zcash_client.get_shielded_pool_metrics()
                logger.info(f"Shielded pool metrics: {pool_metrics}")
            except Exception as e:
                logger.warning(f"Zcash client test failed (node may not be available): {e}")
        
        # Keep agent running
        logger.info("Agent is running. Press Ctrl+C to stop.")
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        # Cleanup
        await agent.cleanup()
        agent.close()
        connection_pool.close()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
