"""Delivery sign-off generation for Triage."""

from .generator import generate_signoff
from .schema import GenerationResult, SignoffValidationError

__all__ = ["GenerationResult", "SignoffValidationError", "generate_signoff"]
