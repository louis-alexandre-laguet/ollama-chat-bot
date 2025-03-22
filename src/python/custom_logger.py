import logging

from config_loader import ConfigLoader

class CustomLogger:
    """
    Singleton class for setting up and managing custom logging configurations.
    """
    _instance = None

    def __new__(cls):
        """
        Create or return the singleton instance of CustomLogger.

        Returns:
            CustomLogger: The singleton instance of the CustomLogger class.
        """
        if cls._instance is None:
            cls._instance = super(CustomLogger, cls).__new__(cls)
            cls._instance.config_loader = ConfigLoader()
            cls._instance._initialize()
        return cls._instance


    def _initialize(self):
        """
        Initialize the logger with settings from the configuration file.

        This method sets up the default logging configuration and applies any 
        custom log level specified in the configuration file.
        """
        # Load the configuration
        config = self._instance.config_loader.load_config()

        # Default logging configuration
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )

        # Configure logging level from config
        log_level_str = config.get('logging', {}).get('level', 'INFO').upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        logging.getLogger().setLevel(log_level)
        logging.info(f"Logging level set to {log_level_str}")


    @staticmethod
    def get_logger(name):
        """
        Get a logger instance with the specified name.

        Args:
            name (str): The name of the logger.

        Returns:
            logging.Logger: A logger instance configured with the custom settings.
        """
        return logging.getLogger(name)


# Initialize the custom logger instance
custom_logger = CustomLogger()
