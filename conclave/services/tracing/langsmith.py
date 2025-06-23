"""
LangSmith tracer implementation.
"""

from __future__ import annotations

import os
import uuid
from typing import Any, Dict, Optional
from .base import AbstractTracer, TraceContext


class LangSmithTracer(AbstractTracer):
    """LangSmith tracer implementation using RunTree."""
    
    def __init__(self):
        super().__init__()
        try:
            from langsmith import Client, RunTree
            self.client = Client()
            self.RunTree = RunTree
            self._current_run: Optional[RunTree] = None
        except ImportError:
            raise ImportError("langsmith package not installed. Install with: pip install langsmith")
    
    def start_root_span(self, project_name: str, metadata: Optional[Dict[str, Any]] = None) -> TraceContext:
        """Start a root span using LangSmith RunTree."""
        try:
            # Redact PII from metadata
            safe_metadata = self._redact_pii(metadata or {})
            
            # Create root run
            run_id = str(uuid.uuid4())
            self._current_run = self.RunTree(
                name=project_name,
                run_type="project",
                inputs=safe_metadata
            )
            
            context = TraceContext(
                run_id=run_id,
                span_id=run_id,
                metadata=safe_metadata
            )
            self.set_current_context(context)
            return context
            
        except Exception as e:
            import logging
            logging.warning(f"Failed to start LangSmith root span: {e}")
            # Fall back to noop behavior
            return super().start_root_span(project_name, metadata)
    
    def start_child_span(self, name: str, kind: str, metadata: Optional[Dict[str, Any]] = None) -> TraceContext:
        """Start a child span using LangSmith RunTree."""
        try:
            if self._current_run is None:
                # No parent run, create a new root
                return self.start_root_span(name, metadata)
            
            # Redact PII from metadata
            safe_metadata = self._redact_pii(metadata or {})
            
            # Create child run
            span_id = str(uuid.uuid4())
            child_run = self._current_run.start_child(
                name=name,
                run_type=kind.lower(),
                inputs=safe_metadata
            )
            
            context = TraceContext(
                run_id=str(self._current_run.id) if self._current_run.id else span_id,
                span_id=span_id,
                metadata=safe_metadata
            )
            self.set_current_context(context)
            return context
            
        except Exception as e:
            import logging
            logging.warning(f"Failed to start LangSmith child span: {e}")
            # Fall back to noop behavior
            return super().start_child_span(name, kind, metadata)
    
    def end_span(self, context: TraceContext, outputs: Optional[Dict[str, Any]] = None) -> None:
        """End a span using LangSmith RunTree."""
        try:
            if self._current_run is not None:
                # Redact PII from outputs
                safe_outputs = self._redact_pii(outputs or {})
                self._current_run.end(outputs=safe_outputs)
                
        except Exception as e:
            import logging
            logging.warning(f"Failed to end LangSmith span: {e}")
    
    def add_event(self, event_type: str, payload: Dict[str, Any], 
                  cost_usd: Optional[float] = None, tokens: Optional[int] = None) -> None:
        """Add an event to the current span."""
        try:
            if self._current_run is not None:
                # Redact PII from payload
                safe_payload = self._redact_pii(payload)
                
                # Add cost information if provided
                if cost_usd is not None:
                    safe_payload["cost_usd"] = cost_usd
                if tokens is not None:
                    safe_payload["tokens"] = tokens
                
                # Add event as extra metadata
                self._current_run.extra = {
                    **(self._current_run.extra or {}),
                    f"event_{event_type}": safe_payload
                }
                
        except Exception as e:
            import logging
            logging.warning(f"Failed to add LangSmith event: {e}")
    
    def get_trace_url(self) -> Optional[str]:
        """Get the trace URL for the current run."""
        try:
            if self._current_run is not None and hasattr(self._current_run, 'url'):
                return self._current_run.url
        except Exception:
            pass
        return None 