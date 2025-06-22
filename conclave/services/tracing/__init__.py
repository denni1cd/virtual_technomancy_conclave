"""
Tracing module for Conclave observability.

Provides structured tracing and cost metrics to external backends
(LangSmith, Langfuse) with fail-open behavior and PII redaction.
"""

from __future__ import annotations

import os
from typing import Optional
from .base import AbstractTracer
from .noop import NoopTracer

# Global tracer instance
_tracer: Optional[AbstractTracer] = None


def get_tracer() -> AbstractTracer:
    """
    Get the configured tracer instance.
    
    Returns:
        AbstractTracer: The configured tracer (LangSmith, Langfuse, or Noop)
    """
    global _tracer
    
    if _tracer is None:
        # Check environment variable first (CLI override)
        trace_backend = os.getenv("TRACE_ENABLED", "").lower()
        
        if trace_backend in ("false", "0", "off", "none"):
            _tracer = NoopTracer()
        elif trace_backend in ("langsmith", "true", "1", "on"):
            try:
                from .langsmith import LangSmithTracer
                _tracer = LangSmithTracer()
            except Exception as e:
                import logging
                logging.warning(f"Failed to initialize LangSmith tracer: {e}")
                _tracer = NoopTracer()
        elif trace_backend == "langfuse":
            try:
                from .langfuse import LangfuseTracer
                _tracer = LangfuseTracer()
            except Exception as e:
                import logging
                logging.warning(f"Failed to initialize Langfuse tracer: {e}")
                _tracer = NoopTracer()
        else:
            # Default to noop if no configuration
            _tracer = NoopTracer()
    
    return _tracer


def reset_tracer() -> None:
    """Reset the global tracer instance (mainly for testing)."""
    global _tracer
    _tracer = None 