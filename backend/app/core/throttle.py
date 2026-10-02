"""Limitation de débit sur la connexion, par adresse source.

`/auth/login` n'avait jusqu'ici aucun frein : un mot de passe deviné se
teste sans limite. Fenêtre glissante en mémoire — pas de service dédié à
ça, cohérent avec le reste du projet. Le compteur est local au worker :
avec plusieurs workers Uvicorn le débit réellement autorisé est multiplié
d'autant, ce qui reste un frein sérieux contre une attaque en ligne sans
prétendre à un verrouillage strict.
"""
import time

from fastapi import HTTPException, Request, status

LOGIN_MAX_ATTEMPTS = 10
LOGIN_WINDOW_SECONDS = 300

_attempts: dict[str, list[float]] = {}


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "inconnu"


def throttle_login(request: Request) -> None:
    """Refuse au-delà de `LOGIN_MAX_ATTEMPTS` échecs récents pour cette IP.

    Purge au passage les fenêtres expirées, pour que le dictionnaire ne
    grossisse pas indéfiniment sur une instance de longue durée.
    """
    now = time.monotonic()
    cutoff = now - LOGIN_WINDOW_SECONDS
    client_ip = _client_ip(request)

    for ip, times in list(_attempts.items()):
        kept = [t for t in times if t > cutoff]
        if kept:
            _attempts[ip] = kept
        else:
            del _attempts[ip]

    if len(_attempts.get(client_ip, ())) >= LOGIN_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Trop de tentatives — réessayer dans {LOGIN_WINDOW_SECONDS // 60} minutes",
        )


def record_login_failure(request: Request) -> None:
    _attempts.setdefault(_client_ip(request), []).append(time.monotonic())


def clear_login_failures(request: Request) -> None:
    _attempts.pop(_client_ip(request), None)


def _reset_all() -> None:
    """Réservé aux tests : vide tout le compteur entre deux cas isolés."""
    _attempts.clear()
