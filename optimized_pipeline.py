#!/usr/bin/env python3
"""
Optimized Trading Pipeline
A modular, efficient trading pipeline with Telegram notifications
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(__file__))

from core.pipeline_orchestrator import PipelineOrchestrator
from logger import get_logger

async def main():
    """Main entry point for the optimized pipeline"""
    logger = get_logger("Main")
    
    logger.info("Starting Optimized Trading Pipeline")
    
    # Initialize pipeline with custom parameters
    pipeline = PipelineOrchestrator(
        symbol="XAUUSD",
        ema_period=200,
        take_profit_pips=50,
        stop_loss_pips=30
    )
    
    # Run until signal is generated
    result = await pipeline.run_until_signal(delay_seconds=1)
    
    if result:
        logger.info("Pipeline completed successfully")
    else:
        logger.warning("Pipeline completed without signal")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Pipeline stopped by user")
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        sys.exit(1)
