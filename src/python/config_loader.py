import os
import yaml

class ConfigLoader:
    """
    Handles the loading of configuration from a YAML file.
    """

    def __init__(self, config_filename='config.yaml', resources_dir='resources'):
        """
        Initialize the ConfigLoader with paths to the configuration file.

        Args:
            config_filename (str): The name of the configuration file. Defaults to 'config.yaml'.
            resources_dir (str): The directory containing the configuration file. Defaults to 'resources'.
        """
        self.config_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', resources_dir, config_filename)
        )

    def load_config(self):
        """
        Load the configuration from the YAML file.

        Returns:
            dict: The configuration data.

        Raises:
            FileNotFoundError: If the configuration file is not found.
            yaml.YAMLError: If there is an error reading the YAML file.
        """
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found at path: {self.config_path}")
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error reading configuration file: {e}")
