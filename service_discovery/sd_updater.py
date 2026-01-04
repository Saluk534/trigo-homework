#!/usr/bin/env python3
"""
Prometheus Service Discovery Updater for Sensor Inventory
Periodically queries the inventory service and updates Prometheus targets file.
"""
import json
import logging
import os
import sys
import time
from typing import List, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuration from environment variables with sensible defaults
INVENTORY_URL = os.getenv('INVENTORY_URL', 'http://inventory_server:1337/inventory')
UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', '30'))  # seconds
TARGETS_FILE = os.getenv('TARGETS_FILE', '/shared/targets.json')
METRICS_PORT = os.getenv('METRICS_PORT', '9100')  # Port where sensors expose metrics
METRICS_PATH = os.getenv('METRICS_PATH', '/metrics')  # Metrics endpoint path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def create_http_session() -> requests.Session:
    """Create HTTP session with retry logic for resilience."""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def fetch_sensor_inventory(session: requests.Session) -> List[str]:
    """
    Fetch the current sensor inventory from the inventory service.
    
    Args:
        session: HTTP session with retry logic
        
    Returns:
        List of sensor hostnames
        
    Raises:
        requests.RequestException: If fetching inventory fails after retries
    """
    try:
        logger.info(f"Fetching sensor inventory from {INVENTORY_URL}")
        response = session.get(INVENTORY_URL, timeout=10)
        response.raise_for_status()
        sensors = response.json()
        
        if not isinstance(sensors, list):
            raise ValueError(f"Expected list from inventory service, got {type(sensors)}")
            
        logger.info(f"Successfully fetched {len(sensors)} sensors")
        return sensors
    except requests.RequestException as e:
        logger.error(f"Failed to fetch inventory: {e}")
        raise
    except (ValueError, json.JSONDecodeError) as e:
        logger.error(f"Invalid response format: {e}")
        raise


def create_prometheus_targets(sensors: List[str]) -> List[Dict[str, Any]]:
    """
    Convert sensor list to Prometheus file-based service discovery format.
    
    Args:
        sensors: List of sensor hostnames
        
    Returns:
        List of target groups in Prometheus SD format
    """
    targets = [f"{sensor}:{METRICS_PORT}" for sensor in sensors]
    
    # Prometheus file-based SD format
    target_group = {
        "targets": targets,
        "labels": {
            "__metrics_path__": METRICS_PATH,
            "job": "sensors",
            "environment": "production"
        }
    }
    
    logger.debug(f"Created target group with {len(targets)} targets")
    return [target_group]


def write_targets_file(targets: List[Dict[str, Any]], file_path: str) -> None:
    """
    Write targets to JSON file atomically to prevent Prometheus from reading partial files.
    
    Args:
        targets: List of target groups
        file_path: Path to write the targets file
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write to temporary file first (atomic operation)
        temp_file = f"{file_path}.tmp"
        with open(temp_file, 'w') as f:
            json.dump(targets, f, indent=2)
        
        # Atomic rename
        os.replace(temp_file, file_path)
        logger.info(f"Successfully updated targets file: {file_path}")
        
    except (IOError, OSError) as e:
        logger.error(f"Failed to write targets file: {e}")
        raise


def update_service_discovery() -> bool:
    """
    Main update logic: fetch inventory and update targets file.
    
    Returns:
        True if update was successful, False otherwise
    """
    session = create_http_session()
    
    try:
        # Fetch current sensor inventory
        sensors = fetch_sensor_inventory(session)
        
        # Convert to Prometheus target format
        targets = create_prometheus_targets(sensors)
        
        # Write to targets file
        write_targets_file(targets, TARGETS_FILE)
        
        return True
        
    except Exception as e:
        logger.error(f"Update cycle failed: {e}")
        return False


def main():
    """Main loop: periodically update service discovery."""
    logger.info("Starting Prometheus Service Discovery Updater")
    logger.info(f"Configuration:")
    logger.info(f"  Inventory URL: {INVENTORY_URL}")
    logger.info(f"  Update Interval: {UPDATE_INTERVAL}s")
    logger.info(f"  Targets File: {TARGETS_FILE}")
    logger.info(f"  Metrics Port: {METRICS_PORT}")
    logger.info(f"  Metrics Path: {METRICS_PATH}")
    
    # Initial update with retry logic for startup
    max_startup_retries = 10
    for attempt in range(max_startup_retries):
        try:
            if update_service_discovery():
                logger.info("Initial update successful")
                break
        except Exception as e:
            if attempt < max_startup_retries - 1:
                logger.warning(f"Startup attempt {attempt + 1} failed, retrying in 5s...")
                time.sleep(5)
            else:
                logger.error("Failed to complete initial update after all retries")
                sys.exit(1)
    
    # Main loop
    while True:
        try:
            time.sleep(UPDATE_INTERVAL)
            update_service_discovery()
        except KeyboardInterrupt:
            logger.info("Received shutdown signal, exiting gracefully")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            # Continue running even if one cycle fails


if __name__ == '__main__':
    main()

