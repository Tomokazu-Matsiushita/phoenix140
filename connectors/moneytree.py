"""
Moneytree connector placeholder.

In ChatGPT, Moneytree data can be viewed through the connected tool.
In this standalone local Streamlit app, official Moneytree API credentials
are required. Add tokens to .env, then implement fetch_accounts().
"""

import os
import requests

class MoneytreeConnector:
    def __init__(self):
        self.access_token = os.getenv("MONEYTREE_ACCESS_TOKEN")

    def is_configured(self) -> bool:
        return bool(self.access_token)

    def fetch_accounts(self):
        if not self.is_configured():
            raise RuntimeError("Moneytree access token is not configured.")
        # Placeholder endpoint. Replace with official Moneytree endpoint/contract.
        raise NotImplementedError("Configure official Moneytree API endpoint here.")
