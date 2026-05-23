import logging
from pathlib import Path


def get_online_logger(name):
    logger = logging.getLogger(f"generala_plus.online.{name}")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    logs_dir = Path.cwd() / "logs"
    logs_dir.mkdir(exist_ok=True)
    handler = logging.FileHandler(logs_dir / "online.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)
    return logger
