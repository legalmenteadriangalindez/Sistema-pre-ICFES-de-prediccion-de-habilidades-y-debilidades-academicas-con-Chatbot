# from django.apps import AppConfig


# class PrincipalConfig(AppConfig):
#     name = 'Principal'
from django.apps import AppConfig
import subprocess
import threading
import os


def start_ollama():
    subprocess.Popen(
        ["ollama", "serve"],
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


class PrincipalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Principal'

    def ready(self):
        # Evita duplicación por el autoreload de Django
        if os.environ.get("RUN_MAIN") != "true":
            return

        threading.Thread(
            target=start_ollama,
            daemon=True
        ).start()