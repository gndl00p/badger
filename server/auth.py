from fastapi import Depends, Header, HTTPException, status

from server.config import Settings


def require_badge_token(settings: Settings):
    def _check(x_badge_token: str | None = Header(default=None)):
        if x_badge_token != settings.badge_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bad token")

    return Depends(_check)