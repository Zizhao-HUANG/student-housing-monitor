import configparser
import logging

def load_config(path='config.ini'):
    """
    Loads the configuration from the specified .ini file.

    Args:
        path (str): The path to the config.ini file.

    Returns:
        A configparser object, or None if the file is not found.
    """
    config = configparser.ConfigParser()
    # config.read() returns a list of files that were successfully read.
    # If the list is empty, the config file was not found or was empty.
    if not config.read(path, encoding='utf-8'):
        logging.error(f"Configuration file not found or is empty at '{path}'.")
        logging.error("Please copy 'config.ini.template' to 'config.ini' and fill in your details.")
        return None
    return config
