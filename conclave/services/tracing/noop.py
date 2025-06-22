"""
No-op tracer implementation for when tracing is disabled.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from .base import AbstractTracer, TraceContext


class NoopTracer(AbstractTracer):
    """No-op tracer that does nothing."""
    
    def start_root_span(self, project_name: str, metadata: Optional[Dict[str, Any]] = None) -> TraceContext:
        """Start a root span (no-op)."""
        context = TraceContext(
            run_id="noop",
            span_id="noop",
            metadata=metadata or {}
        )
        self.set_current_context(context)
        return context
    
    def start_child_span(self, name: str, kind: str, metadata: Optional[Dict[str, Any]] = None) -> TraceContext:
        """Start a child span (no-op)."""
        context = TraceContext(
            run_id="noop",
            span_id=f"noop_{name}",
            metadata=metadata or {}
        )
        self.set_current_context(context)
        return context
    
    def end_span(self, context: TraceContext, outputs: Optional[Dict[str, Any]] = None) -> None:
        """End a span (no-op)."""
        pass
    
    def add_event(self, event_type: str, payload: Dict[str, Any], 
                  cost_usd: Optional[float] = None, tokens: Optional[int] = None) -> None:
        """Add an event (no-op)."""
        pass 