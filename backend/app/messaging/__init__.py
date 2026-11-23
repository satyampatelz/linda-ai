"""Messaging — WhatsApp + Instagram auto-reply via the official Meta APIs.

The agent reads inbound DMs, understands them with its normal brain, and
replies by itself — it never asks the user what to say. Only Meta's own
rules can stop a reply (the 24-hour customer-service window, a platform
that isn't configured yet) plus loop guards (dedupe by message id, a
per-contact rate limit). No unofficial libraries, no WhatsApp Web
automation — this is the official route, so there is no ban risk from
the integration itself.
"""
