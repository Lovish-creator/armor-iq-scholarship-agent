class ArmorIQException(Exception):
    """Base exception for ArmorIQ SDK errors."""
    pass

class InvalidTokenException(ArmorIQException):
    """Raised when an intent token signature or structure is invalid."""
    pass

class IntentMismatchException(ArmorIQException):
    """Raised when a requested action or target parameter violates the signed execution plan intent."""
    pass

class PolicyBlockedException(ArmorIQException):
    """Raised when a policy rule explicitly blocks tool execution."""
    pass

class TokenExpiredException(ArmorIQException):
    """Raised when an intent token has exceeded its validity duration."""
    pass
