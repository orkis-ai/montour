# =============================================================
# MonTour — montour/log_handlers.py
# Handlers de logging (module volontairement sans import Django/DRF :
# il est chargé par LOGGING avant l'initialisation des apps)
# =============================================================

import logging


class SafeStreamHandler(logging.StreamHandler):
    """
    StreamHandler qui ne plante pas sur les caractères que la console ne sait
    pas encoder (ex. « → » ou les emoji sur la console Windows cp1252) :
    ils sont remplacés au lieu de lever UnicodeEncodeError à chaque log.
    """
    def __init__(self, stream=None):
        super().__init__(stream)
        try:
            self.stream.reconfigure(errors='replace')
        except (AttributeError, ValueError):
            pass  # flux non reconfigurable (redirigé, capturé par un test runner…)
