"""Domain-level exceptions used across the service."""


class MetadataServiceError(Exception):
    """Base class for all service-level errors."""


class CollectionError(MetadataServiceError):
    """Raised when an outbound HTTP fetch fails irrecoverably."""


class DatabaseUnavailableError(MetadataServiceError):
    """Raised when MongoDB cannot be reached after the startup retry window."""