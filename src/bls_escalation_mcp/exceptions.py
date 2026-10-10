"""Typed exceptions for the BLS escalation scaffold."""


class BLSEscalationError(Exception):
    """Base exception for the project."""


class BLSAPIError(BLSEscalationError):
    """Raised when the BLS API request fails or returns an error payload."""


class SeriesNotFoundError(BLSEscalationError):
    """Raised when a requested series ID is missing."""


class ObservationNotFoundError(BLSEscalationError):
    """Raised when required observations are not found."""


class InvalidWeightsError(BLSEscalationError):
    """Raised when component weights do not meet expected constraints."""


class CalculationError(BLSEscalationError):
    """Raised for invalid calculation inputs."""


class InvalidPeriodError(BLSEscalationError):
    """Raised when an observation period is invalid."""


class UnsupportedLocalityError(BLSEscalationError):
    """Raised when locality logic is requested for unsupported scope."""


class catalogError(BLSEscalationError):
    """Raised when catalog lookup or persistence fails."""


class RepositoryError(BLSEscalationError):
    """Raised when repository operations fail."""
