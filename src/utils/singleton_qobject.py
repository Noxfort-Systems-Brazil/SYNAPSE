# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/utils/singleton_qobject.py
# Author: Gabriel Moraes
# Date: 2026-09-14

import threading
from typing import Dict, Any
from PyQt6.QtCore import QObject


class SingletonQObject(type(QObject)):
    """
    Thread-safe Singleton metaclass compatible with PyQt6's C++ QObject wrapper type.
    Avoids Python/SIP C++ re-initialization crashes caused by overriding __new__ on QObject.
    """
    _instances: Dict[type, Any] = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
            else:
                instance = cls._instances[cls]
                app_state = kwargs.get("app_state") or (args[0] if args else None)
                if app_state is not None:
                    instance.app_state = app_state
            return cls._instances[cls]

    def clear(cls):
        with cls._lock:
            if cls in cls._instances:
                del cls._instances[cls]
