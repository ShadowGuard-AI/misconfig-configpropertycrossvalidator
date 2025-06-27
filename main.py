import argparse
import logging
import json
import yaml
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define exception for configuration errors
class ConfigError(Exception):
    """Custom exception for configuration related errors."""
    pass


def setup_argparse():
    """Sets up the argument parser for the command line interface."""

    parser = argparse.ArgumentParser(description="Validates configuration properties against a known matrix of compatible values.")
    parser.add_argument("config_file", help="Path to the configuration file to validate (YAML or JSON).")
    parser.add_argument("compatibility_matrix", help="Path to the JSON file containing the compatibility matrix.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging.")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress output except for errors.")

    return parser.parse_args()


def load_config(config_file):
    """Loads the configuration file (JSON or YAML)."""
    try:
        with open(config_file, 'r') as f:
            file_extension = os.path.splitext(config_file)[1].lower()

            if file_extension == '.json':
                try:
                    config_data = json.load(f)
                except json.JSONDecodeError as e:
                    raise ConfigError(f"Error decoding JSON in {config_file}: {e}") from e

            elif file_extension == '.yaml' or file_extension == '.yml':
                try:
                    config_data = yaml.safe_load(f)
                except yaml.YAMLError as e:
                     raise ConfigError(f"Error decoding YAML in {config_file}: {e}") from e
            else:
                raise ConfigError("Unsupported file type.  Must be JSON or YAML.")

        return config_data
    except FileNotFoundError:
        raise ConfigError(f"Configuration file not found: {config_file}")
    except PermissionError:
        raise ConfigError(f"Permission denied when trying to read configuration file: {config_file}")
    except OSError as e:
        raise ConfigError(f"OS error when opening file: {config_file}. {e}")



def load_compatibility_matrix(matrix_file):
    """Loads the compatibility matrix from a JSON file."""
    try:
        with open(matrix_file, 'r') as f:
            try:
                matrix_data = json.load(f)
            except json.JSONDecodeError as e:
                raise ConfigError(f"Error decoding JSON in compatibility matrix file: {matrix_file}. {e}") from e

        return matrix_data
    except FileNotFoundError:
         raise ConfigError(f"Compatibility matrix file not found: {matrix_file}")
    except PermissionError:
        raise ConfigError(f"Permission denied when trying to read compatibility matrix file: {matrix_file}")
    except OSError as e:
        raise ConfigError(f"OS error when opening compatibility matrix file: {matrix_file}. {e}")


def validate_config(config_data, compatibility_matrix):
    """Validates the configuration data against the compatibility matrix."""
    issues = []

    for property_name, expected_values in compatibility_matrix.items():
        if property_name in config_data:
            actual_value = config_data[property_name]
            if actual_value not in expected_values:
                issues.append(f"Property '{property_name}' has incompatible value '{actual_value}'. Allowed values: {expected_values}")
                logging.warning(f"Property '{property_name}' has incompatible value '{actual_value}'. Allowed values: {expected_values}")
        else:
            issues.append(f"Property '{property_name}' is missing from the configuration.")
            logging.warning(f"Property '{property_name}' is missing from the configuration.")

    return issues


def main():
    """Main function to execute the configuration validation."""
    try:
        args = setup_argparse()

        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
            logging.debug("Verbose logging enabled.")
        elif args.quiet:
            logging.getLogger().setLevel(logging.ERROR)
            logging.debug("Suppressing output except for errors.")

        config_data = load_config(args.config_file)
        compatibility_matrix = load_compatibility_matrix(args.compatibility_matrix)

        issues = validate_config(config_data, compatibility_matrix)

        if issues:
            print("Configuration issues found:")
            for issue in issues:
                print(f"- {issue}")
            sys.exit(1)  # Exit with an error code
        else:
            if not args.quiet:
                print("Configuration is valid according to the compatibility matrix.")
            sys.exit(0)  # Exit with a success code


    except ConfigError as e:
        logging.error(f"Configuration error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logging.exception("An unexpected error occurred:")
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()