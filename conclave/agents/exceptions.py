class ConfigError(Exception):
    """Config file is missing or has invalid/missing keys."""


class UnknownRoleError(Exception):
    """Requested role does not exist in roles.yaml."""
