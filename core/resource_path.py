import os
import sys


def resource_path(relative_path: str) -> str:
    """
    Vrátí absolutní cestu k souboru.
    Funguje při spuštění přes Python i po zabalení přes PyInstaller.
    """
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)