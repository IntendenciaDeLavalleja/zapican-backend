import click
from datetime import datetime, timedelta
from flask.cli import with_appcontext
from app.extensions import db
from app.models import (
    SiteSettings, ThemeSettings, Authority, PageBlock,
    NewsCategory, NewsPost, Event, MunicipalMeeting, CustomForm, MediaAsset
)
from app.utils.slug import ensure_unique_slug, slugify

@click.command('seed-data')
@click.option('--force', is_flag=True, help="Force clear existing content and insert again")
@with_appcontext
def seed_data(force):
    if force:
        NewsPost.query.delete()
        Event.query.delete()
        Authority.query.delete()
        PageBlock.query.filter_by(page_type='home').delete()
        MunicipalMeeting.query.delete()
        CustomForm.query.delete()
        db.session.commit()

    # Helper to make media
    def create_dummy_media(url, filename="dummy.jpg"):
        media = MediaAsset(filename=filename, original_filename=filename, mime_type='image/jpeg', size_bytes=1000, public_url=url, is_public=True)
        db.session.add(media)
        db.session.flush()
        return media

    lavalleja_images = {
        'hero': 'https://commons.wikimedia.org/wiki/Special:FilePath/Atardecer%20en%20Marco%20de%20los%20Reyes%20-%20panoramio%20-%20Luis%20Irigoyen.jpg',
        'sierras': 'https://commons.wikimedia.org/wiki/Special:FilePath/CERRO%20GUAZUBIRA%20-%20panoramio.jpg',
        'arequita': 'https://commons.wikimedia.org/wiki/Special:FilePath/El%20Cerro%20Arequita%20desde%20el%20Cerro%20Artigas%20-%20panoramio.jpg',
        'valle': 'https://commons.wikimedia.org/wiki/Special:FilePath/EL%20VALLE%20-%20panoramio.jpg',
        'santa_elena': 'https://commons.wikimedia.org/wiki/Special:FilePath/Santa%20Elena%20de%20la%20Sierra%20Series%20210710-0004554-jikatu%20%2851303694953%29.jpg',
        'helada': 'https://commons.wikimedia.org/wiki/Special:FilePath/HELADA%20EN%20MARCO%20DE%20LOS%20REYES%202%20-%20panoramio.jpg',
        'minas': 'https://commons.wikimedia.org/wiki/Special:FilePath/Lejano%20oeste%20pero%20en%20minas%2C%20lavalleja%20-%20panoramio.jpg',
        'quarry': 'https://commons.wikimedia.org/wiki/Special:FilePath/Detail%20of%20the%20old%20quarry%20-%20panoramio.jpg',
    }

    logo_media = create_dummy_media(
        'https://upload.wikimedia.org/wikipedia/commons/thumb/c/cc/Escudo_de_Lavalleja.svg/240px-Escudo_de_Lavalleja.svg.png',
        'lavalleja-shield.png'
    )
    hero_media = create_dummy_media(
        lavalleja_images['hero'],
        'batlle-hero.jpg'
    )

    # Settings
    site = SiteSettings.get_settings()
    site.name = 'Batlle y Ordóñez'
    site.short_description = 'Municipio serrano del departamento de Lavalleja, con fuerte identidad rural, vida comunitaria y gestión de cercanía.'
    site.long_description = 'Batlle y Ordóñez forma parte del Lavalleja del relieve quebrado, las sierras, la producción agropecuaria y la escala barrial. Este seed simula una agenda municipal centrada en caminería rural, alumbrado, cultura local, apoyo a productores y servicios cotidianos.'
    site.email = 'contacto@municipiobatlle.uy'
    site.phone = '+598 4444 1234'
    site.address = 'Batlle y Ordóñez, Lavalleja, Uruguay'
    site.opening_hours = 'Lunes a viernes de 9:00 a 15:00'
    site.website_url = 'https://lavalleja.gub.uy'
    site.latitude = -33.4656
    site.longitude = -55.1167
    site.logo_media_id = logo_media.id
    site.shield_media_id = logo_media.id
    site.hero_media_id = hero_media.id
    site.seo_og_media_id = hero_media.id
    site.seo_title = 'Municipio de Batlle y Ordóñez'
    site.seo_description = 'Noticias, agenda, trámites y autoridades del Municipio de Batlle y Ordóñez.'
    
    theme = ThemeSettings.get_settings()
    theme.preset = 'sierra'
    theme.primary_color = '#1e6b67'
    theme.secondary_color = '#102a43'
    theme.accent_color = '#d8b15a'
    theme.background_color = '#f4ede3'
    theme.text_color = '#102531'
    theme.enable_dark_section = True
    theme.footer_variant = 'dark'
    theme.hero_style = 'image-full'
    theme.card_style = 'elevated'
    theme.custom_css = 'html[data-theme-mode="night"] { color-scheme: dark; }'
    
    # Blocks for home
    if not PageBlock.query.filter_by(page_type='home', block_type='hero').first():
        db.session.add(PageBlock(page_type='home', block_type='hero', order_index=1,
                                 title='Batlle y Ordóñez, entre sierras, producción y comunidad', subtitle='Servicios municipales, caminería rural, agenda local y noticias pensadas para una localidad del interior lavallejino.',
                                 config_json={
                                     'eyebrow': 'Lavalleja, Uruguay',
                                     'badge_text': 'Territorio serrano y vida local',
                                     'cta_primary_label': 'Ver trámites',
                                     'cta_primary_href': '#tramites',
                                     'cta_secondary_label': 'Conocer el concejo',
                                     'cta_secondary_href': '#concejo',
                                     'news_panel_eyebrow': 'ACTUALIDAD',
                                     'news_panel_title': 'Lo último en Batlle y Ordóñez'
                                 }, is_active=True))

    if not PageBlock.query.filter_by(page_type='home', block_type='navigation').first():
        db.session.add(PageBlock(page_type='home', block_type='navigation', order_index=0,
                                 title='Navegación Principal',
                                 config_json={
                                     'items': [
                                         {'label': 'Inicio', 'href': '#inicio'},
                                         {'label': 'Trámites', 'href': '#tramites'},
                                         {'label': 'Actualidad', 'href': '#actualidad'},
                                         {'label': 'Contacto', 'href': '#contacto'}
                                     ],
                                     'cta_label': 'Contactar',
                                     'cta_href': '#contacto'
                                 }, is_active=True))
    
    if not PageBlock.query.filter_by(page_type='home', block_type='contact_card').first():
        db.session.add(PageBlock(page_type='home', block_type='contact_card', order_index=5,
                                 title='Comunícate con el municipio', subtitle='Estamos para ayudarte',
                                 config_json={'body_text': 'Consultas sobre alumbrado, espacios públicos, caminería, actividades locales o trámites municipales. El contenido queda orientado a la realidad de una localidad del interior de Lavalleja.', 'territory_eyebrow': 'Territorio', 'territory_title': 'Comunidad serrana, conectada con su entorno rural', 'cta_email_label': 'Enviar correo', 'cta_phone_label': 'Llamar'}, is_active=True))

    if not PageBlock.query.filter_by(page_type='home', block_type='quick_links').first():
        db.session.add(PageBlock(page_type='home', block_type='quick_links', order_index=2,
                                 title='Accesos Rápidos',
                                 config_json={'links': [
                                     {'url': '#tramites', 'label': 'Caminería y servicios', 'description': 'Solicitudes sobre mantenimiento vial, espacios públicos y respuesta municipal.'},
                                     {'url': '#concejo', 'label': 'Concejo Municipal', 'description': 'Sesión abierta, resoluciones y participación en temas de la localidad.'},
                                     {'url': '#actualidad', 'label': 'Novedades locales', 'description': 'Obras, actividades comunitarias y acciones coordinadas con vecinos.'},
                                     {'url': '#contacto', 'label': 'Atención al vecino', 'description': 'Canales para consultas, coordinaciones y seguimiento de planteos.'}
                                 ]}, is_active=True))

    if not PageBlock.query.filter_by(page_type='home', block_type='tourism_highlights').first():
        db.session.add(PageBlock(page_type='home', block_type='tourism_highlights', order_index=3,
                                 title='Un municipio ligado al paisaje y al trabajo local', subtitle='Lavalleja combina sierras, valles, ganadería, agricultura, turismo serrano y vida comunitaria. La portada ahora refleja mejor ese contexto.',
                                 config_json={
                                     'eyebrow': 'Descubrí',
                                     'items': [
                                         {'title': 'Sierras y valles', 'text': 'La identidad visual toma referencias del relieve quebrado, los cerros y los valles amplios propios de Lavalleja.'},
                                         {'title': 'Producción rural', 'text': 'El contenido simula una agenda vinculada a ganadería, chacras, logística local y apoyo a productores.'},
                                         {'title': 'Turismo serrano', 'text': 'Se integran referencias al departamento y a sus paisajes como parte del relato municipal.'},
                                         {'title': 'Servicios de cercanía', 'text': 'La home pone foco en alumbrado, mantenimiento, cultura barrial y atención cotidiana al vecino.'}
                                     ]
                                 }, is_active=True))

    if not PageBlock.query.filter_by(page_type='home', block_type='meetings_preview').first():
        db.session.add(PageBlock(page_type='home', block_type='meetings_preview', order_index=6,
                                 title='Sesiones del Concejo', subtitle='Participación ciudadana', is_active=True))
    
    if not PageBlock.query.filter_by(page_type='home', block_type='featured_news').first():
        db.session.add(PageBlock(page_type='home', block_type='featured_news', order_index=4,
                                 title='Actualidad', subtitle='Obras, servicios y vida local en clave serrana', config_json={'cta_label': 'Ver agenda completa'}, is_active=True))

    if not PageBlock.query.filter_by(page_type='home', block_type='events_preview').first():
        db.session.add(PageBlock(page_type='home', block_type='events_preview', order_index=4,
                                 title='Agenda local', subtitle='Actividades comunitarias y servicios en Batlle y Ordóñez', is_active=True))
    
    if not PageBlock.query.filter_by(page_type='home', block_type='authorities').first():
        db.session.add(PageBlock(page_type='home', block_type='authorities', order_index=7,
                                 title='El Concejo', subtitle='Autoridades del municipio', config_json={'text': 'El seed toma como referencia al alcalde Conrado Da Cunha y simula un equipo municipal enfocado en obras, cultura, deporte y articulación con el medio rural.'}, is_active=True))
    
    # Categories
    cat = NewsCategory.query.filter_by(slug='general').first()
    if not cat:
        cat = NewsCategory(name='General', slug='general')
        db.session.add(cat)
    
    db.session.flush()

    # News
    if NewsPost.query.count() == 0:
        news_items = [
            ('Comienza una nueva etapa de mantenimiento en caminería rural', 'mantenimiento-camineria-rural-batlle-ordonez', 'Se priorizan tramos de acceso a predios y puntos de circulación vecinal para mejorar conectividad y seguridad.', lavalleja_images['valle']),
            ('Batlle y Ordóñez prepara agenda cultural de invierno', 'agenda-cultural-invierno-batlle-ordonez', 'El municipio coordina actividades en espacios comunitarios con talleres, propuestas artísticas y encuentros para familias.', lavalleja_images['santa_elena']),
            ('Refuerzo de alumbrado y recuperación de espacios públicos', 'refuerzo-alumbrado-recuperacion-espacios-publicos', 'Se avanza en luminarias, pintura, podas y acondicionamiento de zonas de uso cotidiano en la localidad.', lavalleja_images['minas']),
            ('Productores y municipio coordinan acciones para la zafra y el invierno', 'coordinacion-zafra-invierno-productores-municipio', 'La planificación local incorpora diálogo con el medio rural, mantenimiento de accesos y apoyo logístico.', lavalleja_images['helada']),
            ('Lavalleja serrana inspira la nueva imagen del sitio municipal', 'nueva-imagen-sitio-municipal-lavalleja-serrana', 'La web adopta fondos y referencias visuales más cercanas al paisaje, la escala y la identidad del departamento.', lavalleja_images['arequita']),
        ]
        for index, (title, seo_slug, excerpt, image_url) in enumerate(news_items, start=1):
            cover_img = create_dummy_media(image_url, f'news-{index}.jpg')
            post = NewsPost(
                title=title,
                slug=ensure_unique_slug(NewsPost, 'slug', slugify(seo_slug, 320), max_length=320),
                excerpt=excerpt,
                content_html=f'<p>{excerpt}</p><p>La noticia se presenta como contenido de ejemplo plausible para una localidad del interior de Lavalleja, listo para ser sustituido luego por publicaciones reales del municipio.</p>',
                status='published',
                published_at=datetime.utcnow() - timedelta(days=index),
                cover_media_id=cover_img.id,
                category_id=cat.id
            )
            db.session.add(post)

    # Events
    if Event.query.count() == 0:
        event_items = [
            ('Feria local de productores y emprendedores', lavalleja_images['valle'], 3),
            ('Jornada deportiva y recreativa en espacios comunitarios', lavalleja_images['sierras'], 8),
            ('Encuentro abierto sobre servicios y caminería local', lavalleja_images['quarry'], 14),
        ]
        for index, (title, image_url, days_until) in enumerate(event_items, start=1):
            evt_cover = create_dummy_media(image_url, f'evt-{index}.jpg')
            evt = Event(
                title=title,
                slug=f'batlle-evento-{index}',
                start_datetime=datetime.utcnow() + timedelta(days=days_until),
                location_name='Centro comunal y espacios públicos de la localidad',
                latitude=site.latitude,
                longitude=site.longitude,
                description_html='<p>Actividad comunitaria pensada para una localidad serrana del departamento de Lavalleja, cargada como ejemplo realista para la agenda municipal.</p>',
                status='published',
                cover_media_id=evt_cover.id
            )
            db.session.add(evt)

    # Meetings
    if MunicipalMeeting.query.count() == 0:
        mtg = MunicipalMeeting(
            title='Sesión abierta del Concejo Municipal de Batlle y Ordóñez',
            meeting_datetime=datetime.utcnow() + timedelta(days=2),
            location_name='Sala de Sesiones',
            address='Municipio de Batlle y Ordóñez',
            description='Instancia abierta para seguimiento de caminería, alumbrado, actividades locales, espacios públicos y coordinación con vecinos.',
            is_public=True,
            status='scheduled'
        )
        db.session.add(mtg)

    # Authorities
    if Authority.query.count() == 0:
        auth_photo = create_dummy_media('https://mediospublicos.uy/wp-content/uploads/2025/05/497454266_122225210306037412_5156012987764073870_nuuuu.jpg', 'conrado-da-cunha.jpg')
        auth = Authority(
            name='Conrado Da Cunha',
            role='Alcalde',
            bio='Autoridad principal del seed, con una presentación institucional alineada a la realidad de un municipio del interior lavallejino.',
            order_index=1,
            photo_media_id=auth_photo.id
        )
        db.session.add(auth)

        auth_photo2 = create_dummy_media(lavalleja_images['arequita'], 'concejal-cultura.jpg')
        auth2 = Authority(
            name='Rosana Techera',
            role='Concejala',
            bio='Integra el equipo municipal en este seed con foco en cultura local, articulación comunitaria y actividades barriales.',
            order_index=2,
            photo_media_id=auth_photo2.id
        )
        db.session.add(auth2)

        auth_photo3 = create_dummy_media(lavalleja_images['sierras'], 'concejal-servicios.jpg')
        auth3 = Authority(
            name='Mauricio Correa',
            role='Concejal',
            bio='Referencia simulada para acompañar al alcalde en temas de servicios, mantenimiento y seguimiento territorial.',
            order_index=3,
            photo_media_id=auth_photo3.id
        )
        db.session.add(auth3)

    # Forms
    if not CustomForm.query.filter_by(slug='contacto').first():
        cf = CustomForm(title='Contacto General', slug='contacto', description='Mándanos tu mensaje',
                        is_active=True, notify_emails='test@test.com')
        db.session.add(cf)

    db.session.commit()
    click.echo('Datos de prueba (seed) insertados exitosamente.')
