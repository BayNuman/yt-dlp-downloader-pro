# core/logging_setup.py
import logging
import sys
from pathlib import Path
from core.history import get_app_data_dir

_logger_initialized = False

def setup_logging():
    global _logger_initialized
    if _logger_initialized:
        return
        
    app_dir = get_app_data_dir()
    log_file = app_dir / "app.log"
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clean previous handlers if any
    logger.handlers.clear()
    
    # Formatter (Standardized Principal Engineer Log Format)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(threadName)s] [%(filename)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # File handler
    try:
        file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        sys.stderr.write(f"Failed to initialize file logger: {e}\n")
        
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    _logger_initialized = True
    logging.info("Logging system initialized successfully. Log file: %s", log_file)
