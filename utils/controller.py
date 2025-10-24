"""Utility functions and shared resources for controller operations."""
from multiprocessing import Event

# Shared event to coordinate cancellation among extensions
extraction_cancel_event = Event()