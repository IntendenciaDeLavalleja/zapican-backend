"""Helpers compartidos del admin."""
from flask import abort, flash, redirect, request, url_for
from flask_login import current_user

def superuser_required(view):
    from functools import wraps
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("admin.login", next=request.url))
        if not current_user.is_superuser:
            abort(403)
        return view(*args, **kwargs)
    return wrapper

def admin_required(view):
    from functools import wraps
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("admin.login", next=request.url))
        return view(*args, **kwargs)
    return wrapper

def flash_ok(msg: str) -> None:
    flash(msg, "success")

def flash_err(msg: str) -> None:
    flash(msg, "error")