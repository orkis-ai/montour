# =============================================================
# MonTour — montour/utils.py
# Utilitaires globaux : exception handler, helpers IA
# =============================================================

import logging
import random
from datetime import datetime
from rest_framework.views import exception_handler
from rest_framework.response import Response

logger = logging.getLogger('apps')


# ─── Gestionnaire d'exceptions personnalisé DRF ─────────────
def custom_exception_handler(exc, context):
    """
    Surcharge le handler par défaut de DRF pour uniformiser
    le format des erreurs JSON retournées par l'API.
    """
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            'success': False,
            'error': {
                'code': response.status_code,
                'message': _extract_message(response.data),
                'details': response.data,
            }
        }
    return response


def _extract_message(data):
    if isinstance(data, dict):
        for key in ('detail', 'message', 'non_field_errors'):
            if key in data:
                v = data[key]
                return str(v[0]) if isinstance(v, list) else str(v)
        return str(list(data.values())[0]) if data else 'Erreur inconnue'
    if isinstance(data, list):
        return str(data[0])
    return str(data)


# ─── Module IA : Prédiction du temps d'attente ────────────────
class WaitTimePredictor:
    """
    Simule le modèle TensorFlow Lite embarqué dans l'app mobile.
    En production : charger le modèle .tflite et invoquer l'inférence.
    """

    PRIORITY_FACTORS = {
        'urgent':   0.3,
        'handicap': 0.5,
        'senior':   0.7,
        'normal':   1.0,
    }

    PEAK_SCHEDULES = [
        (8, 10, 1.5),    # Pointe matin
        (11, 13, 1.3),   # Avant-midi
        (15, 17, 1.4),   # Pointe après-midi
    ]

    @classmethod
    def predict(cls, service, position_in_queue: int, user_priority: str) -> int:
        """
        Prédit le temps d'attente en minutes.

        Args:
            service: instance Service avec avg_service_time
            position_in_queue: position effective de l'usager
            user_priority: 'urgent' | 'handicap' | 'senior' | 'normal'

        Returns:
            Temps estimé en minutes (entier, min 1)
        """
        base = service.avg_service_time
        peak_factor = cls._get_peak_factor()
        priority_factor = cls.PRIORITY_FACTORS.get(user_priority, 1.0)

        effective_pos = max(1, position_in_queue * priority_factor)
        estimated = round(effective_pos * base * peak_factor)

        # Bruit réaliste ±15%
        noise = 1 + (random.uniform(-0.15, 0.15))
        result = max(1, round(estimated * noise))

        logger.debug(
            f"[IA] Service={service.name}, pos={position_in_queue}, "
            f"priority={user_priority} → {result} min"
        )
        return result

    @classmethod
    def _get_peak_factor(cls) -> float:
        hour = datetime.now().hour
        for start, end, factor in cls.PEAK_SCHEDULES:
            if start <= hour <= end:
                return factor
        return 1.0


# ─── Module IA : Score de priorité dynamique ─────────────────
class PriorityScorer:
    """
    Calcule le score de priorité pour trier la file d'attente.
    Score = score_base_priorité + bonus_temps_attente
    """

    BASE_SCORES = {
        'urgent':   100,
        'handicap': 80,
        'senior':   60,
        'normal':   40,
    }

    @classmethod
    def compute(cls, priority: str, requested_at: datetime) -> int:
        base = cls.BASE_SCORES.get(priority, 40)
        waited_minutes = (datetime.now(tz=requested_at.tzinfo) - requested_at).total_seconds() / 60
        return base + int(waited_minutes)


# ─── Réponse API standardisée ────────────────────────────────
def api_response(data=None, message='', success=True, status_code=200):
    return Response(
        {'success': success, 'message': message, 'data': data},
        status=status_code
    )


def api_error(message, status_code=400, details=None):
    return Response(
        {'success': False, 'error': {'message': message, 'details': details}},
        status=status_code
    )
