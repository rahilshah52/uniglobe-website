import code
from unicodedata import category

from markupsafe import Markup
from flask import Flask, render_template, request, redirect, flash, url_for, session, g, has_request_context
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import os
import json
import collections
import itertools
import re
from werkzeug.utils import secure_filename
from PIL import Image, ImageOps

# List of product categories (editable!)
categories = ['bedroom', 'living', 'dining', 'modular', 'lighting', 'sanitaryware', 'premium']
# Put this near the top or in a global config section
homepage_display = {
    'bedroom': 'images/bedroom/bed 15.webp',
    'living': 'images/living/living_room 19.webp',
    'dining': 'images/dining/tables_catalog_18_1.webp',
    'modular': 'images/modular/plywood_cabinet 17.webp',
    'lighting': 'images/lighting/lighting 1.webp',
    'sanitaryware': 'images/optimized/sanitaryware-feature.webp',
    'premium': 'images/premium/baxter_2_128_5.webp'
}
homepage_display_names = {
    'bedroom': 'Bedroom & Bed',
    'living': 'Lounge Seating',
    'dining': 'Dining & Coffee Tables',
    'modular': 'Modular Cabinets',
    'lighting': 'Lightings & Fixtures',
    'sanitaryware': 'Sanitaryware',
    'premium': 'Premium Collection',
}

surface_collections = [
    {
        'name': 'Double Charge · 800 × 800 mm',
        'description': 'A bold square format from the 2026 Double Charge collection.',
        'image': 'images/surfaces/catalog/double-charge-800-room.jpg',
        'alt': 'Bright dining space finished with large square porcelain floor tiles',
    },
    {
        'name': 'Digital Full Body',
        'description': 'Stone-inspired full-body surfaces in versatile contemporary formats.',
        'image': 'images/surfaces/catalog/digital-fullbody-living.jpg',
        'alt': 'Contemporary living room with warm stone-look full-body tiles',
    },
    {
        'name': 'Step & Riser',
        'description': 'Coordinated tile designs that carry a material story across staircases.',
        'image': 'images/surfaces/catalog/fullbody-step-riser.jpg',
        'alt': 'Full-body tile design shown across a contemporary staircase',
    },
    {
        'name': 'Regular Full Body · 2026',
        'description': 'A broad palette of full-body designs for residential and commercial spaces.',
        'image': 'images/surfaces/catalog/regular-fullbody-interior.jpg',
        'alt': 'Modern dining interior featuring full-body floor tiles',
    },
    {
        'name': 'Punch Matt',
        'description': 'Textured 5 mm surfaces with a crisp, tactile matt finish.',
        'image': 'images/surfaces/catalog/punch-matt-exterior.jpg',
        'alt': 'Contemporary exterior finished with matt tiles',
    },
    {
        'name': 'Carving Matt',
        'description': 'Textured 5 mm surfaces with expressive carved detail.',
        'image': 'images/surfaces/catalog/carving-matt-bedroom.jpg',
        'alt': 'Contemporary bedroom with textured dark matt wall tiles',
    },
    {
        'name': 'Radiant Shade Matt',
        'description': 'Colour-led matt surfaces for a more expressive material palette.',
        'image': 'images/surfaces/catalog/radiant-shade-interior.jpg',
        'alt': 'Warm contemporary interior from the Radiant Shade Matt catalogue',
    },
]

# Catalog highlights shown as a single, image-led tile lookbook.
# Product details here follow the supplied catalogues; enquiries confirm stock.
tile_lookbook_products = [
    {'name': 'Olimpia Beige', 'group': 'Digital Full Body', 'description': 'A warm beige stone look with delicate, natural-looking movement.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/olimpia-beige.jpg'},
    {'name': 'Olimpia Black', 'group': 'Digital Full Body', 'description': 'A deep, dramatic black surface with understated stone veining.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/olimpia-black.jpg'},
    {'name': 'Olimpia Cookie', 'group': 'Digital Full Body', 'description': 'A gentle cookie-toned stone look for a softer, warmer palette.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/olimpia-cookie.jpg'},
    {'name': 'Olimpia Grey White', 'group': 'Digital Full Body', 'description': 'A light grey-white base with fine, flowing stone detail.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/olimpia-grey-white.jpg'},
    {'name': 'Regal Black', 'group': 'Digital Full Body', 'description': 'A rich black design with expressive pale veins.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/regal-black.jpg'},
    {'name': 'Regal XL White', 'group': 'Digital Full Body', 'description': 'A bright white stone look with softly defined grey movement.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/regal-xl-white.jpg'},
    {'name': 'Smoky Cool Beige', 'group': 'Digital Full Body', 'description': 'A calm beige palette with a subtle smoky stone pattern.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/smoky-cool-beige.jpg'},
    {'name': 'Smoky Cool Black', 'group': 'Digital Full Body', 'description': 'A charcoal-black stone look with a softly clouded finish.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/smoky-cool-black.jpg'},
    {'name': 'Smoky Cool Brown', 'group': 'Digital Full Body', 'description': 'A warm brown stone palette with gentle tonal variation.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/smoky-cool-brown.jpg'},
    {'name': 'Traver Beige', 'group': 'Digital Full Body', 'description': 'A softly layered beige stone look for understated interiors.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/traver-beige.jpg'},
    {'name': 'Traver Grey White', 'group': 'Digital Full Body', 'description': 'A cool light stone design with graceful grey detailing.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/traver-grey-white.jpg'},
    {'name': 'Bali Stone Black', 'group': 'Digital Full Body', 'description': 'A dark stone-inspired surface with a strong, grounded character.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/bali-stone-black.jpg'},
    {'name': 'Bali Stone Brown', 'group': 'Digital Full Body', 'description': 'A warm brown stone look with subtle tonal shifts.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/bali-stone-brown.jpg'},
    {'name': 'Bruno Black', 'group': 'Digital Full Body', 'description': 'A deep black design with a distinctive natural stone pattern.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/bruno-black.jpg'},
    {'name': 'Calcutta Gold Quartz', 'group': 'Digital Full Body', 'description': 'A bright stone look with warm golden accents.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/calcutta-gold-quartz.jpg'},
    {'name': 'Zebrano Black', 'group': 'Digital Full Body', 'description': 'A striking black surface with expressive linear character.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/zebrano-black.jpg'},
    {'name': 'Imperia Quartz', 'group': 'Digital Full Body', 'description': 'A refined quartz-inspired look in a light, balanced palette.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/imperia-quartz.jpg'},
    {'name': 'Muretto Beige', 'group': 'Digital Full Body', 'description': 'A soft beige stone look suited to warm, quiet palettes.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/muretto-beige.jpg'},
    {'name': 'Oxan Beige', 'group': 'Digital Full Body', 'description': 'A natural beige design with gentle stone-like variation.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/oxan-beige.jpg'},
    {'name': 'Oxan Quartz', 'group': 'Digital Full Body', 'description': 'A cool quartz-inspired surface with considered tonal detail.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/oxan-quartz.jpg'},
    {'name': 'Turkish Grey White', 'group': 'Digital Full Body', 'description': 'A light grey-white design with soft, flowing stone movement.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/turkish-grey-white.jpg'},
    {'name': 'Urban Latte', 'group': 'Regular Full Body', 'description': 'A quiet, warm neutral shown in a contemporary interior setting.', 'details': '600 × 1200 mm · Matt', 'image': 'images/surfaces/catalog/products/urban-latte.jpg'},
    {'name': 'Quartzite White', 'group': '5 mm · Punch Matt', 'description': 'A white quartzite-inspired design with delicate linear movement.', 'details': '600 × 1200 mm · 5 mm · Granulla', 'image': 'images/surfaces/catalog/products/quartzite-white-punch.jpg'},
    {'name': 'Panda White', 'group': '5 mm · Carving Matt', 'description': 'A distinctive white marble look with sweeping dark veins.', 'details': '600 × 1200 mm · 5 mm · Rustic Matt Carving', 'image': 'images/surfaces/catalog/products/panda-white-carving.jpg'},
    {'name': 'Travertino Ivory', 'group': '5 mm · Carving Matt', 'description': 'An ivory travertine look with softly layered linear character.', 'details': '600 × 1200 mm · 5 mm · Granulla Carving / Punch', 'image': 'images/surfaces/catalog/products/travertino-ivory-carving.jpg'},
    {'name': 'Urban Dove', 'group': 'Regular Full Body', 'description': 'A soft dove-grey look from the Urban series, shown in a finished outdoor setting.', 'details': '600 × 1200 mm · Matt / Polished / Punch; 600 × 600 mm · Matt / Polished', 'image': 'images/surfaces/catalog/products/urban-dove.jpg'},
    {'name': 'Urban Kota', 'group': 'Regular Full Body', 'description': 'A grounded natural grey from the Urban series.', 'details': '600 × 1200 mm · Matt / Polished / Punch; 600 × 600 mm · Matt / Polished', 'image': 'images/surfaces/catalog/products/urban-kota.jpg'},
    {'name': 'Urban XL Grey', 'group': 'Regular Full Body', 'description': 'A contemporary grey surface with a calm, even appearance.', 'details': '600 × 1200 mm · Matt / Punch / Polished; 600 × 600 mm · Matt / Polished', 'image': 'images/surfaces/catalog/products/urban-xl-grey.jpg'},
    {'name': 'Urban Dark Grey', 'group': 'Regular Full Body', 'description': 'A deeper grey from the Urban series for a more defined palette.', 'details': '600 × 1200 mm · Matt / Punch; 600 × 600 mm · Matt', 'image': 'images/surfaces/catalog/products/urban-dark-grey.jpg'},
    {'name': 'Leonardo Grey White', 'group': 'Regular Full Body', 'description': 'A light grey-white design with quiet stone movement.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/leonardo-grey-white.jpg'},
    {'name': 'Leonardo Beige', 'group': 'Regular Full Body', 'description': 'A warm neutral with a gentle, natural stone character.', 'details': '600 × 1200 mm · Matt / Polished; 600 × 1000 / 600 × 900 mm · Matt; 600 × 600 mm · Matt / Polished', 'image': 'images/surfaces/catalog/products/leonardo-beige.jpg'},
    {'name': 'Leonardo Quartz', 'group': 'Regular Full Body', 'description': 'A refined quartz-inspired surface in balanced neutral tones.', 'details': '600 × 1200 mm · Matt / Polished; 600 × 1000 / 600 × 900 mm · Matt; 600 × 600 mm · Matt / Polished', 'image': 'images/surfaces/catalog/products/leonardo-quartz.jpg'},
    {'name': 'Leonardo Cookie', 'group': 'Regular Full Body', 'description': 'A soft cookie-toned design with understated variation.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/leonardo-cookie.jpg'},
    {'name': 'Aspire Sand', 'group': 'Regular Full Body', 'description': 'A sandy neutral tone from the Aspire series.', 'details': '600 × 1200 mm · Matt / Punch', 'image': 'images/surfaces/catalog/products/aspire-sand.jpg'},
    {'name': 'Leonardo Black', 'group': 'Regular Full Body', 'description': 'A deep black surface with a composed stone-like character.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 mm · Matt', 'image': 'images/surfaces/catalog/products/leonardo-black.jpg'},
    {'name': 'Leonardo Brown', 'group': 'Regular Full Body', 'description': 'A rich brown surface with warm, natural-looking movement.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 · 600 × 600 mm · Matt', 'image': 'images/surfaces/catalog/products/leonardo-brown.jpg'},
    {'name': 'Leonardo Nero', 'group': 'Regular Full Body', 'description': 'A deep nero finish for a crisp, architectural palette.', 'details': '600 × 1200 · 600 × 1000 · 600 × 900 · 600 × 600 mm · Matt', 'image': 'images/surfaces/catalog/products/leonardo-nero.jpg'},
    {'name': 'Infinity White', 'group': 'Regular Full Body', 'description': 'A clean, bright surface in the Infinity series.', 'details': '600 × 1200 · 600 × 600 mm · Matt / Polished', 'image': 'images/surfaces/catalog/products/infinity-white.jpg'},
    {'name': 'Infinity Black', 'group': 'Regular Full Body', 'description': 'A crisp black surface from the Infinity series.', 'details': '600 × 1200 · 600 × 600 mm · Matt', 'image': 'images/surfaces/catalog/products/infinity-black.jpg'},
]

_punch_products = [
    ('Quartzite Black', 23), ('Quartzite Light Grey', 25), ('Quartzite Dark Grey', 27), ('Quartzite Brown', 29), ('Quartzite Ivory', 31),
    ('Jasper Beige', 33), ('Jasper Brown', 35), ('Jasper Black', 37), ('Jasper Ivory', 39), ('Jasper Grey', 41), ('Jasper Bianco', 43), ('Jasper Slate Grey', 45),
    ('Linear White', 50), ('Linear Black', 52), ('Linear Dark Grey', 54), ('Linear Light Grey', 56), ('Linear Brown', 58), ('Linear Ivory', 60),
    ('Afyon Statuario', 62), ('Spanish Black', 64), ('Ethos Grey', 66), ('Ethos Beige', 68), ('Ethos Brown', 70), ('Ethos Black', 72), ('Ethos Ivory', 74), ('Ethos Bianco', 76), ('Ethos Ash Grey', 78),
    ('Dimona Black', 84), ('Dimona Beige', 85), ('Dimona Bianco', 86), ('Dimona Crema', 87), ('Dimona Coffie Brown', 88),
]
for _name, _page in _punch_products:
    _slug = re.sub(r'[^a-z0-9]+', '-', _name.lower()).strip('-')
    tile_lookbook_products.append({
        'name': _name, 'group': '5 mm · Punch Matt', 'catalog_page': _page,
        'description': f'{_name} is a 5 mm full-body tile design from the Punch Matt collection.',
        'details': '600 × 1200 mm · 5 mm · Granulla Punch Matt',
        'image': f'images/surfaces/catalog/products/{_slug}.jpg',
    })

_carving_products = [
    ('Gold Travertine', 36, 'Granulla Carving / Punch'), ('Ether Bianco', 38, 'Satin'),
    ('Ether Natural', 40, 'Satin'), ('Ether Dusky', 41, 'Satin'), ('Ether Ivory', 42, 'Satin'),
    ('Nebula White', 43, 'Satin'), ('Nebula Natural', 44, 'Satin'), ('Nebula Dark Grey', 46, 'Satin'), ('Nebula Grey', 47, 'Satin'),
]
for _name, _page, _finish in _carving_products:
    _slug = re.sub(r'[^a-z0-9]+', '-', _name.lower()).strip('-')
    tile_lookbook_products.append({
        'name': _name, 'group': '5 mm · Carving Matt', 'catalog_page': _page,
        'description': f'{_name} is a 5 mm full-body tile design from the Carving Matt collection.',
        'details': f'600 × 1200 mm · 5 mm · {_finish}',
        'image': f'images/surfaces/catalog/products/{_slug}.jpg',
    })

_radiant_products = [
    ('Elite Ash Grey', 10), ('Elite Black', 13), ('Elite Dark Grey', 16), ('Elite Dove Grey', 19),
    ('Elite Grey', 22), ('Elite Smoke Grey', 25), ('Elite Steel', 28), ('Elite Warm', 31),
    ('Elite White', 34), ('Elite Ivory', 37), ('Elite Limoncello', 43), ('Elite Maldives', 46),
    ('Elite Mushroom', 49), ('Elite Ocean Green', 52), ('Elite Ocher', 55), ('Elite Redwine', 58),
    ('Elite Saphire', 61), ('Elite Turquoise', 64), ('Elite Olive', 67), ('Elite Peach', 70),
    ('Elite Sky', 73), ('Elite Avocado', 76), ('Elite Bali', 79),
]
for _name, _page in _radiant_products:
    _slug = re.sub(r'[^a-z0-9]+', '-', _name.lower()).strip('-')
    tile_lookbook_products.append({
        'name': _name, 'group': 'Radiant Shade Matt', 'catalog_page': _page,
        'description': f'{_name} is a color-led design in the Radiant Shade Matt range.',
        'details': '600 × 1200 mm · 5 mm · Matt range; finish varies by design',
        'image': f'images/surfaces/catalog/products/{_slug}.jpg',
    })

_mto_products = [
    ('Terrazzo Lite', 7, 'Rustic Matt / Carving'), ('Graphito Black', 19, 'Granulla'),
    ('Flaxcoat Charcoal', 37, 'Rustic Matt'), ('Flaxcoat Snowy', 38, 'Granulla'),
    ('Flaxcoat Raddle', 39, 'Rustic Matt'), ('Flaxcoat Blank', 40, 'Rustic Matt'),
    ('Flaxcoat Pallia', 41, 'Rustic Matt'), ('Ignite Natural', 42, 'Granulla'),
    ('Ignite Verde', 43, 'Granulla'), ('Ignite Nero', 44, 'Granulla'),
    ('Crystal Blue', 45, 'Satin'), ('Crystal White', 46, 'Satin'),
    ('Gracile Cream', 48, 'Granulla'), ('Statuario White', 49, 'Rustic Matt'),
    ('Bottochino Crema', 50, 'Granulla'),
]
for _name, _page, _finish in _mto_products:
    _slug = re.sub(r'[^a-z0-9]+', '-', _name.lower()).strip('-')
    tile_lookbook_products.append({
        'name': _name, 'group': 'MTO Catalogue Designs', 'catalog_page': _page,
        'description': f'{_name} is a 5 mm full-body tile design listed in the supplied MTO catalogue.',
        'details': f'600 × 1200 mm · 5 mm · {_finish}; confirm current availability',
        'image': f'images/surfaces/catalog/products/{_slug}.jpg',
    })


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

UPLOAD_FOLDER = os.path.join(app.static_folder, "uploads")
DATA_FILE = os.path.join(app.static_folder, "data", "products.json")
SURFACE_DATA_FILE = os.path.join(app.static_folder, "data", "surface_products.json")
SURFACE_BRANDS_FILE = os.path.join(app.static_folder, "data", "surface_brands.json")
TILE_SERIES_FILE = os.path.join(app.static_folder, "data", "tile_series.json")
TILE_FACETS_FILE = os.path.join(app.static_folder, "data", "tile_facets.json")
TILE_HOME_FEATURED_FILE = os.path.join(app.static_folder, "data", "tiles_home_featured.json")

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

# Email configuration
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME='uniglobelifestyles@gmail.com',
    MAIL_PASSWORD='gmnh dwdq hsrm bnrf',  # Consider using environment variables
    MAIL_DEFAULT_SENDER='uniglobelifestyles@gmail.com'
)

mail = Mail(app)


class _HttpsBehindProxy:
    """Keep links and canonical URLs on https when the host forwards secure requests."""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        if environ.get('HTTP_X_FORWARDED_PROTO', '').lower() == 'https' or environ.get('HTTPS', '').lower() == 'on':
            environ['wsgi.url_scheme'] = 'https'
        return self.wsgi_app(environ, start_response)


app.wsgi_app = _HttpsBehindProxy(app.wsgi_app)

@app.route('/')
def home():
    return render_template('index1.html', homepage_display=homepage_display, homepage_display_names=homepage_display_names)

BATH_BRAND_DEFAULTS = {
    'simpolo': {'image': 'images/sanitaryware/catalog/simpolo-bathroom-suite.jpg',
                'description': 'Wall-hung and floor-standing sanitaryware, basins and bath fittings, designed to pair with Simpolo tiles.'},
}


def bath_brand_view(record):
    """A brand as shown in the bath section: tile-and-bath brands get their own bath picture and text."""
    defaults = BATH_BRAND_DEFAULTS.get(record.get('slug'), {}) if record.get('department') == 'both' else {}
    return {**record,
            'image': record.get('bath_image') or defaults.get('image') or record.get('image', ''),
            'description': record.get('bath_description') or defaults.get('description') or record.get('description', '')}


@app.route('/tiles')
def tiles_home():
    brands = [bath_brand_view(item) for item in load_surface_brands() if item.get('active', True) and item.get('department') in {'bathware', 'both'}]
    series_groups, _, _ = get_series_brand_groups()
    brand_series = next((group for group in series_groups if group['brand'] != 'Uniglobe'), None)
    if brand_series:
        brand_series = {**brand_series, 'series': sorted(brand_series['series'], key=lambda item: -item['count'])[:12],
                        'slug': tile_product_slug(brand_series['brand']), 'total': len(brand_series['series'])}
    return render_template('tiles_home.html', surface_collections=get_homepage_featured_series(), brands=brands, brand_series=brand_series)

def get_bath_categories():
    bath_categories = [
        {
            'slug': 'showers-fittings', 'number': '01', 'title': 'Showers & fittings',
            'description': 'A considered selection of showering and bath fittings, from statement showers to the finishing details.',
            'image': 'images/sanitaryware/catalog/jaquar-shower-setting.jpg',
            'alt': 'Jaquar shower setting in a contemporary bathroom',
            'items': [('Jaquar', 'jaquar-shower-setting.jpg', 'A contemporary shower setting'), ('KOHLER', 'kohler-shower-setting.jpg', 'A considered showering space'), ('KOHLER', 'kohler-shower-fitting.jpg', 'Shower fitting in a refined finish')],
        },
        {
            'slug': 'basins-faucets', 'number': '02', 'title': 'Basins & faucets',
            'description': 'Explore basin forms and faucet details for a calm, cohesive bathroom scheme.',
            'image': 'images/sanitaryware/catalog/jaquar-basin-setting.jpg',
            'alt': 'Jaquar basin and faucet setting',
            'items': [('Jaquar', 'jaquar-basin-setting.jpg', 'Basin and faucet setting'), ('Jaquar', 'jaquar-basin-room.jpg', 'Basin within a contemporary bathroom'), ('Jaquar', 'jaquar-faucet-detail.jpg', 'Faucet finish detail'), ('KOHLER', 'kohler-basin-setting.jpg', 'Basin setting'), ('KOHLER', 'kohler-vanity-setting.jpg', 'Vanity and basin composition'), ('Simpolo', 'simpolo-basin-setting.jpg', 'Basin collection inspiration'), ('Simpolo', 'simpolo-pedestal-basin.jpg', 'Pedestal basin inspiration')],
        },
        {
            'slug': 'sanitaryware', 'number': '03', 'title': 'Sanitaryware',
            'description': 'Clean-lined sanitaryware ideas shown in finished spaces and catalogue selections.',
            'image': 'images/sanitaryware/catalog/kohler-sanitaryware-setting.jpg',
            'alt': 'KOHLER sanitaryware in a finished bathroom',
            'items': [('KOHLER', 'kohler-sanitaryware-setting.jpg', 'Sanitaryware in a contemporary interior'), ('KOHLER', 'kohler-toilet-feature.jpg', 'Sanitaryware detail'), ('Simpolo', 'simpolo-sanitaryware-feature.jpg', 'Sanitaryware catalogue inspiration'), ('Simpolo', 'simpolo-bathroom-suite.jpg', 'Bathroom suite inspiration')],
        },
        {
            'slug': 'baths-wellness', 'number': '04', 'title': 'Baths & wellness',
            'description': 'A softer, more restorative direction for bathing spaces, with sculptural forms and warm materials.',
            'image': 'images/sanitaryware/catalog/kohler-bathing-space.jpg',
            'alt': 'KOHLER bathing space with freestanding tub',
            'items': [('KOHLER', 'kohler-bathing-space.jpg', 'Bathing space with freestanding tub'), ('KOHLER', 'kohler-bathroom-suite.jpg', 'Complete bathroom suite'), ('Simpolo', 'simpolo-bathroom-suite.jpg', 'Bathroom suite inspiration')],
        },
        {
            'slug': 'kitchen', 'number': '05', 'title': 'Kitchen',
            'description': 'Kitchen sinks, faucets and accessories that work as hard as they look.',
            'image': 'images/sanitaryware/catalog/kohler-kitchen-setting.webp',
            'alt': 'KOHLER kitchen faucet over a stainless steel sink',
            'items': [('KOHLER', 'kohler-kitchen-setting.webp', 'Kitchen faucet and sink setting')],
        },
        {
            'slug': 'accessories-mirrors', 'number': '06', 'title': 'Accessories & mirrors',
            'description': 'Mirrors, cabinets, vanities and the finishing accessories that complete a bathroom.',
            'image': 'images/sanitaryware/catalog/kohler-accessories-setting.webp',
            'alt': 'KOHLER mirror, vanity and accessories in a finished bathroom',
            'items': [('KOHLER', 'kohler-accessories-setting.webp', 'Mirror, vanity and accessories')],
        },
    ]
    for category in bath_categories:
        category['items'] = [
            {'brand': brand, 'image': f'images/sanitaryware/catalog/{image}', 'caption': caption}
            for brand, image, caption in category['items']
        ]
    bath_settings = load_tile_facet_config().get('bathware-category', {})
    bath_legacy_overrides = bath_settings.get('images', {})
    bath_card_overrides = {**bath_legacy_overrides, **bath_settings.get('card_images', {})}
    bath_hero_overrides = {**bath_legacy_overrides, **bath_settings.get('hero_images', {})}
    for category in bath_categories:
        default_image = category['image']
        if bath_card_overrides.get(category['slug']):
            category['image'] = bath_card_overrides[category['slug']]
        category['hero_image'] = bath_hero_overrides.get(category['slug']) or default_image
        category['thumbnail'] = card_image_path(category['image'])
        category['image_is_portrait'] = is_portrait_surface_image(category['image'])
    return bath_categories

@app.route('/tiles/bath')
def tiles_bath():
    bath_categories = get_all_bath_categories()
    brands = [bath_brand_view(item) for item in load_surface_brands() if item.get('active', True) and item.get('department') in {'bathware', 'both'}]
    return render_template('tiles_bath.html', bath_categories=bath_categories, brands=brands)


# ---------------------------------------------------------------------------
# Bathware products
# A bathware product can carry, next to the normal manager fields:
#   collection  - range / series name (e.g. "Vive")
#   type        - product type used for filtering (e.g. "Wall hung toilet")
#   sku         - manufacturer code shown on the page
#   variants    - [{"name", "swatch" (hex colour or image path), "sku", "images": [...]}]
#   features    - list of short feature lines
#   specs       - [[label, value], ...]
# Products saved from /tiles/manage without these fields still work.
# ---------------------------------------------------------------------------

def get_public_bath_products():
    """Bathware products that may be shown publicly (brand active, not removed, has photos)."""
    brands = {str(item.get('name', '')).strip().lower(): item for item in load_surface_brands()}
    products = []
    for product in load_surface_products():
        if product.get('department') != 'bathware' or product.get('brand_removed') or not product.get('images'):
            continue
        brand_name = str(product.get('brand', '')).strip()
        if brand_name and brand_name != 'Other / not specified':
            brand = brands.get(brand_name.lower())
            if not (brand and brand.get('active', True) and brand.get('department') in {'bathware', 'both'}):
                continue
        products.append(product)
    return products


def bath_product_variants(product):
    """Colour variants limited to photos that still exist on the product."""
    images = product.get('images', [])
    available = set(images)
    variants = []
    for variant in product.get('variants') or []:
        variant_images = [image for image in variant.get('images', []) if image in available]
        if variant_images:
            variants.append({**variant, 'images': variant_images})
    if not variants:
        cover = get_surface_product_cover(product)
        variants = [{'name': '', 'swatch': '', 'sku': product.get('sku', ''), 'images': [cover] + [image for image in images if image != cover]}]
    return variants


def bath_swatch_style(swatch):
    if not swatch:
        return ''
    if swatch.startswith('#'):
        return f'background:{swatch}'
    return f"background-image:url('{url_for('static', filename=swatch)}')"


def bath_product_card(product, category_title=None):
    variants = bath_product_variants(product)
    first = variants[0]
    return {
        'code': product.get('code'),
        'title': product.get('title', 'Bathware product'),
        'brand': product.get('brand', ''),
        'collection': product.get('collection', ''),
        'type': product.get('type') or category_title or product.get('category', ''),
        'category': product.get('category', ''),
        'image': first['images'][0],
        'thumbnail': card_image_path(first['images'][0]),
        'variants': [{'name': v.get('name', ''), 'style': bath_swatch_style(v.get('swatch', '')),
                      'thumbnail': card_image_path(v['images'][0])} for v in variants if v.get('name')],
    }


def get_all_bath_categories():
    """Bath categories with their inspiration images and, separately, one card per product."""
    bath_categories = get_bath_categories()
    active_bath_brands = {item['name'].lower() for item in load_surface_brands() if item.get('active', True) and item.get('department') in {'bathware', 'both'}}
    for category in bath_categories:
        category['items'] = [item for item in category['items'] if item['brand'].lower() in active_bath_brands]
        category['products'] = []
    categories_by_name = {item['title'].lower(): item for item in bath_categories}
    for product in get_public_bath_products():
        title = product.get('category') or 'Other bathware'
        key = title.lower()
        category = categories_by_name.get(key)
        if category is None:
            cover = get_surface_product_cover(product)
            category = {'slug': tile_product_slug(title), 'number': f'{len(bath_categories) + 1:02d}', 'title': title,
                        'description': f'Explore {title.lower()} from the brands available in our showroom.',
                        'image': cover or 'images/sanitaryware/catalog/kohler-bathroom-suite.jpg',
                        'hero_image': cover or 'images/sanitaryware/catalog/kohler-bathroom-suite.jpg',
                        'alt': f'{title} from our bathware collection', 'items': [], 'products': []}
            category['image_is_portrait'] = is_portrait_surface_image(category['image'])
            bath_categories.append(category)
            categories_by_name[key] = category
        category['products'].append(product)
    for category in bath_categories:
        category['image'] = card_image_path(category.get('image', ''))
        category['thumbnail'] = category.get('thumbnail') or category['image']
        category['product_count'] = len(category['products'])
        for item in category['items']:
            item['thumbnail'] = card_image_path(item.get('image', ''))
    return bath_categories


def _bath_filter_values(products, key):
    return sorted({str(item.get(key) or '').strip() for item in products if str(item.get(key) or '').strip()}, key=str.lower)


@app.route('/tiles/bath/<slug>')
def tiles_bath_category(slug):
    category = next((item for item in get_all_bath_categories() if item['slug'] == slug), None)
    if category is None:
        return redirect(url_for('tiles_bath'))
    products = category['products']
    selected_brands = [value.strip() for value in request.args.getlist('brand') if value.strip()]
    selected_types = [value.strip() for value in request.args.getlist('type') if value.strip()]
    brand_names = {item['brand'] for item in category['items']} | {str(item.get('brand', '')) for item in products}
    brands = sorted({name for name in brand_names if name}, key=str.lower)
    types = _bath_filter_values([item for item in products if not selected_brands or item.get('brand') in selected_brands], 'type')
    shown = [item for item in products
             if (not selected_brands or item.get('brand') in selected_brands)
             and (not selected_types or item.get('type') in selected_types)]
    cards = [bath_product_card(item, category['title']) for item in shown]
    items = [item for item in category['items'] if not selected_brands or item['brand'] in selected_brands]
    return render_template('tiles_bath_category.html', category=category, brands=brands, types=types,
                           selected_brands=selected_brands, selected_types=selected_types, cards=cards, items=items)


@app.route('/tiles/bath/brand/<brand_slug>')
def tiles_bath_brand(brand_slug):
    brand_record = next((item for item in load_surface_brands() if item.get('slug') == brand_slug.lower() and item.get('active', True) and item.get('department') in {'bathware', 'both'}), None)
    if brand_record is None:
        return redirect(url_for('tiles_bath'))
    brand = brand_record['name']
    selected_categories = [value.strip() for value in request.args.getlist('category') if value.strip()]
    selected_types = [value.strip() for value in request.args.getlist('type') if value.strip()]
    bath_categories = get_all_bath_categories()
    categories = []
    cards, inspiration = [], []
    brand_products = []
    for category in bath_categories:
        own = [item for item in category['products'] if str(item.get('brand', '')).lower() == brand.lower()]
        own_items = [item for item in category['items'] if item['brand'].lower() == brand.lower()]
        if own or own_items:
            categories.append((category['title'], category['slug']))
        if selected_categories and category['slug'] not in selected_categories:
            continue
        brand_products.extend((category, item) for item in own)
        inspiration.extend({**item, 'category': category['title']} for item in own_items)
    types = _bath_filter_values([item for _, item in brand_products], 'type')
    for category, item in brand_products:
        if selected_types and item.get('type') not in selected_types:
            continue
        cards.append(bath_product_card(item, category['title']))
    selected_category_names = [title for title, slug in categories if slug in selected_categories]
    brand_image = bath_brand_view(brand_record).get('image') or f'images/sanitaryware/brands/{brand_slug}-bath-inspiration.jpg'
    return render_template('tiles_bath_brand.html', brand=brand, brand_slug=brand_slug, brand_image=brand_image,
                           cards=cards, inspiration=inspiration, categories=categories, types=types,
                           selected_categories=selected_categories, selected_types=selected_types,
                           selected_category_names=selected_category_names)


@app.route('/tiles/bath/product/<code>')
def tiles_bath_product(code):
    products = get_public_bath_products()
    product = next((item for item in products if item.get('code') == code), None)
    if product is None:
        return redirect(url_for('tiles_bath'))
    category = next((item for item in get_bath_categories() if item['title'].lower() == str(product.get('category', '')).lower()), None)
    category_slug = category['slug'] if category else tile_product_slug(product.get('category') or 'Other bathware')
    variants = bath_product_variants(product)
    requested = request.args.get('colour', '')
    active_index = next((index for index, variant in enumerate(variants) if variant.get('name') and tile_product_slug(variant['name']) == requested), 0)
    view_variants = [{
        'name': variant.get('name', ''),
        'slug': tile_product_slug(variant.get('name', '')) if variant.get('name') else '',
        'style': bath_swatch_style(variant.get('swatch', '')),
        'sku': variant.get('sku', ''),
        'images': [{'src': url_for('static', filename=image), 'thumb': url_for('static', filename=card_image_path(image))} for image in variant['images']],
    } for variant in variants]
    brand_record = next((item for item in load_surface_brands() if item.get('name', '').lower() == str(product.get('brand', '')).lower()), None)
    same_collection = [item for item in products if item is not product and product.get('collection')
                       and item.get('collection') == product.get('collection') and item.get('brand') == product.get('brand')]
    same_type = [item for item in products if item is not product and item not in same_collection
                 and item.get('category') == product.get('category') and item.get('type') == product.get('type')]
    related = [bath_product_card(item) for item in (same_collection + same_type)[:8]]
    return render_template('tiles_bath_product.html', product=product, variants=view_variants, active_index=active_index,
                           category_title=product.get('category') or 'Bathware', category_slug=category_slug,
                           brand_slug=brand_record.get('slug') if brand_record else None,
                           related=related, related_is_collection=bool(same_collection))

def get_tile_category_groups():
    available_series = []
    tile_products = [product for product in load_surface_products() if product.get('department', 'tiles') == 'tiles']
    # Work out each product's tags once for this request instead of once per card.
    tile_products_with_tags = [(product, get_product_tile_tags(product)) for product in tile_products]
    for series_record in load_tile_series():
        if not series_record.get('active', True):
            continue
        representative = next((get_surface_product_cover(product) for product, product_tags in tile_products_with_tags
                               if series_record.get('slug') in product_tags
                               and get_surface_product_cover(product)), None)
        series_image = series_record.get('card_image') or series_record.get('cover_image') or representative or series_record.get('image') or 'images/surfaces/catalog/double-charge-800-room.jpg'
        available_series.append((series_record['name'], series_image))
    groups = [
        {
            'name': 'Location', 'slug': 'location',
            'items': [
                ('Living room tiles', 'images/surfaces/catalog/digital-fullbody-living.jpg'),
                ('Bathroom tiles', 'images/surfaces/catalog/products/traver-grey-white-room.jpg'),
                ('Bedroom tiles', 'images/surfaces/catalog/carving-matt-bedroom.jpg'),
                ('Kitchen tiles', 'images/surfaces/catalog/regular-fullbody-interior.jpg'),
                ('Outdoor tiles', 'images/surfaces/catalog/punch-matt-exterior.jpg'),
                ('Balcony tiles', 'images/surfaces/catalog/digital-fullbody-living.jpg'),
                ('Staircase tiles', 'images/surfaces/catalog/fullbody-step-riser.jpg'),
                ('Elevation tiles', 'images/surfaces/catalog/punch-matt-exterior.jpg'),
                ('Commercial tiles', 'images/surfaces/catalog/products/aspire-sand-room.jpg'),
                ('Countertop tiles', 'images/surfaces/catalog/regular-fullbody-interior.jpg'),
            ],
        },
        {
            'name': 'Look & Feel', 'slug': 'look-feel',
            'items': [
                ('Concrete', 'images/surfaces/catalog/products/urban-xl-grey-room.jpg'),
                ('Decor', 'images/surfaces/catalog/radiant-shade-interior.jpg'),
                ('Marble', 'images/surfaces/catalog/products/traver-grey-white-room.jpg'),
                ('Metallic', 'images/surfaces/catalog/products/elite-black-room.jpg'),
                ('Glossy', 'images/surfaces/catalog/products/bruno-black-room.jpg'),
                ('Rustic', 'images/surfaces/catalog/punch-matt-exterior.jpg'),
                ('Rustic Matt', 'images/surfaces/catalog/punch-matt-exterior.jpg'),
                ('Matt', 'images/surfaces/catalog/products/urban-xl-grey-room.jpg'),
                ('Paper Matt', 'images/surfaces/catalog/radiant-shade-interior.jpg'),
                ('Feather Touch', 'images/surfaces/catalog/carving-matt-bedroom.jpg'),
                ('Stone', 'images/surfaces/catalog/products/bali-stone-black-room.jpg'),
                ('Wood', 'images/surfaces/catalog/products/urban-latte-room.jpg'),
            ],
        },
        {
            'name': 'Color', 'slug': 'color',
            'items': [
                ('Black', 'images/surfaces/catalog/products/bruno-black-room.jpg'),
                ('Grey', 'images/surfaces/catalog/products/elite-ash-grey-room.jpg'),
                ('Special', 'images/surfaces/catalog/carving-matt-bedroom.jpg'),
                ('White', 'images/surfaces/catalog/products/crystal-white.jpg'),
                ('Brown', 'images/surfaces/catalog/products/bali-stone-brown-room.jpg'),
                ('Cream', 'images/surfaces/catalog/products/travertino-ivory.jpg'),
            ],
        },
        {
            'name': 'Size', 'slug': 'size',
            'items': [
                ('1200 × 2780 × 6 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('1198 × 2398 × 9 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('1200 × 2400 × 9 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('1200 × 1800 × 9 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('1198 × 1798 × 9 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('1198 × 1198 × 9 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('798 × 1598 × 9 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('598 × 1198 × 8.5 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('598 × 1198 × 9 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('600 × 1200 × 8.5 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('600 × 600 × 8.5 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('598 × 598 × 9 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('195 × 1200 × 8.5 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('300 × 1200 × 11 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('600 × 600 × 12 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('298 × 600 × 12 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('298 × 298 × 12 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('398 × 398 × 10 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('398 × 800 × 10 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('398 × 398 × 16 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('398 × 800 × 16 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('600 × 600 × 16 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('Rockdeck · 15 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('800 × 2600 × 15 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('800 × 2400 × 15 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('1200 × 1800 × 15 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('800 × 3000 × 15 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('198 × 198 × 8.5 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('58 × 250 × 8.5 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('80 × 344 × 8.5 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('80 × 480 × 8.5 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
                ('73 × 198 × 8.5 mm', 'images/surfaces/catalog/double-charge-800-room.jpg'),
            ],
        },
        {
            'name': 'Series', 'slug': 'collection',
            'items': available_series,
        },
    ]

    # Include sizes already present on saved products so future formats become
    # selectable in the upload manager and available as collection categories.
    known_sizes = {tile_product_slug(name) for name, _ in groups[3]['items']}
    for product in load_surface_products():
        if product.get('department', 'tiles') != 'tiles':
            continue
        for size_name in get_product_tile_sizes(product):
            size_slug = tile_product_slug(size_name)
            if size_slug not in known_sizes:
                groups[3]['items'].append((size_name, 'images/surfaces/catalog/double-charge-800-room.jpg'))
                known_sizes.add(size_slug)
        for tag in product.get('tags', []):
            match = re.fullmatch(r'(\d{2,4})-(\d{2,4})(?:-(\d{1,2}(?:-\d{1,2})?))?-mm', str(tag))
            if match and tag not in known_sizes:
                thickness = f' × {match.group(3).replace("-", ".")}' if match.group(3) else ''
                name = f'{match.group(1)} × {match.group(2)}{thickness} mm'
                groups[3]['items'].append((name, 'images/surfaces/catalog/double-charge-800-room.jpg'))
                known_sizes.add(tag)
    facet_config = load_tile_facet_config()
    for group in groups:
        if group['slug'] != 'collection':
            settings = facet_config.get(group['slug'], {})
            removed = set(settings.get('removed', []))
            renamed = {str(slug): str(name).strip() for slug, name in settings.get('renamed', {}).items()
                       if str(slug).strip() and str(name).strip()}
            stable_slug_by_name = {display_name: original_slug for original_slug, display_name in renamed.items()}
            group['items'] = [(renamed.get(tile_product_slug(name), name), image)
                              for name, image in group['items'] if tile_product_slug(name) not in removed]
            existing = {stable_slug_by_name.get(tile_product_slug(name), tile_product_slug(name))
                        for name, _ in group['items']}
            for option in settings.get('added', []):
                option_name = str(option.get('name', '')).strip()
                option_slug = tile_product_slug(option_name)
                if option_name and option_slug not in removed and option_slug not in existing:
                    group['items'].append((option_name, option.get('image') or 'images/surfaces/catalog/double-charge-800-room.jpg'))
                    existing.add(option_slug)
        group['cards'] = [
            {'name': name, 'image': image, 'default_image': image, 'thumbnail': card_image_path(image),
             'slug': stable_slug_by_name.get(name, tile_product_slug(name)) if group['slug'] != 'collection' else tile_product_slug(name)}
            for name, image in group['items']
        ]
        group_settings = facet_config.get(group['slug'], {})
        legacy_overrides = group_settings.get('images', {})
        cover_overrides = {**legacy_overrides, **group_settings.get('card_images', {})}
        hero_overrides = {**legacy_overrides, **group_settings.get('hero_images', {})}
        for card in group['cards']:
            if cover_overrides.get(card['slug']):
                card['image'] = cover_overrides[card['slug']]
                card['thumbnail'] = card_image_path(card['image'])
            card['hero_image'] = hero_overrides.get(card['slug']) or card['default_image']
            if group['slug'] == 'size':
                # Product tags already include the sizes read from the details text.
                matching_product = next((product for product, product_tags in tile_products_with_tags
                    if card['slug'] in product_tags), None)
                product_image = get_surface_product_cover(matching_product) if matching_product else ''
                card['representative_image'] = card_image_path(product_image) if product_image else ''
    return groups

def load_tile_facet_config():
    try:
        with open(TILE_FACETS_FILE, 'r', encoding='utf-8') as file:
            value = json.load(file)
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}

def save_tile_facet_config(config):
    os.makedirs(os.path.dirname(TILE_FACETS_FILE), exist_ok=True)
    with open(TILE_FACETS_FILE, 'w', encoding='utf-8') as file:
        json.dump(config, file, indent=2, ensure_ascii=False)

@app.route('/tiles/manage/facet', methods=['POST'])
def tiles_manage_facet():
    if not session.get('admin_logged'):
        return redirect(url_for('admin_login', next='tiles_manage'))
    group_slug = request.form.get('group', '').strip()
    action = request.form.get('action', '').strip()
    name = request.form.get('name', '').strip()
    option_slug = request.form.get('option_slug', '').strip()
    valid_groups = {'location', 'look-feel', 'color', 'size'}
    if group_slug not in valid_groups:
        flash('Choose a valid tile category.', 'warning')
        return redirect(url_for('tiles_manage'))
    config = load_tile_facet_config()
    settings = config.setdefault(group_slug, {'added': [], 'removed': []})
    settings.setdefault('added', [])
    settings.setdefault('removed', [])
    if action == 'add':
        if not name or len(name) > 80:
            flash('Enter a category name of up to 80 characters.', 'warning')
            return redirect(url_for('tiles_manage'))
        slug = tile_product_slug(name)
        group = next((item for item in get_tile_category_groups() if item['slug'] == group_slug), None)
        existing = {item['slug'] for item in group['cards']} if group else set()
        duplicate_name = any(item['name'].casefold() == name.casefold() for item in group['cards']) if group else False
        settings['removed'] = [item for item in settings['removed'] if item != slug]
        if slug not in existing and not duplicate_name:
            settings['added'] = [item for item in settings['added'] if tile_product_slug(item.get('name', '')) != slug]
            settings['added'].append({'name': name, 'image': 'images/surfaces/catalog/double-charge-800-room.jpg'})
            save_tile_facet_config(config)
            flash(f'{name} added to {group_slug.replace("-", " ").title()}.', 'success')
        else:
            flash('A category with that name already exists.', 'warning')
    elif action == 'remove' and option_slug:
        settings['added'] = [item for item in settings['added'] if tile_product_slug(item.get('name', '')) != option_slug]
        settings.get('renamed', {}).pop(option_slug, None)
        if option_slug not in settings['removed']:
            settings['removed'].append(option_slug)
        save_tile_facet_config(config)
        flash('Category option removed. Existing product assignments are saved and can be restored by adding the same option again.', 'success')
    elif action == 'rename' and option_slug:
        if not name or len(name) > 80:
            flash('Enter a category name of up to 80 characters.', 'warning')
            return redirect(url_for('tiles_manage'))
        group = next((item for item in get_tile_category_groups() if item['slug'] == group_slug), None)
        target = next((item for item in group['cards'] if item['slug'] == option_slug), None) if group else None
        if not target:
            flash('That category option could not be found.', 'warning')
            return redirect(url_for('tiles_manage'))
        if any(item['slug'] != option_slug and item['name'].casefold() == name.casefold() for item in group['cards']):
            flash('Another option already uses that category name.', 'warning')
            return redirect(url_for('tiles_manage'))
        renamed = settings.setdefault('renamed', {})
        if tile_product_slug(name) == option_slug:
            renamed.pop(option_slug, None)
        else:
            renamed[option_slug] = name
        save_tile_facet_config(config)
        flash(f'{target["name"]} renamed to {name}. Existing product assignments are preserved.', 'success')
    else:
        flash('That category change could not be applied.', 'warning')
    return redirect(url_for('tiles_manage'))

@app.route('/tiles/manage/category-cover', methods=['POST'])
def tiles_manage_category_cover():
    if not session.get('admin_logged'):
        return redirect(url_for('admin_login', next='tiles_manage'))
    group_slug = request.form.get('group', '').strip()
    option_slug = request.form.get('option_slug', '').strip()
    card_choice = request.form.get('card_image_choice', '').strip()
    hero_choice = request.form.get('hero_image_choice', '').strip()
    card_upload = request.files.get('card_image')
    hero_upload = request.files.get('hero_image')
    if group_slug == 'bathware':
        config_group = 'bathware-category'
        department = 'bathware'
        category = next((item for item in get_bath_categories() if item['slug'] == option_slug), None)
    else:
        config_group = group_slug
        department = 'tiles'
        group = next((item for item in get_tile_category_groups() if item['slug'] == group_slug and group_slug in {'location', 'look-feel', 'color'}), None)
        category = next((item for item in group['cards'] if item['slug'] == option_slug), None) if group else None
    if not category:
        flash('Choose a valid image category.', 'warning')
        return redirect(url_for('tiles_manage'))

    valid_images = {image for product in load_surface_products()
                    if product.get('department', 'tiles') == department
                    for image in product.get('images', [])}
    config = load_tile_facet_config()
    settings = config.setdefault(config_group, {'added': [], 'removed': []})
    legacy_images = settings.get('images', {})
    card_images = settings.setdefault('card_images', dict(legacy_images))
    hero_images = settings.setdefault('hero_images', dict(legacy_images))

    def update_category_image(kind, choice, upload):
        image_map = card_images if kind == 'card' else hero_images
        if upload and upload.filename:
            folder = os.path.join(UPLOAD_FOLDER, 'surfaces', 'categories', group_slug)
            os.makedirs(folder, exist_ok=True)
            filename = f"{option_slug}-{kind}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}.webp"
            image_path = f'uploads/surfaces/categories/{group_slug}/{filename}'
            process_image(upload, os.path.join(app.static_folder, image_path))
            create_card_image(image_path)
            image_map[option_slug] = image_path
            return True
        previous = image_map.get(option_slug, legacy_images.get(option_slug, ''))
        if choice in valid_images or (previous and choice == previous):
            image_map[option_slug] = choice
            return True
        if choice == 'default':
            image_map.pop(option_slug, None)
            return True
        return False

    if not update_category_image('card', card_choice, card_upload) or not update_category_image('hero', hero_choice, hero_upload):
        flash('Choose an existing product photo, upload a new image, or use the default.', 'warning')
        return redirect(url_for('tiles_manage'))
    # New explicit maps replace the older single-image setting. Keep uploaded
    # assets in place because either image may still be referenced elsewhere.
    settings.pop('images', None)
    save_tile_facet_config(config)
    flash(f'{category.get("name", category.get("title", "Category"))} card and hero images updated.', 'success')
    return redirect(url_for('tiles_manage'))

def load_tile_series():
    """Load editable tile series while preserving the original collection tags."""
    defaults = [
        ('Alchimia', 'images/surfaces/catalog/radiant-shade-interior.jpg'),
        ('Basaltino', 'images/surfaces/catalog/products/bali-stone-black-room.jpg'),
        ('Glyphstone', 'images/surfaces/catalog/products/bali-stone-brown-room.jpg'),
        ('Sparko', 'images/surfaces/catalog/products/elite-ash-grey-room.jpg'),
        ('Venitto', 'images/surfaces/catalog/regular-fullbody-interior.jpg'),
        ('Marmorica', 'images/surfaces/catalog/products/traver-grey-white-room.jpg'),
        ('Spectra', 'images/surfaces/catalog/carving-matt-bedroom.jpg'),
        ('Ricco 2.0', 'images/surfaces/catalog/products/aspire-sand-room.jpg'),
        ('Kitchdeck', 'images/surfaces/catalog/regular-fullbody-interior.jpg'),
        ('Elite', 'images/surfaces/catalog/products/elite-ash-grey-room.jpg'),
        ('Prism', 'images/surfaces/catalog/carving-matt-bedroom.jpg'),
    ]
    try:
        with open(TILE_SERIES_FILE, 'r', encoding='utf-8') as file:
            series = json.load(file)
        if isinstance(series, list):
            return series
    except (OSError, json.JSONDecodeError):
        pass
    series = [{'slug': tile_product_slug(name), 'name': name, 'image': image, 'description': '', 'active': True}
              for name, image in defaults]
    os.makedirs(os.path.dirname(TILE_SERIES_FILE), exist_ok=True)
    with open(TILE_SERIES_FILE, 'w', encoding='utf-8') as file:
        json.dump(series, file, indent=2, ensure_ascii=False)
    return series

def load_homepage_featured_series_slugs():
    try:
        with open(TILE_HOME_FEATURED_FILE, 'r', encoding='utf-8') as file:
            value = json.load(file)
        if isinstance(value, list):
            return list(dict.fromkeys(str(slug).strip() for slug in value if str(slug).strip()))[:3]
    except (OSError, json.JSONDecodeError):
        pass
    return []

def save_homepage_featured_series_slugs(slugs):
    os.makedirs(os.path.dirname(TILE_HOME_FEATURED_FILE), exist_ok=True)
    with open(TILE_HOME_FEATURED_FILE, 'w', encoding='utf-8') as file:
        json.dump(list(slugs)[:3], file, indent=2, ensure_ascii=False)

def get_homepage_featured_series():
    """Return the three tile series featured on the public tile homepage."""
    series = [item for item in load_tile_series() if item.get('active', True)]
    products = [item for item in load_surface_products()
                if item.get('department', 'tiles') == 'tiles' and is_public_surface_product(item, 'tiles')]
    series_by_slug = {item.get('slug'): item for item in series}
    configured = [series_by_slug[slug] for slug in load_homepage_featured_series_slugs()
                  if slug in series_by_slug]
    if len(configured) < 3:
        used = {item.get('slug') for item in configured}
        with_products = [item for item in series if item.get('slug') not in used and any(
            item.get('slug') in get_product_tile_tags(product) for product in products)]
        configured.extend(with_products[:3 - len(configured)])
    if len(configured) < 3:
        used = {item.get('slug') for item in configured}
        configured.extend([item for item in series if item.get('slug') not in used][:3 - len(configured)])

    featured = []
    for record in configured[:3]:
        representative = next((get_surface_product_cover(product) for product in products
                               if record.get('slug') in get_product_tile_tags(product)
                               and get_surface_product_cover(product)), None)
        image = record.get('card_image') or record.get('cover_image') or representative or record.get('image') or 'images/surfaces/catalog/double-charge-800-room.jpg'
        featured.append({
            **record,
            'image': image,
            'alt': f"{record.get('name', 'Tile')} series tile collection",
            'description': record.get('description') or 'Explore the colours, formats and finishes in this tile series.',
            'href': url_for('tiles_category_products', group_slug='collection', category_slug=record.get('slug'), series_slug=record.get('slug')),
        })
    return featured

def clear_tile_series_cover_images(image_paths):
    removed = set(image_paths)
    if not removed:
        return
    series = load_tile_series()
    changed = False
    for record in series:
        for key in ('cover_image', 'card_image', 'hero_image'):
            if record.get(key) in removed:
                record[key] = ''
                changed = True
    if changed:
        with open(TILE_SERIES_FILE, 'w', encoding='utf-8') as file:
            json.dump(series, file, indent=2, ensure_ascii=False)

_TILE_SIZE_PATTERN = re.compile(r'(?<!\d)(\d{2,4})\s*(?:x|×|\*)\s*(\d{2,4})(?:\s*(?:x|×|\*)\s*(\d{1,2}(?:\.\d+)?))?(?:\s*mm)?', re.IGNORECASE)
_ROCKDECK_PATTERN = re.compile(r'\brockdeck\b.*?15\s*mm', re.IGNORECASE)
_tile_sizes_cache = {}
_tile_tags_cache = {}

def _tile_sizes_from_details(details):
    """Parse sizes from a details text once and remember the result (same text -> same sizes)."""
    cached = _tile_sizes_cache.get(details)
    if cached is None:
        sizes = []
        for width, height, thickness in _TILE_SIZE_PATTERN.findall(details):
            thickness_label = f' × {format(float(thickness), "g")}' if thickness else ''
            name = f'{width} × {height}{thickness_label} mm'
            if name not in sizes:
                sizes.append(name)
        if _ROCKDECK_PATTERN.search(details):
            sizes.append('Rockdeck · 15 mm')
        cached = tuple(sizes)
        if len(_tile_sizes_cache) > 20000:
            _tile_sizes_cache.clear()
        _tile_sizes_cache[details] = cached
    return cached

def get_product_tile_sizes(product):
    """Return tile dimensions found in product details in a consistent form."""
    return list(_tile_sizes_from_details(str(product.get('details', ''))))

def get_product_tile_tags(product):
    """Include dimensions from the details field for older products too."""
    key = (tuple(product.get('tags', [])), str(product.get('details', '')))
    cached = _tile_tags_cache.get(key)
    if cached is None:
        tags = set(key[0])
        tags.update(tile_product_slug(size) for size in _tile_sizes_from_details(key[1]))
        cached = frozenset(tags)
        if len(_tile_tags_cache) > 20000:
            _tile_tags_cache.clear()
        _tile_tags_cache[key] = cached
    return cached

def get_surface_product_cover(product):
    """Return the selected product cover, falling back to its first gallery photo."""
    images = product.get('images', [])
    selected = product.get('card_image')
    return selected if selected in images else (images[0] if images else '')

def card_image_path(image_path):
    """Use a generated small WebP for cards, falling back for existing images."""
    if not image_path:
        return ''
    stem, _ = os.path.splitext(image_path)
    thumbnail = f'{stem}-card.webp'
    return thumbnail if os.path.isfile(os.path.join(app.static_folder, thumbnail)) else image_path

def is_portrait_surface_image(image_path):
    """Identify portrait cover art so wide hero areas can show the whole image."""
    if not image_path:
        return False
    try:
        with Image.open(os.path.join(app.static_folder, image_path)) as image:
            return image.height / max(image.width, 1) > 1.25
    except (OSError, ValueError):
        return False

# ---------------------------------------------------------------------------
# Tile cards and tile detail helpers
# Optional product fields used when present (added for Simpolo tiles):
#   finish, body, surface, application
# Optional data file static/data/tile_packing.json, by series slug:
#   {"sizes": {"600x1200": {"thickness", "pieces", "sqft"}}, "use", "features"}
# ---------------------------------------------------------------------------
TILE_PACKING_FILE = os.path.join(app.static_folder, "data", "tile_packing.json")
_tile_packing_cache = {'mtime': None, 'data': {}}
_image_ratio_cache = {}
_SIZE_TAG_PATTERN = re.compile(r'(\d{2,4})-(\d{2,4})(?:-(\d{1,2}(?:-\d{1,2})?))?-mm')
_ROOM_NAME_PATTERN = re.compile(r'preview|room|living|bedroom|kitchen|setting|interior|ambien|lifestyle|_p\d*\.|-p\.', re.IGNORECASE)
_FACE_NAME_PATTERN = re.compile(r'[-_]f\d+\.', re.IGNORECASE)
_FINISH_WORDS = ('matt', 'gloss', 'polish', 'satin', 'carving', 'lappato', 'sugar', 'punch', 'feather', 'texture')
SQFT_PER_SQM = 10.7639


def load_tile_packing():
    try:
        mtime = os.path.getmtime(TILE_PACKING_FILE)
    except OSError:
        return {}
    if _tile_packing_cache['mtime'] != mtime:
        try:
            with open(TILE_PACKING_FILE, 'r', encoding='utf-8') as file:
                data = json.load(file)
            _tile_packing_cache.update(mtime=mtime, data=data if isinstance(data, dict) else {})
        except (OSError, json.JSONDecodeError):
            _tile_packing_cache.update(mtime=mtime, data={})
    return _tile_packing_cache['data']


def surface_image_ratio(image_path):
    """Width / height of a stored photo (read from the file header and cached)."""
    full_path = os.path.join(app.static_folder, card_image_path(image_path))
    try:
        mtime = os.path.getmtime(full_path)
    except OSError:
        return None
    cached = _image_ratio_cache.get(full_path)
    if cached and cached[0] == mtime:
        return cached[1]
    try:
        with Image.open(full_path) as image:
            ratio = image.width / max(image.height, 1)
    except (OSError, ValueError):
        ratio = None
    _image_ratio_cache[full_path] = (mtime, ratio)
    return ratio


def tile_product_size_list(product):
    """Sizes of a tile as [{'width', 'height', 'thickness', 'slug'}], read from its size tags."""
    sizes, seen = [], set()
    for tag in sorted(get_product_tile_tags(product)):
        match = _SIZE_TAG_PATTERN.fullmatch(str(tag))
        if not match or tag in seen:
            continue
        seen.add(tag)
        thickness = match.group(3).replace('-', '.') if match.group(3) else ''
        sizes.append({'width': int(match.group(1)), 'height': int(match.group(2)), 'thickness': thickness, 'slug': tag})
    sizes.sort(key=lambda item: (item['width'] * item['height'], item['thickness']))
    return sizes


def tile_image_kind(image_path, product, sizes=None):
    """'room' for a room / application photo, 'face' for a straight photo of the tile itself."""
    name = os.path.basename(str(image_path))
    if _ROOM_NAME_PATTERN.search(name):
        return 'room'
    if _FACE_NAME_PATTERN.search(name):
        return 'face'
    ratio = surface_image_ratio(image_path)
    if not ratio:
        return 'room'
    for size in sizes if sizes is not None else tile_product_size_list(product):
        for expected in (size['width'] / size['height'], size['height'] / size['width']):
            if abs(ratio - expected) / expected < 0.04:
                return 'face'
    return 'room'


def tile_product_finishes(product, look_names=None):
    stated = [part.strip().capitalize() for part in str(product.get('finish') or '').split(',') if part.strip()]
    if stated:
        return list(dict.fromkeys(stated))
    names = look_names or {}
    found = []
    for tag in get_product_tile_tags(product):
        label = names.get(tag) or tag.replace('-', ' ').title()
        if any(word in tag for word in _FINISH_WORDS) and label not in found:
            found.append(label)
    return found


def series_title(name):
    """Show a series name once with the word Series: 'Neo' -> 'Neo Series', 'Neo Series' stays."""
    name = str(name or '').strip()
    if not name:
        return ''
    return name if name.lower().endswith('series') else f'{name} Series'


app.add_template_filter(series_title, 'series_title')


def absolute_url(path):
    """Full https URL for a site path (used in structured data)."""
    path = str(path or '')
    if path.startswith(('http://', 'https://')):
        return path
    return request.url_root.rstrip('/') + '/' + path.lstrip('/')


def spec_property(pair):
    return {'@type': 'PropertyValue', 'name': pair[0], 'value': pair[1]}


app.add_template_filter(absolute_url, 'absolute_url')
app.add_template_filter(spec_property, 'spec_property')


def manager_option_set(options):
    """Register a list of image choices once per page; the manager fills the dropdown when it is opened."""
    store = g.setdefault('_option_sets', {'images': [], 'index': {}, 'sets': {}, 'keys': {}})
    signature = tuple(option.get('image', '') for option in options)
    key = store['keys'].get(signature)
    if key is None:
        indexes = []
        for option in options:
            image = option.get('image', '')
            label = f"{option.get('title', '')} · {image.split('/')[-1]}"
            position = store['index'].get((image, label))
            if position is None:
                position = len(store['images'])
                store['images'].append([image, label])
                store['index'][(image, label)] = position
            indexes.append(position)
        key = f"s{len(store['sets'])}"
        store['sets'][key] = indexes
        store['keys'][signature] = key
    return key


def manager_option_sets_json():
    store = g.get('_option_sets') or {'images': [], 'sets': {}}
    return Markup(json.dumps({'images': store['images'], 'sets': store['sets']}, ensure_ascii=False).replace('</', '<\\/'))


app.add_template_filter(manager_option_set, 'manager_option_set')
app.add_template_global(manager_option_sets_json, 'manager_option_sets_json')


def tile_series_for(product, series_by_slug):
    return next((series_by_slug[tag] for tag in sorted(get_product_tile_tags(product)) if tag in series_by_slug), None)


def tile_packing_for(series_slug, size):
    """Box details for one size of a series, allowing for 1-2 mm differences in the stated size."""
    sizes = (load_tile_packing().get(series_slug or '') or {}).get('sizes', {})
    for key, value in sizes.items():
        try:
            width, height = (int(part) for part in key.lower().split('x'))
        except ValueError:
            continue
        for a, b in ((width, height), (height, width)):
            if abs(a - size['width']) <= 3 and abs(b - size['height']) <= 3:
                return value
    return None


def tile_size_label(size, with_thickness=True):
    label = f"{size['width']} × {size['height']}"
    if with_thickness and size.get('thickness'):
        label += f" × {size['thickness']}"
    return label + ' mm'


def tile_card(product, series_by_slug, look_names=None):
    sizes = tile_product_size_list(product)
    cover = get_surface_product_cover(product)
    kind = tile_image_kind(cover, product, sizes)
    face = ''
    if kind == 'room':
        face = next((image for image in product.get('images', []) if image != cover and tile_image_kind(image, product, sizes) == 'face'), '')
    series = tile_series_for(product, series_by_slug)
    compact = list(dict.fromkeys(f"{size['width']}×{size['height']}" for size in sizes))
    return {
        'code': product.get('code'),
        'title': product.get('title', 'Tile design'),
        'brand': '' if str(product.get('brand', '')).strip() in {'', 'Other / not specified'} else product.get('brand'),
        'series': series_title(series.get('name', '')) if series else '',
        'image': cover,
        'thumbnail': card_image_path(cover),
        'kind': kind,
        'face': card_image_path(face) if face else '',
        'sizes': compact,
        'finishes': tile_product_finishes(product, look_names),
        'demo': product.get('demo', False),
    }


def card_image_disk_path(image_path):
    stem, _ = os.path.splitext(image_path)
    return f'{stem}-card.webp'

def create_card_image(image_path):
    """Create a 640px WebP card image while retaining the sharp detail image."""
    if not image_path:
        return ''
    thumbnail = card_image_disk_path(image_path)
    source_path = os.path.join(app.static_folder, image_path)
    thumbnail_path = os.path.join(app.static_folder, thumbnail)
    # Upload edits often revisit every gallery photo. Reuse existing card
    # derivatives so unchanged images are not decoded and re-encoded each time.
    if os.path.isfile(thumbnail_path):
        return thumbnail
    if os.path.isfile(source_path):
        process_image(source_path, thumbnail_path, max_width=640, quality=78)
        return thumbnail
    return image_path

@app.route('/tiles/collections')
def tiles_collections():
    brands = [item for item in load_surface_brands() if item.get('active', True) and item.get('department') in {'tiles', 'both'}]
    return render_template('tiles_collection_home.html', tile_category_groups=get_tile_category_groups(), tile_brands=brands)

@app.route('/tiles/category/<group_slug>/<category_slug>')
@app.route('/tiles/category/<group_slug>/<category_slug>/series/<series_slug>')
def tiles_category_products(group_slug, category_slug, series_slug=None):
    category_groups = get_tile_category_groups()
    group = next((group for group in category_groups if group['slug'] == group_slug), None)
    category_item = next((item for item in group['cards'] if item['slug'] == category_slug), None) if group else None
    if group_slug == 'collection' and category_slug == 'all-collections':
        category_item = {'slug': 'all-collections', 'name': 'All collections', 'image': 'images/surfaces/catalog/double-charge-800-room.jpg'}
    if not group or not category_item:
        return redirect(url_for('tiles_collections'))
    brand_slug = request.args.get('brand', '').lower()
    brand_record = next((item for item in load_surface_brands() if item.get('slug') == brand_slug and item.get('active', True)), None) if brand_slug else None
    brand_name = brand_record.get('name') if brand_record else None
    all_brand_products = group_slug == 'collection' and category_slug == 'all-collections' and bool(brand_name)
    if group_slug == 'collection' and category_slug == 'all-collections' and not all_brand_products:
        return redirect(url_for('tiles_catalogues'))
    if brand_slug and not brand_record:
        return redirect(url_for('tiles_collections'))
    series_records = [item for item in load_tile_series() if item.get('active', True)]
    series_by_slug = {item.get('slug'): item for item in series_records}
    selected_series_slug = series_slug or (category_slug if group_slug == 'collection' and category_slug != 'all-collections' else None)
    selected_series = series_by_slug.get(selected_series_slug)
    if selected_series_slug and not selected_series:
        return redirect(url_for('tiles_collections'))
    selected = {'filter_brand': [value.strip() for value in request.args.getlist('filter_brand') if value.strip()]}
    selected.update({facet_group['slug']: [value.strip() for value in request.args.getlist(facet_group['slug']) if value.strip()]
                     for facet_group in category_groups})
    if brand_name:
        selected['filter_brand'] = [brand_name]
    active_tile_brands = {str(item.get('name', '')).strip().lower() for item in load_surface_brands()
                          if item.get('active', True) and item.get('department') in {'tiles', 'both'}}
    base_products = []
    for item in load_surface_products():
        item_brand = str(item.get('brand', '')).strip()
        publicly_listed = not item.get('brand_removed') and (not item_brand or item_brand.lower() == 'other / not specified' or item_brand.lower() in active_tile_brands)
        item_tags = get_product_tile_tags(item)
        matches_category = all_brand_products or (group_slug == 'collection' and category_slug == 'all-collections') or category_slug in item_tags
        if item.get('department', 'tiles') == 'tiles' and publicly_listed and matches_category:
            base_products.append(item)
    if group_slug != 'collection' and not selected_series:
        if brand_name:
            base_products = [item for item in base_products if str(item.get('brand', '')).lower() == brand_name.lower()]
        series_filter_groups = [
            {**facet_group, 'items': [card for card in facet_group['cards'] if card['slug'] != 'all-collections']}
            for facet_group in category_groups
            if facet_group['slug'] not in {group_slug, 'collection'}
        ]
        series_available_brands = sorted({str(item.get('brand', '')).strip() for item in base_products
                                          if str(item.get('brand', '')).strip()}, key=str.lower)
        if selected['filter_brand']:
            wanted_brands = {name.lower() for name in selected['filter_brand']}
            base_products = [item for item in base_products if str(item.get('brand', '')).strip().lower() in wanted_brands]
        for facet_group in series_filter_groups:
            wanted_values = selected.get(facet_group['slug'], [])
            if wanted_values:
                base_products = [item for item in base_products
                                 if any(tag in get_product_tile_tags(item) for tag in wanted_values)]
        series_cards = []
        for record in series_records:
            member_products = [item for item in base_products if record['slug'] in get_product_tile_tags(item)]
            if not member_products:
                continue
            representative = next((get_surface_product_cover(product) for product in member_products if get_surface_product_cover(product)), None)
            image = record.get('card_image') or record.get('cover_image') or representative or record.get('image') or category_item['image']
            series_cards.append({
                **record,
                'image': card_image_path(image),
                'product_count': len(member_products),
                'url': url_for('tiles_category_products', group_slug=group_slug, category_slug=category_slug,
                               series_slug=record['slug'], brand=brand_slug or None),
            })
        return render_template('tiles_category_series.html', group=group, category=category_item['name'],
                               category_image=category_item.get('hero_image', category_item['image']), series_cards=series_cards,
                               category_image_portrait=is_portrait_surface_image(category_item.get('hero_image', category_item['image'])),
                               brand=brand_name, brand_slug=brand_slug, filter_groups=series_filter_groups,
                               available_brands=series_available_brands, selected_filters=selected)
    if selected_series:
        base_products = [item for item in base_products if selected_series_slug in get_product_tile_tags(item)]
    available_brands = sorted({str(item.get('brand', '')).strip() for item in base_products if str(item.get('brand', '')).strip()}, key=str.lower)
    products = base_products
    if selected['filter_brand']:
        selected_brand_names = {name.lower() for name in selected['filter_brand']}
        products = [item for item in products if str(item.get('brand', '')).lower() in selected_brand_names]
    for facet, value in selected.items():
        if facet != 'filter_brand' and value:
            products = [item for item in products if any(tag in get_product_tile_tags(item) for tag in value)]
    filter_groups = []
    for facet_group in category_groups:
        if facet_group['slug'] != group_slug and facet_group['slug'] != 'collection' and not all_brand_products:
            filter_groups.append({**facet_group, 'items': [card for card in facet_group['cards'] if card['slug'] != 'all-collections']})
    if brand_name:
        available_brands = [brand_name]
    for item in products:
        item['thumbnail'] = card_image_path(get_surface_product_cover(item))
    look_names = {card['slug']: card['name'] for facet_group in category_groups if facet_group['slug'] == 'look-feel' for card in facet_group['cards']}
    page_size = 24
    try:
        cards_from = max(int(request.args.get('cards_from', 0)), 0)
    except ValueError:
        cards_from = 0
    if cards_from:
        # "Show more" asks for the next page of cards only.
        page_cards = [tile_card(item, series_by_slug, look_names) for item in products[cards_from:cards_from + page_size]]
        return render_template('_tile_cards_page.html', cards=page_cards, brand=brand_name, brand_slug=brand_slug,
                               return_to=request.full_path.split('cards_from')[0].rstrip('?&'))
    cards = [tile_card(item, series_by_slug, look_names) for item in products[:page_size]]
    series_summary = None
    if selected_series:
        member_sizes, member_finishes, member_bodies = {}, [], []
        for item in base_products:
            for size in tile_product_size_list(item):
                member_sizes.setdefault(size['slug'], size)
            for finish in tile_product_finishes(item, look_names):
                if finish not in member_finishes:
                    member_finishes.append(finish)
            for body in str(item.get('body') or '').split(','):
                if body.strip() and body.strip() not in member_bodies:
                    member_bodies.append(body.strip())
        ordered_sizes = sorted(member_sizes.values(), key=lambda size: (size['width'] * size['height'], size['thickness']))
        packing = load_tile_packing().get(selected_series_slug) or {}
        series_summary = {
            'count': len(base_products),
            'sizes': [{'label': tile_size_label(size), 'slug': size['slug']} for size in ordered_sizes],
            'finishes': member_finishes, 'bodies': member_bodies,
            'use': packing.get('use', ''), 'features': packing.get('features', []),
        }
    category = (f'{brand_name} · All tile collections' if all_brand_products else
                f'{selected_series["name"]} · {category_item["name"]}' if selected_series and group_slug != 'collection' else
                series_title(selected_series["name"]) if selected_series else category_item['name'])
    series_image = next((image for item in products for image in item.get('images', []) if image), None)
    category_image = (selected_series.get('hero_image') or category_item.get('hero_image', category_item['image'])) if selected_series else category_item.get('hero_image', category_item['image'])
    return render_template('tiles_category_products.html', group=group, category=category, category_image=category_image, category_image_portrait=is_portrait_surface_image(category_image), products=products, brand=brand_name, brand_slug=brand_slug, filter_groups=filter_groups, available_brands=available_brands, selected_filters=selected, selected_series=selected_series, selected_series_slug=selected_series_slug, cards=cards, card_total=len(products), series_summary=series_summary)

@app.route('/tiles/collections/brand/<slug>')
def tiles_collection_brand(slug):
    brand_record = next((item for item in load_surface_brands() if item.get('slug') == slug.lower() and item.get('active', True) and item.get('department') in {'tiles', 'both'}), None)
    if brand_record:
        return render_template('tiles_collection_home.html', tile_category_groups=get_tile_category_groups(), tile_brands=[brand_record], brand=brand_record['name'], brand_slug=brand_record['slug'])
    return redirect(url_for('tiles_collections'))

@app.route('/tiles/search')
def tiles_search():
    query = ' '.join(request.args.get('q', '').split())[:80]
    words = [word for word in re.split(r'[^a-z0-9.]+', query.lower()) if word]
    tile_cards, bath_cards = [], []
    tile_total = bath_total = 0
    if words:
        series_by_slug = {record.get('slug'): record for record in load_tile_series() if record.get('active', True)}
        tile_hits, bath_hits = [], []
        for product in load_surface_products():
            if not product.get('images'):
                continue
            department = product.get('department', 'tiles')
            tags = ' '.join(sorted(get_product_tile_tags(product))) if department == 'tiles' else ''
            series = tile_series_for(product, series_by_slug) if department == 'tiles' else None
            haystack = ' '.join(str(value) for value in (
                product.get('title', ''), product.get('brand', ''), product.get('collection', ''), product.get('type', ''),
                product.get('category', ''), product.get('sku', ''), product.get('finish', ''), tags.replace('-', ' '),
                series.get('name', '') if series else '')).lower()
            if not all(word in haystack for word in words):
                continue
            title = str(product.get('title', '')).lower()
            score = (0 if title.startswith(words[0]) else 1, 0 if all(word in title for word in words) else 1)
            if department == 'tiles' and is_public_surface_product(product, 'tiles'):
                tile_hits.append((score, product))
            elif department == 'bathware':
                bath_hits.append((score, product))
        public_bath = {item.get('code') for item in get_public_bath_products()}
        bath_hits = [hit for hit in bath_hits if hit[1].get('code') in public_bath]
        tile_hits.sort(key=lambda hit: hit[0]); bath_hits.sort(key=lambda hit: hit[0])
        tile_total, bath_total = len(tile_hits), len(bath_hits)
        tile_cards = [tile_card(product, series_by_slug) for _, product in tile_hits[:48]]
        bath_cards = [bath_product_card(product) for _, product in bath_hits[:24]]
    return render_template('tiles_search.html', query=query, tile_cards=tile_cards, bath_cards=bath_cards,
                           tile_total=tile_total, bath_total=bath_total)


@app.route('/tiles/wishlist')
def tiles_wishlist():
    return render_template('tiles_wishlist.html')

@app.route('/wishlist')
def furniture_wishlist():
    return render_template('furniture_wishlist.html')

def get_series_brand_groups(surface_products=None):
    """Tile series grouped by brand, plus designs that belong to no series."""
    if surface_products is None:
        surface_products = [item for item in load_surface_products() if item.get('department', 'tiles') == 'tiles' and is_public_surface_product(item, 'tiles')]
    series_records = [record for record in load_tile_series() if record.get('active', True)]
    series_by_slug = {record.get('slug'): record for record in series_records}
    members, loose = {}, []
    for item in surface_products:
        if not item.get('images'):
            continue
        record = tile_series_for(item, series_by_slug)
        if record:
            members.setdefault(record['slug'], []).append(item)
        else:
            loose.append(item)
    series_brand_groups = []
    for record in series_records:
        items = members.get(record['slug'])
        if not items:
            continue
        brands = [str(item.get('brand', '')).strip() for item in items]
        brand_name = max(set(brands), key=brands.count) if brands else ''
        if brand_name in {'', 'Other / not specified'}:
            brand_name = 'Uniglobe'
        image = record.get('card_image') or record.get('cover_image') or get_surface_product_cover(items[0])
        group = next((entry for entry in series_brand_groups if entry['brand'] == brand_name), None)
        if group is None:
            group = {'brand': brand_name, 'series': [], 'count': 0}
            series_brand_groups.append(group)
        group['series'].append({'name': record.get('name', ''), 'slug': record['slug'], 'count': len(items), 'image': card_image_path(image),
                                'url': url_for('tiles_category_products', group_slug='collection', category_slug=record['slug'], series_slug=record['slug'])})
        group['count'] += len(items)
    series_brand_groups.sort(key=lambda group: (group['brand'] == 'Uniglobe', -group['count']))
    return series_brand_groups, loose, series_by_slug


@app.route('/tiles/catalogues')
def tiles_catalogues():
    catalog_groups = []
    for item in tile_lookbook_products:
        catalog = item.get('catalog') or {
            'Digital Full Body': 'Digital Fullbody Catalogue 01',
            'Regular Full Body': 'Regular Fullbody Collection · 2026',
            '5 mm · Punch Matt': 'Punch Matt Catalogue',
            '5 mm · Carving Matt': 'Carving Matt Catalogue',
            'Radiant Shade Matt': 'Radiant Shade Matt Catalogue',
            'MTO Catalogue Designs': 'MTO Catalogue · design index',
        }.get(item['group'], item['group'])
        section = next((group for group in catalog_groups if group['name'] == catalog), None)
        if section is None:
            section = {'name': catalog, 'items': []}
            catalog_groups.append(section)
        # Keep the card URL slug in sync with the product detail route. Doing
        # this here also avoids duplicating slug-cleanup logic in the template.
        catalog_item = dict(item)
        catalog_item['slug'] = tile_product_slug(item['name'])
        section['items'].append(catalog_item)
    surface_products = [item for item in load_surface_products() if item.get('department', 'tiles') == 'tiles' and is_public_surface_product(item, 'tiles')]
    for item in surface_products:
        item['thumbnail'] = card_image_path(item.get('images', [''])[0] if item.get('images') else '')
    series_brand_groups, loose, series_by_slug = get_series_brand_groups(surface_products)
    loose_cards = [tile_card(item, series_by_slug) for item in loose]
    return render_template('tiles_collections.html', surface_collections=surface_collections, surface_products=surface_products, tile_catalog_groups=catalog_groups, brand=None,
                           series_brand_groups=series_brand_groups, loose_cards=loose_cards)

def tile_product_slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

@app.route('/tiles/product/<slug>')
def tiles_product_detail(slug):
    product = next((item for item in tile_lookbook_products if tile_product_slug(item['name']) == slug), None)
    if product is None:
        return redirect(url_for('tiles_catalogues'))

    gallery = [{'src': product['image'], 'label': 'Tile surface'}]
    slug_to_page = {
        'olimpia-beige': 6, 'olimpia-black': 8, 'olimpia-cookie': 10,
        'olimpia-grey-white': 12, 'regal-black': 14, 'regal-xl-white': 16,
        'smoky-cool-beige': 18, 'smoky-cool-black': 20, 'smoky-cool-brown': 22,
        'traver-beige': 24, 'traver-grey-white': 26,
        'bali-stone-black': 28, 'bali-stone-brown': 30, 'bruno-black': 32,
        'calcutta-gold-quartz': 34, 'zebrano-black': 36, 'imperia-quartz': 38,
        'muretto-beige': 40, 'oxan-beige': 42, 'oxan-quartz': 44,
        'turkish-grey-white': 46,
    }
    digital_page = slug_to_page.get(slug)
    if digital_page:
        base = f'images/surfaces/catalog/products/{slug}'
        gallery = [
            {'src': base + '-600x1200.jpg', 'label': '600 × 1200 mm'},
            {'src': base + '-600x1000.jpg', 'label': '600 × 1000 mm'},
            {'src': base + '-600x900.jpg', 'label': '600 × 900 mm'},
            {'src': base + '-room.jpg', 'label': 'Installed collection view'},
        ]
    else:
        base = f'images/surfaces/catalog/products/{slug}'
        if os.path.exists(os.path.join(app.static_folder, base + '-sample-2.jpg')):
            gallery.append({'src': base + '-sample-2.jpg', 'label': 'Another format view'})
        if os.path.exists(os.path.join(app.static_folder, base + '-sample-3.jpg')):
            gallery.append({'src': base + '-sample-3.jpg', 'label': 'Additional format view'})
        if os.path.exists(os.path.join(app.static_folder, base + '-sample-4.jpg')):
            gallery.append({'src': base + '-sample-4.jpg', 'label': 'Surface variation'})
        if os.path.exists(os.path.join(app.static_folder, base + '-room.jpg')):
            gallery.append({'src': base + '-room.jpg', 'label': 'Installed collection view'})
        inspiration = {
            'Regular Full Body': 'images/surfaces/catalog/regular-fullbody-interior.jpg',
            '5 mm · Punch Matt': 'images/surfaces/catalog/punch-matt-exterior.jpg',
            '5 mm · Carving Matt': 'images/surfaces/catalog/carving-matt-bedroom.jpg',
            'MTO Catalogue Designs': 'images/surfaces/catalog/punch-matt-exterior.jpg',
        }.get(product['group'])
        if inspiration and (len(gallery) == 1 or product['group'].startswith('5 mm')):
            gallery.append({'src': inspiration, 'label': 'Collection inspiration'})
    product['wishlist_id'] = slug
    views = []
    for view in gallery:
        is_room = 'room' in view['src'] or view['label'] in {'Installed collection view', 'Collection inspiration'}
        views.append({'src': url_for('static', filename=view['src']), 'thumb': url_for('static', filename=card_image_path(view['src'])),
                      'kind': 'room' if is_room else 'face'})
    room_views = [view for view in views if view['kind'] == 'room']
    face_views = [view for view in views if view['kind'] == 'face']
    specs = [('Collection', product.get('group', ''))] + ([('Formats', product['details'])] if product.get('details') else [])
    return render_template('tiles_product_detail.html', product=product, gallery=gallery,
                           wishlist_image=url_for('static', filename=gallery[0]['src']),
                           wishlist_url=request.full_path.rstrip('?'),
                           views=room_views + face_views, has_room_and_face=bool(room_views and face_views),
                           size_options=[], specs=specs, features=[], brand_name='', finishes=[],
                           related_cards=[], related_label='', related_url=None, related_total=0, series_slug=None)

@app.route('/tiles/product-uploaded/<code>')
def tiles_uploaded_product_detail(code):
    item = next((product for product in load_surface_products() if product.get('code') == code), None)
    if item is None or item.get('department', 'tiles') != 'tiles' or not is_public_surface_product(item, 'tiles') or not item.get('images'):
        return redirect(url_for('tiles_collections'))
    assigned_tags = get_product_tile_tags(item)
    series_record = next((series for series in load_tile_series()
                          if series.get('slug') in assigned_tags), None)
    selected_specs = {'size': [], 'look-feel': [], 'color': []}
    category_groups = get_tile_category_groups()
    if item.get('department', 'tiles') == 'tiles':
        for group in category_groups:
            if group['slug'] not in selected_specs:
                continue
            selected_specs[group['slug']] = [card['name'] for card in group['cards']
                                             if card['slug'] in assigned_tags]
    spec_labels = {'size': 'Size', 'look-feel': 'Finish', 'color': 'Colour'}
    details = ' · '.join(
        f"{spec_labels[slug]}: {', '.join(values)}"
        for slug, values in selected_specs.items() if values
    ) or item.get('details') or 'Please enquire for available sizes and finishes.'
    product = {
        'name': item.get('title', 'Tile design'),
        'group': item.get('category') or 'Tile design',
        'series_name': series_title(series_record.get('name', '')) if series_record else '',
        'description': item.get('description', ''),
        'details': details,
    }
    product_images = item.get('images', [])
    cover_image = get_surface_product_cover(item)
    if cover_image:
        product_images = [cover_image] + [image for image in product_images if image != cover_image]
    gallery = [{'src': image, 'thumbnail': card_image_path(image), 'label': 'Selected cover' if index == 0 else f'Product view {index + 1}'} for index, image in enumerate(product_images)]
    requested_brand = request.args.get('brand', '').lower()
    brand_record = next((brand for brand in load_surface_brands() if brand.get('slug') == requested_brand and brand.get('active', True)), None)
    brand_slug = requested_brand if brand_record and str(item.get('brand', '')).lower() == brand_record.get('name', '').lower() else None
    return_to = request.args.get('return_to', '')
    if not return_to.startswith('/tiles/category/') or return_to.startswith('//') or '\r' in return_to or '\n' in return_to:
        return_to = None
    product['wishlist_id'] = code
    # Richer details for the product page: views, sizes with box details, specs and related designs.
    names_by_group = {group['slug']: {card['slug']: card['name'] for card in group['cards']} for group in category_groups}
    sizes = tile_product_size_list(item)
    series_slug = series_record.get('slug') if series_record else None
    views = []
    for image in product_images:
        views.append({'src': url_for('static', filename=image), 'thumb': url_for('static', filename=card_image_path(image)),
                      'kind': tile_image_kind(image, item, sizes)})
    room_views = [view for view in views if view['kind'] == 'room']
    face_views = [view for view in views if view['kind'] == 'face']
    views = room_views + face_views if room_views and views and views[0]['kind'] == 'room' else views
    size_options = []
    for size in sizes:
        packing = tile_packing_for(series_slug, size)
        tile_sqft = size['width'] * size['height'] / 1_000_000 * SQFT_PER_SQM
        option = {'label': tile_size_label(size), 'short': f"{size['width']} × {size['height']} mm",
                  'thickness': f"{size['thickness']} mm" if size['thickness'] else (packing or {}).get('thickness', ''),
                  'tile_sqft': round(tile_sqft, 3), 'pieces': None, 'box_sqft': None, 'box_sqm': None}
        if packing and packing.get('pieces'):
            option['pieces'] = int(packing['pieces'])
            option['box_sqft'] = round(option['pieces'] * tile_sqft, 2)
            option['box_sqm'] = round(option['box_sqft'] / SQFT_PER_SQM, 2)
        size_options.append(option)
    tags = assigned_tags
    rooms = [names_by_group.get('location', {}).get(tag) for tag in tags if tag in names_by_group.get('location', {})]
    colours = [names_by_group.get('color', {}).get(tag) for tag in tags if tag in names_by_group.get('color', {})]
    looks = [name for tag, name in names_by_group.get('look-feel', {}).items() if tag in tags]
    finishes = tile_product_finishes(item, names_by_group.get('look-feel', {}))
    series_packing = load_tile_packing().get(series_slug or '') or {}
    brand_name = '' if str(item.get('brand', '')).strip() in {'', 'Other / not specified'} else item.get('brand')
    specs = []
    if brand_name:
        specs.append(('Brand', brand_name))
    if product['series_name']:
        specs.append(('Series', product['series_name']))
    if finishes:
        specs.append(('Finish', ' · '.join(finishes)))
    if item.get('surface'):
        specs.append(('Surface', item['surface']))
    if item.get('body'):
        specs.append(('Body', item['body']))
    other_looks = [name for name in looks if not any(name.lower() in finish.lower() for finish in finishes)]
    if other_looks:
        specs.append(('Look', ' · '.join(other_looks)))
    if colours:
        specs.append(('Colour', ' · '.join(sorted(colours))))
    if item.get('application'):
        specs.append(('Application', ' and '.join(part.strip().lower() for part in item['application'].split(',') if part.strip()).capitalize()))
    if series_packing.get('use'):
        specs.append(('Use', series_packing['use']))
    if rooms:
        specs.append(('Suitable for', ', '.join(name.replace(' tiles', '') for name in rooms)))
    related_cards, related_label = [], ''
    series_by_slug = {record.get('slug'): record for record in load_tile_series() if record.get('active', True)}
    public_tiles = [other for other in load_surface_products()
                    if other.get('department', 'tiles') == 'tiles' and other.get('code') != code
                    and other.get('images') and is_public_surface_product(other, 'tiles')]
    if series_slug:
        related = [other for other in public_tiles if series_slug in get_product_tile_tags(other)]
        related_label = f"More from the {product['series_name']}"
    else:
        related = []
    if not related and colours:
        colour_tags = {tag for tag in tags if tag in names_by_group.get('color', {})}
        related = [other for other in public_tiles if colour_tags & get_product_tile_tags(other)]
        related_label = 'Similar colours'
    related_cards = [tile_card(other, series_by_slug, names_by_group.get('look-feel', {})) for other in related[:8]]
    related_url = (url_for('tiles_category_products', group_slug='collection', category_slug=series_slug, series_slug=series_slug)
                   if series_slug and len(related) > 8 else None)
    return render_template('tiles_product_detail.html', product=product, gallery=gallery,
                           demo=item.get('demo', False), brand_slug=brand_slug, return_to=return_to,
                           wishlist_image=url_for('static', filename=gallery[0]['src']),
                           wishlist_url=request.full_path.rstrip('?'),
                           views=views, has_room_and_face=bool(room_views and face_views),
                           size_options=size_options, specs=specs, features=series_packing.get('features', []),
                           brand_name=brand_name, finishes=finishes, related_cards=related_cards,
                           related_label=related_label, related_url=related_url, related_total=len(related),
                           series_slug=series_slug)

# ---------------------------------------------------------------------------
# Search engines: robots.txt and an always up-to-date sitemap.xml
# ---------------------------------------------------------------------------
@app.route('/robots.txt')
def robots_txt():
    lines = [
        'User-agent: *',
        'Disallow: /tiles/manage',
        'Disallow: /tiles/search',
        'Disallow: /tiles/wishlist',
        'Disallow: /wishlist',
        'Disallow: /admin-login',
        'Disallow: /admin-logout',
        'Disallow: /upload',
        'Disallow: /*?cards_from=',
        '',
        f"Sitemap: {url_for('sitemap_xml', _external=True)}",
    ]
    return app.response_class('\n'.join(lines) + '\n', mimetype='text/plain')


@app.route('/sitemap.xml')
def sitemap_xml():
    from xml.sax.saxutils import escape
    urls = []

    def add(endpoint, priority='0.6', **values):
        try:
            urls.append((url_for(endpoint, _external=True, **values), priority))
        except Exception:
            pass

    # Furniture
    for endpoint, priority in (('home', '1.0'), ('about', '0.7'), ('products', '0.9'), ('services', '0.8'),
                               ('projects', '0.6'), ('showroom', '0.7'), ('catalogs', '0.6'), ('blog', '0.5'), ('contact', '0.7')):
        add(endpoint, priority)
    blog_folder = os.path.join(app.template_folder, 'blog')
    if os.path.isdir(blog_folder):
        for name in sorted(os.listdir(blog_folder)):
            if name.endswith('.html'):
                add('blog_post', '0.5', slug=name[:-5])
    try:
        with open(DATA_FILE, 'r') as file:
            furniture = json.load(file)
        for category, section in furniture.items():
            if category in categories:
                for item in section.get('items', []):
                    if item.get('code'):
                        add('product_detail', '0.6', category=category, code=item['code'])
    except (OSError, ValueError, NameError):
        pass
    # Tiles and bathware
    for endpoint, priority in (('tiles_home', '1.0'), ('tiles_collections', '0.9'), ('tiles_catalogues', '0.8'),
                               ('tiles_bath', '0.9'), ('tiles_about', '0.7'), ('tiles_contact', '0.8')):
        add(endpoint, priority)
    for brand in load_surface_brands():
        if brand.get('active', True):
            if brand.get('department') in {'tiles', 'both'}:
                add('tiles_collection_brand', '0.8', slug=brand['slug'])
            if brand.get('department') in {'bathware', 'both'}:
                add('tiles_bath_brand', '0.8', brand_slug=brand['slug'])
    for group in get_tile_category_groups():
        for card in group['cards']:
            if group['slug'] == 'collection':
                add('tiles_category_products', '0.8', group_slug='collection', category_slug=card['slug'], series_slug=card['slug'])
            else:
                add('tiles_category_products', '0.7', group_slug=group['slug'], category_slug=card['slug'])
    for product in load_surface_products():
        if product.get('department', 'tiles') == 'tiles' and product.get('images') and is_public_surface_product(product, 'tiles'):
            add('tiles_uploaded_product_detail', '0.6', code=product['code'])
    for category in get_all_bath_categories():
        add('tiles_bath_category', '0.7', slug=category['slug'])
    for product in get_public_bath_products():
        add('tiles_bath_product', '0.5', code=product['code'])
    for item in tile_lookbook_products:
        add('tiles_product_detail', '0.5', slug=tile_product_slug(item['name']))
    seen, body = set(), []
    for loc, priority in urls:
        if loc in seen:
            continue
        seen.add(loc)
        body.append(f'  <url><loc>{escape(loc)}</loc><priority>{priority}</priority></url>')
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(body) + '\n</urlset>\n'
    return app.response_class(xml, mimetype='application/xml')


@app.route('/tiles/about')
def tiles_about():
    tiles = [item for item in load_surface_products()
             if item.get('department', 'tiles') == 'tiles' and item.get('images') and is_public_surface_product(item, 'tiles')]
    bath = get_public_bath_products()
    series_groups, _, _ = get_series_brand_groups(tiles)
    series_total = sum(len(group['series']) for group in series_groups)
    # Brands in the showroom, with what we carry from each
    brands = []
    for record in load_surface_brands():
        if not record.get('active', True):
            continue
        name = record.get('name', '')
        tile_count = sum(1 for item in tiles if str(item.get('brand', '')).lower() == name.lower())
        bath_count = sum(1 for item in bath if str(item.get('brand', '')).lower() == name.lower())
        if not (tile_count or bath_count or record.get('department') in {'bathware', 'both'}):
            continue
        view = bath_brand_view(record) if not tile_count else record
        image = view.get('image') or record.get('image', '')
        if tile_count:
            url = url_for('tiles_collection_brand', slug=record['slug'])
        else:
            url = url_for('tiles_bath_brand', brand_slug=record['slug'])
        brands.append({'name': name, 'image': card_image_path(image), 'tiles': tile_count, 'bath': bath_count, 'url': url})
    brands.sort(key=lambda brand: -(brand['tiles'] + brand['bath']))
    # A few room photos from the series covers for the gallery
    gallery = []
    for group in series_groups:
        for series in sorted(group['series'], key=lambda item: -item['count']):
            if (series.get('image') and len(gallery) < 6 and os.path.isfile(os.path.join(app.static_folder, series['image']))
                    and not is_portrait_surface_image(series['image'])):
                gallery.append(series)
    return render_template('tiles_about.html', tile_count=len(tiles), bath_count=len(bath), series_total=series_total,
                           brands=brands, gallery=gallery)

def _request_memo(key, path, loader):
    """Read a data file once per page view (GET requests only); saves always read fresh."""
    if not has_request_context() or request.method != 'GET':
        return loader()
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return loader()
    memo = g.setdefault('_data_memo', {})
    hit = memo.get(key)
    if hit is not None and hit[0] == mtime:
        return hit[1]
    value = loader()
    memo[key] = (mtime, value)
    return value

def load_surface_products():
    return _request_memo('surface_products', SURFACE_DATA_FILE, _read_surface_products)

def _read_surface_products():
    if not os.path.exists(SURFACE_DATA_FILE):
        return []
    try:
        with open(SURFACE_DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return []

def is_public_surface_product(product, department):
    if product.get('brand_removed'):
        return False
    brand_name = str(product.get('brand', '')).strip()
    if not brand_name or brand_name == 'Other / not specified':
        return True
    brand = next((item for item in load_surface_brands() if item.get('name', '').lower() == brand_name.lower()), None)
    return bool(brand and brand.get('active', True) and brand.get('department') in {department, 'both'})

def load_surface_brands():
    return _request_memo('surface_brands', SURFACE_BRANDS_FILE, _read_surface_brands)

def _read_surface_brands():
    defaults = [
        {'slug': 'simpolo', 'name': 'Simpolo', 'department': 'tiles', 'description': 'Explore tiles by location, look and feel, colour, or collection.', 'image': 'images/surfaces/catalog/double-charge-800-room.jpg'},
        {'slug': 'jaquar', 'name': 'Jaquar', 'department': 'bathware', 'description': 'Bath fittings, showers and sanitaryware for considered bathroom spaces.', 'image': 'images/sanitaryware/brands/jaquar-bath-inspiration.jpg'},
        {'slug': 'kohler', 'name': 'KOHLER', 'department': 'bathware', 'description': 'Distinctive bath, basin and sanitaryware options for your project.', 'image': 'images/sanitaryware/brands/kohler-bath-inspiration.jpg'},
    ]
    try:
        with open(SURFACE_BRANDS_FILE, 'r', encoding='utf-8') as file:
            brands = json.load(file)
        return brands if isinstance(brands, list) else defaults
    except (OSError, json.JSONDecodeError):
        os.makedirs(os.path.dirname(SURFACE_BRANDS_FILE), exist_ok=True)
        with open(SURFACE_BRANDS_FILE, 'w', encoding='utf-8') as file:
            json.dump(defaults, file, indent=2, ensure_ascii=False)
        return defaults
@app.route('/tiles/manage', methods=['GET', 'POST'])
def tiles_manage():
    if not session.get("admin_logged"):
        flash("Please log in to manage Surfaces products.", "warning")
        return redirect(url_for("admin_login", next="tiles_manage"))

    products = load_surface_products()
    all_brands = load_surface_brands()
    brands = [item for item in all_brands if item.get('active', True)]
    all_series = load_tile_series()
    homepage_featured_slugs = [item.get('slug') for item in get_homepage_featured_series()]
    edit_brand = next((item for item in all_brands if item.get('slug') == request.args.get('edit_brand')), None)
    edit_series = next((item for item in all_series if item.get('slug') == request.args.get('edit_series')), None)
    series_image_options = []
    tile_category_groups = get_tile_category_groups()
    category_cover_cards = {
        card['slug']: card
        for group in tile_category_groups if group['slug'] in {'location', 'look-feel', 'color'}
        for card in group['cards']
    }
    cover_options_by_category = {slug: [] for slug in category_cover_cards}
    seen_images_by_category = {slug: set() for slug in category_cover_cards}
    for product in products:
        if product.get('department', 'tiles') != 'tiles':
            continue
        image = get_surface_product_cover(product)
        if not image:
            continue
        for slug in get_product_tile_tags(product).intersection(category_cover_cards):
            if image not in seen_images_by_category[slug]:
                seen_images_by_category[slug].add(image)
                cover_options_by_category[slug].append({'image': image, 'title': product.get('title', 'Tile design')})
    for slug, card in category_cover_cards.items():
        card['cover_options'] = cover_options_by_category[slug]
    bath_categories = get_bath_categories()
    bath_cover_options = []
    seen_bath_covers = set()
    for product in products:
        if product.get('department', 'tiles') != 'bathware':
            continue
        image = get_surface_product_cover(product)
        if image and image not in seen_bath_covers:
            seen_bath_covers.add(image)
            bath_cover_options.append({'image': image, 'title': product.get('title', 'Bathware product')})
    for category in bath_categories:
        category['cover_options'] = bath_cover_options
    if edit_series:
        for product in products:
            if product.get('department', 'tiles') != 'tiles' or edit_series['slug'] not in get_product_tile_tags(product):
                continue
            for image in product.get('images', []):
                series_image_options.append({'image': image, 'title': product.get('title', 'Tile design')})
    edit_code = request.args.get("edit")
    edit_product = next((item for item in products if item.get("code") == edit_code), None)

    if request.method == "POST":
        code = request.form.get("code", "").strip()
        product = next((item for item in products if item.get("code") == code), None) if code else None
        department = request.form.get('department', 'tiles').strip().lower()
        if department not in {'tiles', 'bathware'}:
            department = 'tiles'
        brand = request.form.get("brand", "Other / not specified").strip()
        available_brands = {item['name'] for item in brands if item.get('department') in {department, 'both'}}
        if brand not in available_brands:
            brand = 'Other / not specified'
        category = request.form.get("category", "").strip() or ("Tile design" if department == 'tiles' else "Bathware")
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        details = request.form.get("details", product.get("details", "") if product else "").strip()
        tags = list(dict.fromkeys(request.form.getlist("tags") + request.form.getlist("series")))
        allowed_tags = {
            tile['slug']
            for group in get_tile_category_groups()
            for tile in group['cards']
            if not (group['slug'] == 'collection' and tile['slug'] == 'all-collections')
        }
        tags = [tag for tag in tags if tag in allowed_tags or re.fullmatch(r'\d{2,4}-\d{2,4}(?:-\d{1,2}(?:-\d{1,2})?)?-mm', tag)] if department == 'tiles' else []
        series_slugs = {item.get('slug') for item in load_tile_series() if item.get('active', True)}
        tile_category_slugs = {card['slug'] for group in get_tile_category_groups() if group['slug'] != 'collection' for card in group['cards']}
        has_series = any(tag in series_slugs for tag in tags)
        has_tile_category = any(tag in tile_category_slugs for tag in tags)
        if department == 'tiles' and (not has_series or not has_tile_category):
            flash("Choose a tile series and at least one category for this design. A series appears only in categories assigned to its products.", "danger")
            return redirect(url_for("tiles_manage", edit=code or None))
        if not title:
            flash("Please enter a product name.", "danger")
            return redirect(url_for("tiles_manage", edit=code or None))

        if not product:
            next_number = max([int(item.get("code", "S00000")[1:]) for item in products if item.get("code", "").startswith("S") and item.get("code", "")[1:].isdigit()] or [0]) + 1
            code = f"S{next_number:05d}"
            product = {"code": code, "images": []}
            products.append(product)

        folder = os.path.join(UPLOAD_FOLDER, "surfaces", code)
        os.makedirs(folder, exist_ok=True)
        files = request.files.getlist("images")
        if not request.form.get("code") and not any(uploaded and uploaded.filename for uploaded in files):
            products = [item for item in products if item is not product]
            flash("Please choose at least one product photo.", "danger")
            return redirect(url_for("tiles_manage"))
        if request.form.get("replace_images") == "yes":
            if not any(uploaded and uploaded.filename for uploaded in files):
                flash("Choose replacement photos before removing the current images.", "danger")
                return redirect(url_for("tiles_manage", edit=code))
            removed_images = []
            for old_image in product.get("images", []):
                if not old_image.startswith(f"uploads/surfaces/{code}/"):
                    continue
                removed_images.append(old_image)
                old_path = os.path.join(app.static_folder, old_image)
                if os.path.isfile(old_path):
                    os.remove(old_path)
                old_thumbnail = os.path.join(app.static_folder, card_image_disk_path(old_image))
                if os.path.isfile(old_thumbnail):
                    os.remove(old_thumbnail)
            clear_tile_series_cover_images(removed_images)
            product["images"] = []
        uploaded_image_paths = {}
        for uploaded in files:
            if uploaded and uploaded.filename:
                original_stem = os.path.splitext(secure_filename(uploaded.filename))[0] or 'tile-photo'
                filename = original_stem + ".webp"
                suffix = 2
                image_path = f"uploads/surfaces/{code}/{filename}"
                while os.path.exists(os.path.join(folder, filename)) or image_path in product.get("images", []):
                    filename = f"{original_stem}-{suffix}.webp"
                    suffix += 1
                    image_path = f"uploads/surfaces/{code}/{filename}"
                process_image(uploaded, os.path.join(folder, filename))
                if image_path not in product["images"]:
                    product["images"].append(image_path)
                uploaded_image_paths[uploaded.filename] = image_path
                uploaded_image_paths[filename] = image_path
        chosen_cover = request.form.get('primary_image_choice', '').strip()
        if chosen_cover in product.get('images', []):
            product['card_image'] = chosen_cover
        elif chosen_cover in uploaded_image_paths:
            product['card_image'] = uploaded_image_paths[chosen_cover]
        elif product.get('card_image') not in product.get('images', []):
            product['card_image'] = product.get('images', [''])[0]
        for image_path in product.get('images', []):
            if image_path.startswith(f'uploads/surfaces/{code}/'):
                create_card_image(image_path)
        product.pop('stock', None)
        product.update({"department": department, "brand": brand, "brand_removed": False, "category": category, "title": title, "description": description, "details": details, "tags": tags, "card_image": product.get('card_image', ''), "demo": request.form.get("demo") == "yes"})
        os.makedirs(os.path.dirname(SURFACE_DATA_FILE), exist_ok=True)
        with open(SURFACE_DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(products, file, indent=2, ensure_ascii=False)
        flash(f"{title} saved. Product code: {code}", "success")
        return redirect(url_for("tiles_manage"))

    if edit_product and edit_product.get('department', 'tiles') == 'tiles':
        edit_product = {**edit_product, 'tags': list(get_product_tile_tags(edit_product))}
    return render_template("tiles_manage.html", products=products, edit_product=edit_product, tile_category_groups=tile_category_groups, bath_categories=bath_categories, brands=brands, all_brands=all_brands, edit_brand=edit_brand, all_series=all_series, edit_series=edit_series, series_image_options=series_image_options, homepage_featured_slugs=homepage_featured_slugs)

@app.route('/tiles/manage/homepage', methods=['POST'])
def tiles_manage_homepage_featured():
    if not session.get('admin_logged'):
        return redirect(url_for('admin_login', next='tiles_manage'))
    selected = [slug.strip() for slug in request.form.getlist('featured_series') if slug.strip()]
    active_slugs = {item.get('slug') for item in load_tile_series() if item.get('active', True)}
    if len(selected) != 3 or len(set(selected)) != 3 or any(slug not in active_slugs for slug in selected):
        flash('Choose three different active tile series for the homepage.', 'danger')
        return redirect(url_for('tiles_manage'))
    save_homepage_featured_series_slugs(selected)
    flash('Featured tile series updated on the homepage.', 'success')
    return redirect(url_for('tiles_manage'))

@app.route('/tiles/manage/series', methods=['POST'])
def tiles_manage_series():
    if not session.get('admin_logged'):
        return redirect(url_for('admin_login', next='tiles_manage'))
    series = load_tile_series()
    products = load_surface_products()
    old_slug = request.form.get('slug', '').strip()
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    card_choice = request.form.get('card_image_choice', '').strip()
    hero_choice = request.form.get('hero_image_choice', '').strip()
    card_file = request.files.get('card_image')
    hero_file = request.files.get('hero_image')
    slug = tile_product_slug(name)
    if not name or not slug:
        flash('Enter a series name.', 'danger')
        return redirect(url_for('tiles_manage'))
    category_slugs = {card['slug'] for group in get_tile_category_groups() if group['slug'] != 'collection' for card in group['cards']}
    if slug == 'all-collections' or slug in category_slugs:
        flash('Choose a series name that does not match a tile category.', 'danger')
        return redirect(url_for('tiles_manage', edit_series=old_slug or None))
    if any(item.get('slug') == slug and item.get('slug') != old_slug for item in series):
        flash('That tile series already exists.', 'danger')
        return redirect(url_for('tiles_manage', edit_series=old_slug or None))
    record = next((item for item in series if item.get('slug') == old_slug), None) if old_slug else None
    valid_cover_images = {image for product in products
                          if product.get('department', 'tiles') == 'tiles' and old_slug in get_product_tile_tags(product)
                          for image in product.get('images', [])}
    previous_images = {key: record.get(key, '') for key in ('card_image', 'hero_image', 'cover_image')} if record else {}
    if record:
        previous_slug = record.get('slug')
        record.update({'slug': slug, 'name': name, 'description': description, 'active': True})
        if previous_slug != slug:
            for product in products:
                if product.get('department', 'tiles') == 'tiles' and previous_slug in product.get('tags', []):
                    product['tags'] = [slug if tag == previous_slug else tag for tag in product.get('tags', [])]
        message = f'{name} series updated.'
    else:
        record = {'slug': slug, 'name': name, 'description': description, 'image': '', 'card_image': '', 'hero_image': '', 'cover_image': '', 'active': True}
        series.append(record)
        message = f'{name} series added. Assign it to tile products below.'
    def save_series_image(kind, choice, uploaded, fallback=''):
        field = f'{kind}_image'
        previous = record.get(field) or fallback
        if uploaded and uploaded.filename:
            image_folder = os.path.join(UPLOAD_FOLDER, 'surfaces', 'series', slug)
            os.makedirs(image_folder, exist_ok=True)
            filename = f"{kind}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}.webp"
            image_path = f'uploads/surfaces/series/{slug}/{filename}'
            process_image(uploaded, os.path.join(app.static_folder, image_path))
            create_card_image(image_path)
            record[field] = image_path
        elif choice == 'keep-current' and previous:
            record[field] = previous
        elif choice in valid_cover_images:
            record[field] = choice
        else:
            record[field] = ''

    save_series_image('card', card_choice, card_file, record.get('cover_image', ''))
    save_series_image('hero', hero_choice, hero_file)
    if old_slug and old_slug != slug:
        configured_featured = load_homepage_featured_series_slugs()
        if old_slug in configured_featured:
            save_homepage_featured_series_slugs([slug if item == old_slug else item for item in configured_featured])
    # The old field remains as a fallback for existing data, but new edits use
    # card_image and hero_image independently. Retain files to avoid deleting an
    # image still used by the other slot or by a tile gallery.
    os.makedirs(os.path.dirname(TILE_SERIES_FILE), exist_ok=True)
    with open(TILE_SERIES_FILE, 'w', encoding='utf-8') as file:
        json.dump(series, file, indent=2, ensure_ascii=False)
    if old_slug and old_slug != slug:
        with open(SURFACE_DATA_FILE, 'w', encoding='utf-8') as file:
            json.dump(products, file, indent=2, ensure_ascii=False)
    flash(message, 'success')
    return redirect(url_for('tiles_manage'))

@app.route('/tiles/manage/series/<slug>/remove', methods=['POST'])
def tiles_manage_series_remove(slug):
    if not session.get('admin_logged'):
        return redirect(url_for('admin_login', next='tiles_manage'))
    series = load_tile_series()
    record = next((item for item in series if item.get('slug') == slug), None)
    if not record:
        return redirect(url_for('tiles_manage'))
    for image_path in {record.get('cover_image', ''), record.get('card_image', ''), record.get('hero_image', '')}:
        if image_path.startswith('uploads/surfaces/series/'):
            disk_path = os.path.join(app.static_folder, image_path)
            if os.path.isfile(disk_path):
                os.remove(disk_path)
            thumbnail_path = os.path.join(app.static_folder, card_image_disk_path(image_path))
            if os.path.isfile(thumbnail_path):
                os.remove(thumbnail_path)
    series = [item for item in series if item.get('slug') != slug]
    configured_featured = [item for item in load_homepage_featured_series_slugs() if item != slug]
    if configured_featured:
        save_homepage_featured_series_slugs(configured_featured)
    products = load_surface_products()
    changed = False
    for product in products:
        if product.get('department', 'tiles') == 'tiles' and slug in product.get('tags', []):
            product['tags'] = [tag for tag in product.get('tags', []) if tag != slug]
            changed = True
    with open(TILE_SERIES_FILE, 'w', encoding='utf-8') as file:
        json.dump(series, file, indent=2, ensure_ascii=False)
    if changed:
        with open(SURFACE_DATA_FILE, 'w', encoding='utf-8') as file:
            json.dump(products, file, indent=2, ensure_ascii=False)
    flash(f'{record.get("name", "Series")} removed. Products remain saved; assign them to another series to show them in the collection.', 'success')
    return redirect(url_for('tiles_manage'))

@app.route('/tiles/manage/brand', methods=['POST'])
def tiles_manage_brand():
    if not session.get('admin_logged'):
        return redirect(url_for('admin_login', next='tiles_manage'))
    old_slug = request.form.get('slug', '').strip()
    name = request.form.get('name', '').strip()
    department = request.form.get('department', 'tiles').strip().lower()
    description = request.form.get('description', '').strip()
    image_file = request.files.get('image')
    if not name or department not in {'tiles', 'bathware', 'both'}:
        flash('Enter a brand name and choose where it belongs.', 'danger')
        return redirect(url_for('tiles_manage'))
    brands = load_surface_brands()
    slug = tile_product_slug(name)
    existing = next((item for item in brands if item.get('slug') == old_slug), None) if old_slug else None
    if any(item.get('slug') == slug and item.get('slug') != old_slug for item in brands):
        flash('That brand already exists. Choose a unique brand name.', 'danger')
        return redirect(url_for('tiles_manage'))
    image = existing.get('image') if existing else ('images/surfaces/catalog/double-charge-800-room.jpg' if department == 'tiles' else 'images/sanitaryware/catalog/kohler-bathroom-suite.jpg')
    if image_file and image_file.filename:
        brand_folder = os.path.join(UPLOAD_FOLDER, 'surface-brands')
        os.makedirs(brand_folder, exist_ok=True)
        filename = f'{slug}.webp'
        process_image(image_file, os.path.join(brand_folder, filename))
        image = f'uploads/surface-brands/{filename}'
    if existing:
        previous_name = existing.get('name')
        if previous_name != name:
            products = load_surface_products()
            for product in products:
                if product.get('brand') == previous_name:
                    product['brand'] = name
            with open(SURFACE_DATA_FILE, 'w', encoding='utf-8') as file:
                json.dump(products, file, indent=2, ensure_ascii=False)
        existing.update({'slug': slug, 'name': name, 'department': department, 'description': description or f'Explore {name} products available through our showroom.', 'image': image, 'active': True})
    else:
        brands.append({'slug': slug, 'name': name, 'department': department, 'description': description or f'Explore {name} products available through our showroom.', 'image': image, 'active': True})
    with open(SURFACE_BRANDS_FILE, 'w', encoding='utf-8') as file:
        json.dump(brands, file, indent=2, ensure_ascii=False)
    flash(f'{name} has been {"updated" if existing else "added"}.', 'success')
    return redirect(url_for('tiles_manage'))

@app.route('/tiles/manage/brand/<slug>/remove', methods=['POST'])
def tiles_manage_brand_remove(slug):
    if not session.get('admin_logged'):
        return redirect(url_for('admin_login', next='tiles_manage'))
    brands = load_surface_brands()
    brand = next((item for item in brands if item.get('slug') == slug), None)
    if not brand:
        flash('That brand was not found.', 'warning')
        return redirect(url_for('tiles_manage'))
    remaining_brands = [item for item in brands if item.get('slug') != slug]
    with open(SURFACE_BRANDS_FILE, 'w', encoding='utf-8') as file:
        json.dump(remaining_brands, file, indent=2, ensure_ascii=False)
    products = load_surface_products()
    affected = 0
    for product in products:
        if str(product.get('brand', '')).lower() == brand['name'].lower():
            product['brand_removed'] = True
            affected += 1
    if affected:
        with open(SURFACE_DATA_FILE, 'w', encoding='utf-8') as file:
            json.dump(products, file, indent=2, ensure_ascii=False)
    image = brand.get('image', '')
    if image.startswith('uploads/surface-brands/'):
        image_path = os.path.join(app.static_folder, image)
        if os.path.isfile(image_path):
            os.remove(image_path)
    flash(f'{brand["name"]} was removed. {affected} associated products are kept in the manager and removed from public listings until reassigned.', 'success')
    return redirect(url_for('tiles_manage'))

@app.route('/tiles/manage/delete/<code>', methods=['POST'])
def tiles_manage_delete(code):
    if not session.get("admin_logged"):
        return redirect(url_for("admin_login", next="tiles_manage"))
    products = load_surface_products()
    deleted_product = next((item for item in products if item.get('code') == code), None)
    if deleted_product:
        clear_tile_series_cover_images(deleted_product.get('images', []))
        products = [item for item in products if item.get("code") != code]
        with open(SURFACE_DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(products, file, indent=2, ensure_ascii=False)
        import shutil
        folder = os.path.join(UPLOAD_FOLDER, "surfaces", code)
        if os.path.isdir(folder):
            shutil.rmtree(folder)
        flash("Product removed.", "success")
    return redirect(url_for("tiles_manage"))

@app.route('/tiles/services')
def tiles_services():
    # "Our approach" is now part of the About us page.
    return redirect(url_for('tiles_about') + '#how-we-work', code=301)

@app.route('/tiles/contact', methods=['GET', 'POST'])
def tiles_contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        interest = request.form.get('interest')
        message = request.form.get('message')

        if not name or not email:
            flash('Please enter your name and email address.', 'danger')
            return redirect(url_for('tiles_contact'))

        msg = Message('New Surfaces & Tiles Inquiry', recipients=['uniglobelifestyles@gmail.com'])
        msg.body = f"""Surfaces & Tiles Inquiry:
Name: {name}
Email: {email}
Phone: {phone or 'N/A'}
Interest: {interest or 'General surfaces inquiry'}
Message: {message or 'N/A'}
"""

        try:
            mail.send(msg)
            flash('Thank you. Our team will be in touch.', 'success')
        except Exception as e:
            print('Error sending surfaces inquiry:', e)
            flash('Something went wrong. Please try again or email our team.', 'danger')

        return redirect(url_for('tiles_contact'))

    return render_template('tiles_contact.html', selected_interest=request.args.get('interest', ''), surface_collections=surface_collections)

@app.route('/catalogs')
def catalogs():
    return render_template('catalogs.html')

@app.route('/about')
def about():
    return render_template('about.html')

import os

FURNITURE_ROOMS = [
    {'key': 'living', 'name': 'Living room', 'blurb': 'Sofas, lounge chairs, coffee and side tables.', 'image': 'images/living/living_room 19.webp'},
    {'key': 'dining', 'name': 'Dining', 'blurb': 'Dining tables, chairs, bar stools and sideboards.', 'image': 'images/dining/tables_catalog_18_1.webp'},
    {'key': 'bedroom', 'name': 'Bedroom', 'blurb': 'Beds, bedside tables and dressing tables.', 'image': 'images/bedroom/bed 15.webp'},
    {'key': 'modular', 'name': 'Cabinets &amp; storage', 'blurb': 'Sideboards, TV units, cabinets and shelving.', 'image': 'images/modular/plywood_cabinet 17.webp'},
    {'key': 'lighting', 'name': 'Lighting', 'blurb': 'Chandeliers, pendants and wall lights.', 'image': 'images/lighting/lighting 1.webp'},
    {'key': 'premium', 'name': 'Signature collection', 'blurb': 'Statement pieces and complete luxury looks.', 'image': 'images/premium/baxter_2_128_5.webp'},
]
FURNITURE_PAGE_SIZE = 24


def load_furniture_data():
    def read():
        try:
            with open(DATA_FILE, 'r') as file:
                data = json.load(file)
        except (OSError, ValueError):
            return {}
        return {key: value for key, value in data.items() if key in categories}
    return _request_memo('furniture_products', DATA_FILE, read) if os.path.exists(DATA_FILE) else {}


def furniture_card(category, item):
    images = item.get('images', [])
    cover = item.get('card_image') if item.get('card_image') in images else (images[0] if images else '')
    second = next((image for image in images if image != cover), '')
    cutouts = set(item.get('cutouts', []))
    return {
        'category': category, 'code': item.get('code', ''), 'title': item.get('title', 'Furniture piece'),
        'type': item.get('type', ''), 'model': item.get('model', ''),
        'image': cover, 'thumbnail': card_image_path(cover), 'hover': card_image_path(second) if second else '',
        'cutout': cover in cutouts, 'hover_cutout': second in cutouts,
        'size': (item.get('specs') or {}).get('Size', ''),
    }


def furniture_matches(item, words):
    if not words:
        return True
    haystack = ' '.join(str(value) for value in (item.get('title', ''), item.get('code', ''), item.get('model', ''), item.get('type', ''),
                                                  item.get('description', ''), ' '.join(str(v) for v in (item.get('specs') or {}).values()))).lower()
    return all(word in haystack for word in words)


@app.route('/products')
def products():
    data = load_furniture_data()
    selected_categories = [value for value in request.args.getlist('category') if value in data]
    selected_types = [value for value in request.args.getlist('type') if value.strip()]
    query = ' '.join(request.args.get('q', '').split())[:80]
    words = [word for word in re.split(r'[^a-z0-9.]+', query.lower()) if word]
    rooms = []
    for room in FURNITURE_ROOMS:
        section = data.get(room['key'], {})
        count = len(section.get('items', []))
        if count:
            rooms.append({**room, 'count': count, 'thumbnail': card_image_path(room['image'])})
    order = [room['key'] for room in FURNITURE_ROOMS if room['key'] in data] + [key for key in data if key not in {r['key'] for r in FURNITURE_ROOMS}]
    groups = [[(category, item) for item in data[category].get('items', []) if item.get('images')]
              for category in order if not selected_categories or category in selected_categories]
    if len(groups) > 1 and not selected_types and not words:
        # the whole collection: mix the rooms so the first screen shows a bit of everything
        pool = [entry for row in itertools.zip_longest(*groups) for entry in row if entry]
    else:
        pool = [entry for group in groups for entry in group]
    types = collections.Counter(item.get('type') for _, item in pool if item.get('type'))
    type_options = sorted(types.items(), key=lambda pair: (-pair[1], pair[0]))
    shown = [(category, item) for category, item in pool
             if (not selected_types or item.get('type') in selected_types) and furniture_matches(item, words)]
    try:
        cards_from = max(int(request.args.get('cards_from', 0)), 0)
    except ValueError:
        cards_from = 0
    page = shown[cards_from:cards_from + FURNITURE_PAGE_SIZE]
    cards = [furniture_card(category, item) for category, item in page]
    if cards_from:
        return render_template('_furniture_cards_page.html', cards=cards)
    room_lookup = {room['key']: room for room in FURNITURE_ROOMS}
    heading = room_lookup[selected_categories[0]]['name'] if len(selected_categories) == 1 else 'The collection'
    return render_template('products.html', rooms=rooms, cards=cards, total=len(shown), type_options=type_options,
                           selected_categories=selected_categories, selected_types=selected_types, query=query,
                           heading=heading, room_lookup=room_lookup, product_categories=data)


@app.route("/products/<category>/<code>")
def product_detail(category, code):
    data = load_furniture_data()
    category = category.lower()
    section = data.get(category)
    product = next((item for item in (section or {}).get('items', []) if item.get('code') == code), None)
    if product is None:
        return redirect(url_for('products'))
    product = dict(product)
    product['image_thumbnails'] = [card_image_path(image) for image in product.get('images', [])]
    cutouts = set(product.get('cutouts', []))
    views = [{'src': url_for('static', filename=image), 'thumb': url_for('static', filename=card_image_path(image)),
              'kind': 'cutout' if image in cutouts else 'room'} for image in product.get('images', [])]
    rooms = [view for view in views if view['kind'] == 'room']
    cuts = [view for view in views if view['kind'] == 'cutout']
    views = rooms + cuts
    same = [item for item in section['items'] if item is not None and item.get('code') != code and item.get('images')]
    related = [item for item in same if product.get('collection') and item.get('collection') == product.get('collection')]
    related += [item for item in same if item not in related and product.get('type') and item.get('type') == product.get('type')]
    related_cards = [furniture_card(category, item) for item in related[:8]]
    room = next((room for room in FURNITURE_ROOMS if room['key'] == category), None)
    return render_template('product_detail.html', product=product, category=category, views=views,
                           has_room_and_cutout=bool(rooms and cuts), related_cards=related_cards,
                           room_name=room['name'] if room else (section.get('display_name') or category.title()))


@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/projects')
def projects():
    return render_template('projects.html')

@app.route('/showroom', methods=['GET', 'POST'])
def showroom():
    today = datetime.today().strftime('%Y-%m-%d')  # Get today's date in proper format
    max_date = (datetime.today() + timedelta(days=30)).strftime('%Y-%m-%d')  # 30 days from today
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        date = request.form.get('date')
        location = request.form.get('location')
        message = request.form.get('message')

        if not name or not email or not date or not location:
            flash("All fields marked with * are required.", "danger")
            return redirect(url_for('showroom'))

        msg = Message("New Showroom Appointment", recipients=['uniglobelifestyles@gmail.com'])
        msg.body = f"""Showroom Booking Request:
Name: {name}
Email: {email}
Preferred Date: {date}
Location: {location}
Message: {message or 'N/A'}
"""
        try:
            mail.send(msg)
            flash("Appointment request submitted successfully.", "success")
        except Exception as e:
            print("Error sending mail:", e)
            flash("Something went wrong while sending the email. Please try again.", "danger")

        return redirect(url_for('showroom'))

    return render_template('showroom.html', today=today)


@app.route("/blog")
def blog():
    return render_template("blog.html")

@app.route("/blog/<slug>")
def blog_post(slug):
    return render_template(f"blog/{slug}.html")


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        form_type = request.form.get('form_type')

        if form_type == 'quote':
            phone = request.form.get('phone')
            interest = request.form.get('interest')
            message = request.form.get('message')

            msg = Message("New Quotation Request", recipients=['uniglobelifestyles@gmail.com'])
            msg.body = f"""Quotation Request:
Name: {name}
Email: {email}
Phone: {phone}
Interests: {interest}
Message: {message}
"""
        else:
            category = request.form.get('category')
            product_code = request.form.get('product_code')
            product_message = request.form.get('product_message')

            msg = Message("Product Price Inquiry", recipients=['uniglobelifestyles@gmail.com'])
            msg.body = f"""Product Inquiry:
Name: {name}
Email: {email}
Category: {category}
Product Description: {product_code}
Message: {product_message}
"""

        try:
            mail.send(msg)
            flash("Thank you for contacting us!", "success")
        except Exception as e:
            print("Error sending mail:", e)
            flash("Failed to send message. Please try again.", "danger")

        return redirect(url_for('contact'))

    return render_template('contact.html')






def process_image(image_file, save_path, keep_original=False, max_width=1600, quality=85):

    img = ImageOps.exif_transpose(Image.open(image_file))

    # Convert to RGB safely
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Resize proportionally (NO distortion)
    if img.width > max_width:
        ratio = max_width / float(img.width)
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)

    img.save(save_path, "WEBP", quality=quality, optimize=True)

    # Save original if requested
    if keep_original:
        image_file.seek(0)
        original_extension = image_file.filename.split('.')[-1]
        original_path = save_path.replace(".webp", f"_original.{original_extension}")
        with open(original_path, "wb") as f:
            f.write(image_file.read())


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":
        password = request.form.get("password")

        if password == "1234":
            session["admin_logged"] = True
            if request.args.get("next") == "tiles_manage":
                return redirect(url_for("tiles_manage"))
            return redirect(url_for("upload"))
        else:
            flash("Incorrect password", "danger")

    return render_template("admin_login.html")

@app.route("/upload", methods=["GET", "POST"])
def upload():

    # ---------------------------
    # AUTH CHECK
    # ---------------------------
    if not session.get("admin_logged"):
        flash("Please log in to access the upload page.", "warning")
        return redirect(url_for("admin_login"))

    # ---------------------------
    # LOAD DATA
    # ---------------------------
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {}

    existing_categories = list(data.keys())

    # ---------------------------
    # EDIT MODE CHECK (GET)
    # ---------------------------
    edit_code = request.args.get("edit")
    edit_category = request.args.get("category")
    edit_product = None

    if edit_code and edit_category:
        edit_category = edit_category.lower()
        if edit_category in data:
            for item in data[edit_category]["items"]:
                if item["code"] == edit_code:
                    edit_product = item
                    break

    # ===========================
    # POST SUBMISSION
    # ===========================
    if request.method == "POST":

        is_edit = request.form.get("is_edit")
        edit_code = request.form.get("edit_code")
        edit_category = request.form.get("edit_category")

        # ---------------------------
        # CATEGORY + CODE
        # ---------------------------
        if is_edit:
            category = edit_category
            code = edit_code
        else:
            selected_category = request.form.get("category_select")
            new_category = request.form.get("new_category")

            if selected_category == "new":
                if not new_category or new_category.strip() == "":
                    return "Please provide a valid category name."
                category = new_category.strip().lower()
            else:
                category = selected_category

            category = category.replace(" ", "_")

            prefix = ''.join(word[0] for word in category.split('_')).upper()
            existing_count = len(data.get(category, {}).get("items", []))
            code = f"{prefix}{existing_count + 1:03d}"

        # ---------------------------
        # FORM DATA
        # ---------------------------
        title = request.form.get("title")
        description = request.form.get("description")
        brand = request.form.get("brand", "").strip()
        keep_original = request.form.get("keep_original") == "yes"

        specs_keys = request.form.getlist("spec_key[]")
        specs_values = request.form.getlist("spec_value[]")

        specs = {}
        for k, v in zip(specs_keys, specs_values):
            if k and v:
                specs[k] = v

        main_image = request.files.get("main_image")
        other_images = request.files.getlist("other_images[]")

        # ---------------------------
        # CREATE PRODUCT FOLDER
        # ---------------------------
        product_folder = os.path.join(UPLOAD_FOLDER, category, code)
        os.makedirs(product_folder, exist_ok=True)

        # ---------------------------
        # IMAGE HANDLING
        # ---------------------------
        if is_edit and edit_product:
            image_paths = edit_product.get("images", [])
        else:
            image_paths = []

        # MAIN IMAGE REQUIRED ONLY FOR NEW PRODUCTS
        if not is_edit:
            if not main_image or main_image.filename == "":
                return "Main image is required."

        # PROCESS MAIN IMAGE IF PROVIDED
        if main_image and main_image.filename != "":
            filename = secure_filename(main_image.filename)
            base_name = os.path.splitext(filename)[0]
            webp_name = base_name + ".webp"
            save_path = os.path.join(product_folder, webp_name)

            process_image(main_image, save_path, keep_original)

            new_main_path = f"uploads/{category}/{code}/{webp_name}"

            if is_edit and image_paths:
                # Remove old main image
                old_main = image_paths.pop(0)
                full_old_path = os.path.join(app.static_folder, old_main)
                if old_main != new_main_path and os.path.exists(full_old_path):
                    os.remove(full_old_path)
                old_thumbnail = os.path.join(app.static_folder, card_image_disk_path(old_main))
                if os.path.isfile(old_thumbnail):
                    os.remove(old_thumbnail)

                image_paths.insert(0, new_main_path)
            else:
                image_paths.insert(0, new_main_path)

        # PROCESS ADDITIONAL IMAGES
        for file in other_images:
            if file and file.filename != "":
                filename = secure_filename(file.filename)
                base_name = os.path.splitext(filename)[0]
                webp_name = base_name + ".webp"
                save_path = os.path.join(product_folder, webp_name)

                process_image(file, save_path, keep_original)
                image_paths.append(f"uploads/{category}/{code}/{webp_name}")

        for image_path in image_paths:
            if image_path.startswith(f'uploads/{category}/{code}/'):
                create_card_image(image_path)

        # ---------------------------
        # UPDATE JSON
        # ---------------------------
        if category not in data:
            data[category] = {
                "display_name": category.title(),
                "items": []
            }

        if is_edit:
            for item in data[category]["items"]:
                if item["code"] == code:
                    item["title"] = title
                    item["description"] = description
                    item["brand"] = brand
                    item["specs"] = specs
                    item["images"] = image_paths
                    break
            flash("Product Updated Successfully", "success")
        else:
            data[category]["items"].append({
                "code": code,
                "title": title,
                "description": description,
                "brand": brand,
                "specs": specs,
                "images": image_paths
            })
            flash(f"Product Uploaded Successfully — Code: {code}", "success")

        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

        return redirect(url_for("upload"))

    # ===========================
    # GET RENDER
    # ===========================
    return render_template(
        "upload.html",
        categories=existing_categories,
        products=data,
        edit_product=edit_product,
        edit_category=edit_category
    )


@app.route("/delete-product/<category>/<code>", methods=["POST"])
def delete_product(category, code):

    if not session.get("admin_logged"):
        return redirect(url_for("admin_login"))

    if not os.path.exists(DATA_FILE):
        return redirect(url_for("upload"))

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    category = category.lower()

    if category in data:
        data[category]["items"] = [
            item for item in data[category]["items"]
            if item["code"] != code
        ]

        if not data[category]["items"]:
            del data[category]

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

    # Delete folder
    product_folder = os.path.join(UPLOAD_FOLDER, category, code)
    if os.path.exists(product_folder):
        import shutil
        shutil.rmtree(product_folder)

    flash("Product Deleted Successfully", "success")
    return redirect(url_for("upload"))

@app.route("/reorder-images/<category>/<code>", methods=["POST"])
def reorder_images(category, code):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    new_order = request.json.get("images")

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    if category in data:
        for item in data[category]["items"]:
            if item["code"] == code:
                item["images"] = new_order
                break

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

    return {"status": "success"}


@app.route("/delete-image/<category>/<code>", methods=["POST"])
def delete_image(category, code):

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    image_path = request.form.get("image_path")

    if not image_path:
        return redirect(url_for("upload"))

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    if category in data:
        for item in data[category]["items"]:
            if item["code"] == code:

                if image_path in item["images"]:
                    item["images"].remove(image_path)

                    # Delete file from disk
                    full_path = os.path.join(app.static_folder, image_path)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                    thumbnail_path = os.path.join(app.static_folder, card_image_disk_path(image_path))
                    if os.path.isfile(thumbnail_path):
                        os.remove(thumbnail_path)

                break

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

    flash("Image Deleted Successfully", "success")
    return redirect(url_for("upload", edit=code, category=category))

@app.route("/admin-logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))


if __name__ == '__main__':
    app.run(debug=True)
