"""CRUD de noticias."""
from datetime import datetime
from flask import redirect, render_template, request, url_for
from flask_login import login_required, current_user
from app.admin import admin_bp
from app.admin.routes_components._helpers import flash_err, flash_ok
from app.extensions import db
from app.models.content import NEWS_STATUSES, NewsPost, NewsCategory
from app.models.media import MediaAsset
from app.services.sanitize_service import sanitize_html
from app.utils.slug import ensure_unique_slug, slugify

@admin_bp.route("/news")
@login_required
def news_list():
    from sqlalchemy import case
    status = request.args.get("status")
    query = NewsPost.query
    if status in NEWS_STATUSES:
        query = query.filter_by(status=status)
    items = query.order_by(
        case((NewsPost.published_at == None, 1), else_=0),
        NewsPost.published_at.desc(),
        NewsPost.created_at.desc()
    ).all()
    return render_template("admin/news_list.html", posts=items, statuses=NEWS_STATUSES)

@admin_bp.route("/news/new", methods=["GET", "POST"])
@login_required
def news_new():
    if request.method == "POST":
        p, err = _save(None)
        if err:
            flash_err(err)
        else:
            flash_ok("Noticia creada.")
            return redirect(url_for("admin.news_edit", post_id=p.id))
    cats = NewsCategory.query.all()
    return render_template("admin/news_form.html", post=None, categories=cats, statuses=NEWS_STATUSES,
                           media_assets=_image_media_assets())

@admin_bp.route("/news/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def news_edit(post_id):
    p = NewsPost.query.get_or_404(post_id)
    if request.method == "POST":
        _, err = _save(p)
        if err:
            flash_err(err)
        else:
            flash_ok("Noticia actualizada.")
            return redirect(url_for("admin.news_edit", post_id=p.id))
    cats = NewsCategory.query.all()
    return render_template("admin/news_form.html", post=p, categories=cats, statuses=NEWS_STATUSES,
                           media_assets=_image_media_assets())

def _save(p):
    title = (request.form.get("title") or "").strip()
    if not title: return None, "Titulo requerido."
    requested_slug = (request.form.get("slug") or "").strip()
    slug = slugify(requested_slug, 320) if requested_slug else slugify(title, 320)
    
    if p is None:
        slug = ensure_unique_slug(NewsPost, "slug", slug)
        p = NewsPost(slug=slug)
        db.session.add(p)
    elif slug != p.slug:
        slug = ensure_unique_slug(NewsPost, "slug", slug, ignore_id=p.id)

    p.title = title
    p.slug = slug
    p.excerpt = request.form.get("excerpt")
    p.content_html = sanitize_html(request.form.get("content_html") or "")
    p.seo_title = (request.form.get("seo_title") or "").strip() or None
    p.seo_description = (request.form.get("seo_description") or "").strip() or None
    
    cat_id = request.form.get("category_id")
    p.category_id = int(cat_id) if cat_id else None
    
    status = request.form.get("status", "draft")
    p.status = status if status in NEWS_STATUSES else "draft"
    p.is_featured = request.form.get("is_featured") == "on"
    
    if p.status == "published" and not p.published_at:
        p.published_at = datetime.utcnow()
    elif p.status != "published":
        p.published_at = None

    if p is None or not p.author_id:
        p.author_id = current_user.id
        
    cover_media_id = request.form.get("cover_media_id")
    og_media_id = request.form.get("og_media_id")
    try:
        p.cover_media_id = int(cover_media_id) if cover_media_id else None
    except (TypeError, ValueError):
        p.cover_media_id = None
    try:
        p.og_media_id = int(og_media_id) if og_media_id else None
    except (TypeError, ValueError):
        p.og_media_id = None

    if p.cover_media_id and not MediaAsset.query.get(p.cover_media_id):
        return None, "La portada seleccionada no existe."
    if p.og_media_id and not MediaAsset.query.get(p.og_media_id):
        return None, "La imagen OG seleccionada no existe."

    db.session.commit()
    return p, None

def _image_media_assets():
    return (
        MediaAsset.query
        .filter(MediaAsset.mime_type.like("image/%"))
        .order_by(MediaAsset.created_at.desc())
        .all()
    )

@admin_bp.route("/news/<int:post_id>/delete", methods=["POST"])
@login_required
def news_delete(post_id):
    p = NewsPost.query.get_or_404(post_id)
    db.session.delete(p)
    db.session.commit()
    flash_ok("Noticia eliminada.")
    return redirect(url_for("admin.news_list"))

@admin_bp.route("/news/categories", methods=["GET", "POST"])
@login_required
def news_categories():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            nm = (request.form.get("name") or "").strip()
            if nm:
                slug = slugify(nm)
                db.session.add(
                    NewsCategory(
                        name=nm,
                        slug=ensure_unique_slug(NewsCategory, "slug", slug),
                        description=(request.form.get("description") or "").strip() or None,
                        color=(request.form.get("color") or "").strip() or None,
                    )
                )
                db.session.commit()
                flash_ok("Categoría creada.")
        elif action == "update":
            c_id = request.form.get("category_id")
            category = NewsCategory.query.get_or_404(c_id)
            nm = (request.form.get("name") or "").strip()
            if nm:
                category.name = nm
                slug = (request.form.get("slug") or "").strip() or slugify(nm)
                if slug != category.slug:
                    category.slug = ensure_unique_slug(NewsCategory, "slug", slug, ignore_id=category.id)
                category.description = (request.form.get("description") or "").strip() or None
                category.color = (request.form.get("color") or "").strip() or None
                db.session.commit()
                flash_ok("Categoría actualizada.")
        elif action == "delete":
            c_id = request.form.get("category_id")
            if c_id:
                c = NewsCategory.query.get(c_id)
                if c:
                    db.session.delete(c)
                    db.session.commit()
                    flash_ok("Categoría eliminada.")
        return redirect(url_for("admin.news_categories"))
    items = NewsCategory.query.order_by(NewsCategory.name.asc()).all()
    editing_category = None
    edit_id = request.args.get("edit_id", type=int)
    if edit_id:
        editing_category = NewsCategory.query.get_or_404(edit_id)
    return render_template("admin/news_categories.html", categories=items, editing_category=editing_category)
