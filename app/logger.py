import logging
import sys

# Define the standard format for all logs
log_format = "%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"

# Configure the root logger
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    datefmt=date_format,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def get_logger(name: str):
    return logging.getLogger(name)