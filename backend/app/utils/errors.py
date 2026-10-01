class AppError(Exception):
    safe_message = "Request complete aagala."


class ConfigurationError(AppError):
    safe_message = "Required configuration missing."


class AuthenticationError(AppError):
    safe_message = "Authentication failed or token expired."


class PermissionError(AppError):
    safe_message = "Required permission illa."


class ProviderError(AppError):
    safe_message = "Provider request failed."


class NetworkError(ProviderError):
    safe_message = "Provider network reachable illa."


class ProviderTimeout(NetworkError):
    safe_message = "Provider request timeout aayiduchu."


class GenerationError(ProviderError):
    safe_message = "Generation failed."


class SocialError(AppError):
    safe_message = "Social publish failed."


class PublishInProgressError(SocialError):
    safe_message = "Publish already processing; konjam wait pannunga."


class ExpiredError(SocialError):
    safe_message = "Preview expire aayiduchu."


class OwnershipError(SocialError):
    safe_message = "Indha preview unga account-ukku belong aagala."
