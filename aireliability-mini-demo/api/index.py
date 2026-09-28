"""Vercel Serverless Function entrypoint."""
import sys
import os

# Add parent directory to sys.path so app and server modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server import app
