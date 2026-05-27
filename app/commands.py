"""Comandos CLI: bootstrap admin, init-db, seed."""
from __future__ import annotations

import os
import secrets

import click
from flask.cli import with_appcontext

from app.extensions import db


def register_cli(app):
    app.cli.add_command(create_admin)
    app.cli.add_command(bootstrap_admin)
    app.cli.add_command(init_db)

    from app.seed_command import seed_data
    app.cli.add_command(seed_data)


@click.command("create-admin")
@click.argument("username")
@click.argument("email")
@click.argument("password")
@click.argument("is_superuser", default="false")
@with_appcontext
def create_admin(username, email, password, is_superuser):
    """Crea un usuario administrador."""
    from app.models.user import AdminUser

    is_super = is_superuser.lower() == 'true'

    if AdminUser.query.filter((AdminUser.username == username) | (AdminUser.email == email)).first():
        click.echo("Ya existe un usuario con ese username o email.")
        return

    user = AdminUser(
        username=username, email=email, is_superuser=is_super
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(f"Admin creado: {username} (id={user.id})")


@click.command("bootstrap-admin")
@with_appcontext
def bootstrap_admin():
    """Crea el admin inicial usando ADMIN_BOOTSTRAP_*."""
    from flask import current_app
    from app.models.user import AdminUser

    username = current_app.config.get("ADMIN_BOOTSTRAP_USERNAME")
    email = current_app.config.get("ADMIN_BOOTSTRAP_EMAIL")
    password = current_app.config.get("ADMIN_BOOTSTRAP_PASSWORD") or secrets.token_urlsafe(16)

    if AdminUser.query.filter_by(username=username).first():
        click.echo("Bootstrap admin ya existe; nada que hacer.")
        return
    user = AdminUser(username=username, email=email, is_superuser=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(f"Bootstrap admin creado: {username} / {email}")
    if not current_app.config.get("ADMIN_BOOTSTRAP_PASSWORD"):
        click.echo(f"Password generada: {password}")


@click.command("init-db")
@with_appcontext
def init_db():
    """Crea todas las tablas (usar solo sin Alembic)."""
    db.create_all()
    click.echo("Tablas creadas.")


