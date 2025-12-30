"""Custom exceptions for the application."""


class ChatException(Exception):
    """Base exception for chat-related errors."""
    pass


class LLMServiceException(ChatException):
    """Exception raised when LLM service fails."""
    pass


class DatabaseException(ChatException):
    """Exception raised when database operations fail."""
    pass


class ValidationException(ChatException):
    """Exception raised when input validation fails."""
    pass

