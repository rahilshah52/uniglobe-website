import code
from unicodedata import category

from flask import Flask, render_template, request, redirect, flash, url_for, session
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import os
import json
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

@app.route('/')
def home():
    return render_template('index1.html', homepage_display=homepage_display, homepage_display_names=homepage_display_names)

@app.route('/tiles')
def tiles_home():
    brands = [item for item in load_surface_brands() if item.get('active', True) and item.get('department') in {'bathware', 'both'}]
    return render_template('tiles_home.html', surface_collections=get_homepage_featured_series(), brands=brands)

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
    brands = [item for item in load_surface_brands() if item.get('active', True) and item.get('department') in {'bathware', 'both'}]
    return render_template('tiles_bath.html', bath_categories=bath_categories, brands=brands)

def get_all_bath_categories():
    bath_categories = get_bath_categories()
    active_bath_brands = {item['name'].lower() for item in load_surface_brands() if item.get('active', True) and item.get('department') in {'bathware', 'both'}}
    for category in bath_categories:
        category['items'] = [item for item in category['items'] if item['brand'].lower() in active_bath_brands]
    bath_products = [item for item in load_surface_products() if item.get('department') == 'bathware' and is_public_surface_product(item, 'bathware')]
    categories_by_name = {item['title'].lower(): item for item in bath_categories}
    for product in bath_products:
        title = product.get('category') or 'Other bathware'
        key = title.lower()
        category = categories_by_name.get(key)
        if category is None:
            category = {'slug': tile_product_slug(title), 'number': f'{len(bath_categories) + 1:02d}', 'title': title,
                        'description': f'Explore {title.lower()} from the brands available in our showroom.',
                        'image': (product.get('images') or ['images/sanitaryware/catalog/kohler-bathroom-suite.jpg'])[0],
                        'alt': f'{title} from our bathware collection', 'items': []}
            bath_categories.append(category)
            categories_by_name[key] = category
        for image in product.get('images', []):
            category['items'].append({'brand': product.get('brand', 'Other'), 'image': image,
                                      'caption': product.get('title', title), 'product_code': product.get('code')})
    for category in bath_categories:
        category['image'] = card_image_path(category.get('image', ''))
        for item in category['items']:
            item['thumbnail'] = card_image_path(item.get('image', ''))
    return bath_categories

@app.route('/tiles/bath/<slug>')
def tiles_bath_category(slug):
    category = next((item for item in get_all_bath_categories() if item['slug'] == slug), None)
    if category is None:
        return redirect(url_for('tiles_bath'))
    brands = sorted({item['brand'] for item in category['items']}, key=str.lower)
    selected_brands = [value.strip() for value in request.args.getlist('brand') if value.strip()]
    selected_brand_names = {brand.lower() for brand in selected_brands}
    items = [item for item in category['items'] if not selected_brands or item['brand'].lower() in selected_brand_names]
    return render_template('tiles_bath_category.html', category=category, brands=brands, selected_brands=selected_brands, items=items)

@app.route('/tiles/bath/brand/<brand_slug>')
def tiles_bath_brand(brand_slug):
    brand_record = next((item for item in load_surface_brands() if item.get('slug') == brand_slug.lower() and item.get('active', True) and item.get('department') in {'bathware', 'both'}), None)
    if brand_record is None:
        return redirect(url_for('tiles_bath'))
    brand = brand_record['name']
    products = []
    selected_categories = [value.strip() for value in request.args.getlist('category') if value.strip()]
    bath_categories = get_all_bath_categories()
    categories = sorted({(category['title'], category['slug']) for category in bath_categories
                        if any(item['brand'].lower() == brand.lower() for item in category['items'])}, key=lambda value: value[0].lower())
    selected_category_names = [title for title, slug in categories if slug in selected_categories]
    for category in bath_categories:
        for item in category['items']:
            if item['brand'].lower() == brand.lower() and (not selected_categories or category['slug'] in selected_categories):
                products.append({**item, 'category': category['title'], 'category_slug': category['slug']})
    brand_image = brand_record.get('image') or f'images/sanitaryware/brands/{brand_slug}-bath-inspiration.jpg'
    return render_template('tiles_bath_brand.html', brand=brand, brand_slug=brand_slug, brand_image=brand_image, products=products, categories=categories, selected_categories=selected_categories, selected_category_names=selected_category_names)

def get_tile_category_groups():
    available_series = []
    tile_products = [product for product in load_surface_products() if product.get('department', 'tiles') == 'tiles']
    for series_record in load_tile_series():
        if not series_record.get('active', True):
            continue
        representative = next((get_surface_product_cover(product) for product in tile_products
                               if series_record.get('slug') in get_product_tile_tags(product)
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
            group['items'] = [(name, image) for name, image in group['items']
                              if tile_product_slug(name) not in removed]
            existing = {tile_product_slug(name) for name, _ in group['items']}
            for option in settings.get('added', []):
                option_name = str(option.get('name', '')).strip()
                option_slug = tile_product_slug(option_name)
                if option_name and option_slug not in removed and option_slug not in existing:
                    group['items'].append((option_name, option.get('image') or 'images/surfaces/catalog/double-charge-800-room.jpg'))
                    existing.add(option_slug)
        group['cards'] = [
            {'name': name, 'image': image, 'default_image': image, 'thumbnail': card_image_path(image), 'slug': tile_product_slug(name)}
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
                matching_product = next((product for product in tile_products
                    if card['slug'] in get_product_tile_tags(product)
                    or card['slug'] in {tile_product_slug(size) for size in get_product_tile_sizes(product)}), None)
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
        settings['removed'] = [item for item in settings['removed'] if item != slug]
        if slug not in existing:
            settings['added'] = [item for item in settings['added'] if tile_product_slug(item.get('name', '')) != slug]
            settings['added'].append({'name': name, 'image': 'images/surfaces/catalog/double-charge-800-room.jpg'})
        save_tile_facet_config(config)
        flash(f'{name} added to {group_slug.replace("-", " ").title()}.', 'success')
    elif action == 'remove' and option_slug:
        settings['added'] = [item for item in settings['added'] if tile_product_slug(item.get('name', '')) != option_slug]
        if option_slug not in settings['removed']:
            settings['removed'].append(option_slug)
        save_tile_facet_config(config)
        flash('Category option removed. Existing product assignments are saved and can be restored by adding the same option again.', 'success')
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

def get_product_tile_sizes(product):
    """Return tile dimensions found in product details in a consistent form."""
    details = str(product.get('details', ''))
    sizes = []
    pattern = r'(?<!\d)(\d{2,4})\s*(?:x|×|\*)\s*(\d{2,4})(?:\s*(?:x|×|\*)\s*(\d{1,2}(?:\.\d+)?))?(?:\s*mm)?'
    for width, height, thickness in re.findall(pattern, details, flags=re.IGNORECASE):
        thickness_label = f' × {format(float(thickness), "g")}' if thickness else ''
        name = f'{width} × {height}{thickness_label} mm'
        if name not in sizes:
            sizes.append(name)
    if re.search(r'\brockdeck\b.*?15\s*mm', details, flags=re.IGNORECASE):
        sizes.append('Rockdeck · 15 mm')
    return sizes

def get_product_tile_tags(product):
    """Include dimensions from the details field for older products too."""
    tags = set(product.get('tags', []))
    tags.update(tile_product_slug(size) for size in get_product_tile_sizes(product))
    return tags

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
    category = (f'{brand_name} · All tile collections' if all_brand_products else
                f'{selected_series["name"]} · {category_item["name"]}' if selected_series and group_slug != 'collection' else
                f'{selected_series["name"]} Series' if selected_series else category_item['name'])
    series_image = next((image for item in products for image in item.get('images', []) if image), None)
    category_image = (selected_series.get('hero_image') or category_item.get('hero_image', category_item['image'])) if selected_series else category_item.get('hero_image', category_item['image'])
    return render_template('tiles_category_products.html', group=group, category=category, category_image=category_image, category_image_portrait=is_portrait_surface_image(category_image), products=products, brand=brand_name, brand_slug=brand_slug, filter_groups=filter_groups, available_brands=available_brands, selected_filters=selected, selected_series=selected_series, selected_series_slug=selected_series_slug)

@app.route('/tiles/collections/brand/<slug>')
def tiles_collection_brand(slug):
    brand_record = next((item for item in load_surface_brands() if item.get('slug') == slug.lower() and item.get('active', True) and item.get('department') in {'tiles', 'both'}), None)
    if brand_record:
        return render_template('tiles_collection_home.html', tile_category_groups=get_tile_category_groups(), tile_brands=[brand_record], brand=brand_record['name'], brand_slug=brand_record['slug'])
    return redirect(url_for('tiles_collections'))

@app.route('/tiles/wishlist')
def tiles_wishlist():
    return render_template('tiles_wishlist.html')

@app.route('/wishlist')
def furniture_wishlist():
    return render_template('furniture_wishlist.html')

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
    return render_template('tiles_collections.html', surface_collections=surface_collections, surface_products=surface_products, tile_catalog_groups=catalog_groups, brand=None)

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
    return render_template('tiles_product_detail.html', product=product, gallery=gallery,
                           wishlist_image=url_for('static', filename=gallery[0]['src']),
                           wishlist_url=request.full_path.rstrip('?'))

@app.route('/tiles/product-uploaded/<code>')
def tiles_uploaded_product_detail(code):
    item = next((product for product in load_surface_products() if product.get('code') == code), None)
    if item is None or item.get('department', 'tiles') != 'tiles' or not is_public_surface_product(item, 'tiles') or not item.get('images'):
        return redirect(url_for('tiles_collections'))
    assigned_tags = get_product_tile_tags(item)
    series_record = next((series for series in load_tile_series()
                          if series.get('slug') in assigned_tags), None)
    selected_specs = {'size': [], 'look-feel': [], 'color': []}
    if item.get('department', 'tiles') == 'tiles':
        for group in get_tile_category_groups():
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
        'series_name': series_record.get('name', '') if series_record else '',
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
    return render_template('tiles_product_detail.html', product=product, gallery=gallery,
                           demo=item.get('demo', False), brand_slug=brand_slug, return_to=return_to,
                           wishlist_image=url_for('static', filename=gallery[0]['src']),
                           wishlist_url=request.full_path.rstrip('?'))

@app.route('/tiles/about')
def tiles_about():
    return render_template('tiles_about.html')

def load_surface_products():
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
    return render_template('tiles_services.html')

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

@app.route('/products')
def products():
    if not os.path.exists(DATA_FILE):
        return render_template("products.html", product_data={}, product_categories={}, product_brands=[], selected_categories=[], selected_brands=[])

    with open(DATA_FILE, "r") as f:
        all_product_data = json.load(f)

    # The general products file can also contain legacy surface records. Keep
    # the furniture storefront scoped to the furniture categories above.
    furniture_product_data = {key: value for key, value in all_product_data.items() if key in categories}
    selected_categories = [value for value in request.args.getlist('category') if value in furniture_product_data]
    selected_brands = list(dict.fromkeys(value.strip() for value in request.args.getlist('brand') if value.strip()))
    product_brands = sorted({str(item.get('brand', '')).strip() for section in furniture_product_data.values()
                              for item in section.get('items', []) if str(item.get('brand', '')).strip()}, key=str.lower)
    product_data = {}
    selected_brand_names = {value.lower() for value in selected_brands}
    for category, section in furniture_product_data.items():
        if selected_categories and category not in selected_categories:
            continue
        matching_items = [item for item in section.get('items', [])
                          if not selected_brands or str(item.get('brand', '')).strip().lower() in selected_brand_names]
        if matching_items:
            product_data[category] = {**section, 'items': matching_items}

    for section in product_data.values():
        for item in section.get('items', []):
            item['thumbnail'] = card_image_path(item.get('images', [''])[0] if item.get('images') else '')

    return render_template("products.html", product_data=product_data, product_categories=furniture_product_data,
                           product_brands=product_brands, selected_categories=selected_categories,
                           selected_brands=selected_brands)

@app.route("/products/<category>/<code>")
def product_detail(category, code):

    if not os.path.exists(DATA_FILE):
        return "No products found."

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    category = category.lower()

    if category not in data:
        return "Category not found."

    for product in data[category]["items"]:
        if product["code"] == code:
            product['image_thumbnails'] = [card_image_path(image) for image in product.get('images', [])]
            return render_template(
                "product_detail.html",
                product=product
            )

    return "Product not found."

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
