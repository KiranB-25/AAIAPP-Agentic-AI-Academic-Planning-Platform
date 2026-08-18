import logging
import hashlib

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.core.cache import cache
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, Throttled
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Role, User

logger = logging.getLogger(__name__)


def _login_key(email: str) -> str:
    return f"auth-login-failures:{email.casefold()}"


def _lock_key(email: str) -> str:
    return f"auth-login-lock:{email.casefold()}"


def _identifier(email: str) -> str:
    return hashlib.sha256(email.casefold().encode()).hexdigest()[:16]


def default_student_role() -> Role:
    role, _ = Role.objects.get_or_create(name=Role.Name.STUDENT)
    return role


def issue_tokens(user: User) -> dict[str, str]:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def authenticate_login(*, email: str, password: str, request) -> User:
    key = _lock_key(email)
    if cache.get(key):
        logger.warning("Authentication denied for temporarily locked account", extra={"identifier": _identifier(email)})
        raise Throttled(wait=settings.AUTH_LOGIN_LOCKOUT_MINUTES * 60, detail="Too many failed login attempts. Try again later.")

    user = authenticate(request=request, email=email, password=password)
    if user is None or not user.is_account_active:
        failures_key = _login_key(email)
        failures = cache.get(failures_key, 0) + 1
        lock_timeout = settings.AUTH_LOGIN_LOCKOUT_MINUTES * 60
        cache.set(failures_key, failures, lock_timeout)
        if failures >= settings.AUTH_LOGIN_MAX_FAILURES:
            cache.set(key, True, lock_timeout)
            cache.delete(failures_key)
        logger.warning("Authentication failed", extra={"identifier": _identifier(email), "ip": request.META.get("REMOTE_ADDR")})
        raise AuthenticationFailed("Invalid email or password.")

    cache.delete(_login_key(email))
    logger.info("Authentication succeeded", extra={"user_id": user.pk, "ip": request.META.get("REMOTE_ADDR")})
    update_last_login(None, user)
    return user


def logout_refresh_token(refresh_token: str) -> None:
    try:
        RefreshToken(refresh_token).blacklist()
    except Exception as exc:
        raise AuthenticationFailed("Invalid refresh token.") from exc
