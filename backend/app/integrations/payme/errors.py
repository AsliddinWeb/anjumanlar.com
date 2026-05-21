"""Payme JSON-RPC error code catalogue + exception class.

The codes are copied verbatim from the Paycom Merchant API protocol.
We use a single ``PaymeError`` exception that the handler converts to
the JSON-RPC ``error`` shape so endpoint code never has to assemble
the response manually.
"""

from __future__ import annotations

from typing import Any

# Standard JSON-RPC 2.0 reserved range (-32700 .. -32600) plus Paycom's
# custom range (-31xxx). Messages are the protocol's English defaults;
# user-facing strings live in the locale files.
PAYME_ERRORS: dict[int, str] = {
    -32700: "Parse error",
    -32600: "Invalid request",
    -32601: "Method not found",
    -32602: "Invalid params",
    -32603: "Internal error",
    -32504: "Authorization failed",
    -31001: "Invalid amount",
    -31003: "Transaction not found",
    -31007: "Unable to cancel",
    -31008: "Unable to perform operation",
    -31050: "Order not found",
    -31051: "Order not available for payment",
    -31052: "Invalid amount",
    -31053: "Method not supported",
    -31054: "Order already paid",
    -31055: "Order cancelled",
    -31099: "Other error",
}


class PaymeError(Exception):
    """Raised inside the JSON-RPC handler — caught at the top level
    and serialised as ``{"jsonrpc": "2.0", "id": ..., "error": ...}``.
    """

    def __init__(
        self,
        code: int,
        message: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message or PAYME_ERRORS.get(code, "Unknown error")
        self.data = data or {}
        super().__init__(self.message)
