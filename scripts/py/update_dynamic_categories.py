#!/usr/bin/env python3
"""
Update Dynamic Categories Script
Updates app_config.json with categories dynamically generated from Excel files
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.dynamic_categories import dynamic_categories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to update dynamic categories"""
    try:
        logger.info("Starting dynamic categories update...")
        
        # Update both app_config.json and roles.json with dynamic categories
        success = dynamic_categories.update_all_configs()
        
        if success:
            logger.info("✅ Dynamic categories updated successfully!")
            
            # Display the updated categories
            categories = dynamic_categories.get_dynamic_categories()
            logger.info(f"📊 Found {len(categories)} dynamic categories:")
            
            for category_id, category_config in categories.items():
                logger.info(f"  - {category_config['name']} ({category_id})")
                
        else:
            logger.error("❌ Failed to update dynamic categories")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Error updating dynamic categories: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
