"""Domain errors for the admin backend."""


class AdminBackendError(Exception):
    """Base class for expected admin backend failures."""


class AdminConfigurationError(AdminBackendError):
    """Required runtime configuration is missing or invalid."""


class AdminNotFoundError(AdminBackendError):
    """Requested admin resource does not exist."""


class AdminConflictError(AdminBackendError):
    """Requested operation conflicts with current persisted state."""

