"""Capture token usage and provider-reported cost from LangChain LLM callbacks."""
from typing import Any
from langchain_core.callbacks import BaseCallbackHandler


def _as_dict(value: Any) -> dict:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        try:
            return value.model_dump()
        except Exception:
            return {}
    if hasattr(value, "dict"):
        try:
            return value.dict()
        except Exception:
            return {}
    return {}


class LLMUsageCapture(BaseCallbackHandler):
    def __init__(self):
        self.data = {
            "input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
            "input_cost": None, "output_cost": None, "total_cost": None,
            "model_name": None, "usage_source": "unavailable",
        }

    def _capture(self, response: Any) -> None:
        output = _as_dict(getattr(response, "llm_output", None))
        generations = getattr(response, "generations", []) or []
        message = None
        try:
            message = generations[0][0].message
        except (IndexError, AttributeError, TypeError):
            pass
        usage = _as_dict(getattr(message, "usage_metadata", None))
        response_meta = _as_dict(getattr(message, "response_metadata", None))
        token_usage = _as_dict(output.get("token_usage"))
        if not token_usage:
            token_usage = _as_dict(response_meta.get("token_usage"))
        if not token_usage:
            token_usage = _as_dict(response_meta.get("usage"))
        usage = {**token_usage, **usage}

        def first(*keys):
            for key in keys:
                val = usage.get(key)
                if val is not None:
                    return val
            return None

        input_tokens = first("input_tokens", "prompt_tokens")
        output_tokens = first("output_tokens", "completion_tokens")
        total_tokens = first("total_tokens")
        if input_tokens is not None: self.data["input_tokens"] = int(input_tokens)
        if output_tokens is not None: self.data["output_tokens"] = int(output_tokens)
        if total_tokens is not None: self.data["total_tokens"] = int(total_tokens)
        elif input_tokens is not None or output_tokens is not None:
            self.data["total_tokens"] = int(input_tokens or 0) + int(output_tokens or 0)

        details = _as_dict(usage.get("cost_details"))
        total_cost = first("total_cost", "cost", "total_cost_usd")
        input_cost = first("input_cost", "prompt_cost")
        output_cost = first("output_cost", "completion_cost")
        if total_cost is None: total_cost = details.get("upstream_inference_cost")
        if input_cost is None: input_cost = details.get("upstream_inference_prompt_cost")
        if output_cost is None: output_cost = details.get("upstream_inference_completions_cost")
        for key, val in (("input_cost", input_cost), ("output_cost", output_cost), ("total_cost", total_cost)):
            if val is not None:
                try: self.data[key] = float(val)
                except (TypeError, ValueError): pass
        self.data["model_name"] = response_meta.get("model_name") or response_meta.get("model") or output.get("model_name")
        if any(self.data[k] for k in ("input_tokens", "output_tokens", "total_tokens")):
            self.data["usage_source"] = "llm_response"

    def on_llm_end(self, response, **kwargs):
        self._capture(response)
