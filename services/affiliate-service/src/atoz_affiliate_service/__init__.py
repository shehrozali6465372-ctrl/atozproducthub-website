"""Affiliate & revenue business module — M5 business layer.

Owns the affiliate database (networks, merchants, products, categories,
links, tokens, clicks, revenue ledgers) and exposes the public catalog API,
the server-controlled redirector, the admin affiliate API, and the network
conversion webhook. Business data only: no AI functionality, no prompts,
no models — intelligence belongs to the AI OS and arrives via the Bridge.
"""

__version__ = "0.5.0"
