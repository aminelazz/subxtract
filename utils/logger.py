import logging

def get_logger(name: str) -> logging.Logger:
    """Returns a logger with the specified name."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        datefmt='%d-%m-%Y %H:%M:%S',
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
    )
    logger = logging.getLogger(name)
    return logger