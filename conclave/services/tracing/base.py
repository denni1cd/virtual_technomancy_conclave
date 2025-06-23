"""
Abstract base class for tracing implementations.
"""

from __future__ import annotations

import contextvars
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class TraceContext:
    """Context for tracing operations."""
    run_id: str
    span_id: str
    metadata: Dict[str, Any]


class AbstractTracer(ABC):
    """Abstract base class for tracing implementations."""
    
    def __init__(self):
        # ContextVar for propagating trace context across async tasks
        self._context_var: contextvars.ContextVar[Optional[TraceContext]] = contextvars.ContextVar(
            "trace_context", default=None
        )
    
    @abstractmethod
    def start_root_span(self, project_name: str, metadata: Optional[Dict[str, Any]] = None) -> TraceContext:
        """Start a root span for a project."""
        pass
    
    @abstractmethod
    def start_child_span(self, name: str, kind: str, metadata: Optional[Dict[str, Any]] = None) -> TraceContext:
        """Start a child span."""
        pass
    
    @abstractmethod
    def end_span(self, context: TraceContext, outputs: Optional[Dict[str, Any]] = None) -> None:
        """End a span."""
        pass
    
    @abstractmethod
    def add_event(self, event_type: str, payload: Dict[str, Any], 
                  cost_usd: Optional[float] = None, tokens: Optional[int] = None) -> None:
        """Add an event to the current span."""
        pass
    
    def get_current_context(self) -> Optional[TraceContext]:
        """Get the current trace context."""
        return self._context_var.get()
    
    def set_current_context(self, context: TraceContext) -> None:
        """Set the current trace context."""
        self._context_var.set(context)
    
    def get_trace_url(self) -> Optional[str]:
        """Get the trace URL for the current run (optional)."""
        return None
    
    @contextmanager
    def root_span(self, project_name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager for root spans.
        
        Args:
            project_name: Name of the project/run
            metadata: Additional metadata for the span
        """
        context = self.start_root_span(project_name, metadata)
        try:
            yield context
        finally:
            self.end_span(context)
    
    @contextmanager
    def child_span(self, name: str, kind: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager for child spans.
        
        Args:
            name: Name of the span
            kind: Type of operation (e.g., "LLM", "TOOL", "DEBATE")
            metadata: Additional metadata for the span
        """
        context = self.start_child_span(name, kind, metadata)
        try:
            yield context
        finally:
            self.end_span(context)
    
    def _redact_pii(self, data: Any) -> Any:
        """
        Redact PII from data if redaction is enabled.
        
        Args:
            data: Data to potentially redact
            
        Returns:
            Redacted data or original data
        """
        if isinstance(data, str):
            # Simple PII redaction - replace prompts and code with [redacted]
            if any(keyword in data.lower() for keyword in ["prompt", "user", "password", "api_key", "secret"]):
                return "[redacted]"
            # Redact code blocks
            if "```" in data or "def " in data or "class " in data:
                return "[redacted]"
            # Redact OpenAI API keys and similar
            if data.strip().startswith("sk-"):
                return "[redacted]"
        elif isinstance(data, dict):
            return {k: self._redact_pii(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._redact_pii(item) for item in data]
        
        return data 