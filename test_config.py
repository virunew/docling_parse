#!/usr/bin/env python3

import os
import sys
import yaml
import logging

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_config_loading():
    """Test loading the docling_config.yaml file."""
    config_path = os.path.join(os.path.dirname(__file__), 'docling_config.yaml')
    
    if not os.path.exists(config_path):
        print(f"ERROR: Configuration file not found at {config_path}")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        print("Successfully loaded docling_config.yaml:")
        print(f"  Batch Size: {config.get('batch_concurrency_settings', {}).get('doc_batch_size')}")
        print(f"  Debug Mode: {config.get('debug_settings', {}).get('visualize_blocks', False)}")
        print(f"  Cache Dir: {config.get('app_settings', {}).get('cache_dir')}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}")
        return False

if __name__ == "__main__":
    success = test_config_loading()
    print(f"\nConfiguration test {'passed' if success else 'failed'}") 