import logging
from pathlib import Path

# Configure logging
def setup_logging(log_level="INFO"):
    """Set up logging with the specified verbosity level."""
    # Convert string log level to numeric value
    numeric_level = getattr(logging, log_level.upper(), None)
    
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    # Configure logging
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create logger
    logger = logging.getLogger("docling_parser")
    logger.setLevel(numeric_level)
    
    # Add file handler if we want to log to file as well
    log_file = Path("logs") / "docling_parser.log"
    log_file.parent.mkdir(exist_ok=True)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    
    logger.addHandler(file_handler)
    
    logger.debug(f"Logging configured at level {log_level}")
    return logger

# Create a default logger instance
logger = setup_logging() 