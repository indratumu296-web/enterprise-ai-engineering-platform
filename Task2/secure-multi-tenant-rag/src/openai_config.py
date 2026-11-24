import os

import streamlit as st


def get_openai_api_key() -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    try:
        return st.secrets.get("OPENAI_API_KEY") or api_key
    except (FileNotFoundError, RuntimeError):
        return api_key
