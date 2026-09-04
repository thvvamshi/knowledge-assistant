class ProviderError(Exception):
    """Base exception for all LLM provider failures."""

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        retryable: bool = False,
    ):
        super().__init__(message)

        self.message = message
        self.provider = provider
        self.retryable = retryable

    def __str__(self) -> str:
        return self.message


class ProviderConfigurationError(ProviderError):
    """Raised when a provider is not configured correctly."""

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
    ):
        super().__init__(
            message,
            provider=provider,
            retryable=False,
        )


class ProviderUnavailableError(ProviderError):
    """Raised when a provider cannot currently be reached."""

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
    ):
        super().__init__(
            message,
            provider=provider,
            retryable=True,
        )


class ProviderTimeoutError(ProviderError):
    """Raised when a provider request times out."""

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
    ):
        super().__init__(
            message,
            provider=provider,
            retryable=True,
        )


class ProviderResponseError(ProviderError):
    """Raised when a provider returns an invalid or unusable response."""

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        retryable: bool = False,
    ):
        super().__init__(
            message,
            provider=provider,
            retryable=retryable,
        )