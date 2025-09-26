# logger_utils.py
import logging

def log_and_store(message, messages_list, level="info"):
    if level == "info":
        logging.info(message)
    elif level == "warning":
        logging.warning(message)
    elif level == "error":
        logging.error(message)
    messages_list.append(message)