import code
from unicodedata import category

from flask import Flask, render_template, request, redirect, flash, url_for, session
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import os
import json
import re
from werkzeug.utils import secure_filename
from PIL import Image

# List of product categories (editable!)
categories = ['bedroom', 'living', 'dining', 'modular', 'lighting', 'sanitaryware', 'premium']
# Put this near the top or in a global config section
homepage_display = {
    'bedroom': 'images/bedroom/bed 15.webp',
    'living': 'images/living/living_room 19.webp',
    'dining': 'images/dining/tables_catalog_18_1.webp',
    'modular': 'images/modular/plywood_cabinet 17.webp',
    'lighting': 'images/lighting/lighting 1.webp',
    'sanitaryware': 'images/sanitaryware/washbasin_faucets 78.webp',
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
        'name': 'Punch Matt & Carving Matt',
        'description': 'Textured 5 mm surfaces with distinctive matt and carved finishes.',
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
    return render_template('tiles_home.html', surface_collections=surface_collections[:3])

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
            'items': [('Jaquar', 'jaquar-basin-lifestyle.jpg', 'Sanitaryware and basin setting'), ('KOHLER', 'kohler-sanitaryware-setting.jpg', 'Sanitaryware in a contemporary interior'), ('KOHLER', 'kohler-toilet-feature.jpg', 'Sanitaryware detail'), ('Simpolo', 'simpolo-sanitaryware-feature.jpg', 'Sanitaryware catalogue inspiration'), ('Simpolo', 'simpolo-bathroom-suite.jpg', 'Bathroom suite inspiration')],
        },
        {
            'slug': 'baths-wellness', 'number': '04', 'title': 'Baths & wellness',
            'description': 'A softer, more restorative direction for bathing spaces, with sculptural forms and warm materials.',
            'image': 'images/sanitaryware/catalog/kohler-bathing-space.jpg',
            'alt': 'KOHLER bathing space with freestanding tub',
            'items': [('Jaquar', 'jaquar-shower-setting.jpg', 'Bathing space inspiration'), ('KOHLER', 'kohler-bathing-space.jpg', 'Bathing space with freestanding tub'), ('KOHLER', 'kohler-bathroom-suite.jpg', 'Complete bathroom suite'), ('Simpolo', 'simpolo-bathroom-suite.jpg', 'Bathroom suite inspiration')],
        },
    ]
    for category in bath_categories:
        category['items'] = [
            {'brand': brand, 'image': f'images/sanitaryware/catalog/{image}', 'caption': caption}
            for brand, image, caption in category['items']
        ]
    return bath_categories

@app.route('/tiles/bath')
def tiles_bath():
    bath_categories = get_bath_categories()
    return render_template('tiles_bath.html', bath_categories=bath_categories)

@app.route('/tiles/bath/<slug>')
def tiles_bath_category(slug):
    category = next((item for item in get_bath_categories() if item['slug'] == slug), None)
    if category is None:
        return redirect(url_for('tiles_bath'))
    return render_template('tiles_bath_category.html', category=category)

@app.route('/tiles/collections')
def tiles_collections():
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
    return render_template('tiles_collections.html', surface_collections=surface_collections, surface_products=load_surface_products(), tile_catalog_groups=catalog_groups)

def tile_product_slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

@app.route('/tiles/product/<slug>')
def tiles_product_detail(slug):
    product = next((item for item in tile_lookbook_products if tile_product_slug(item['name']) == slug), None)
    if product is None:
        return redirect(url_for('tiles_collections'))

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
    return render_template('tiles_product_detail.html', product=product, gallery=gallery)

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

@app.route('/tiles/manage', methods=['GET', 'POST'])
def tiles_manage():
    if not session.get("admin_logged"):
        flash("Please log in to manage Surfaces products.", "warning")
        return redirect(url_for("admin_login", next="tiles_manage"))

    products = load_surface_products()
    edit_code = request.args.get("edit")
    edit_product = next((item for item in products if item.get("code") == edit_code), None)

    if request.method == "POST":
        code = request.form.get("code", "").strip()
        category = request.form.get("category", "Tiles").strip()
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        try:
            stock = max(0, int(request.form.get("stock", "0")))
        except ValueError:
            stock = 0
        if not title:
            flash("Please enter a product name.", "danger")
            return redirect(url_for("tiles_manage", edit=code or None))

        product = next((item for item in products if item.get("code") == code), None) if code else None
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
            for old_image in product.get("images", []):
                old_path = os.path.join(app.static_folder, old_image)
                if os.path.isfile(old_path):
                    os.remove(old_path)
            product["images"] = []
        for uploaded in files:
            if uploaded and uploaded.filename:
                filename = os.path.splitext(secure_filename(uploaded.filename))[0] + ".webp"
                process_image(uploaded, os.path.join(folder, filename))
                image_path = f"uploads/surfaces/{code}/{filename}"
                if image_path not in product["images"]:
                    product["images"].append(image_path)
        product.update({"category": category, "title": title, "description": description, "stock": stock})
        os.makedirs(os.path.dirname(SURFACE_DATA_FILE), exist_ok=True)
        with open(SURFACE_DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(products, file, indent=2, ensure_ascii=False)
        flash(f"{title} saved. Product code: {code}", "success")
        return redirect(url_for("tiles_manage"))

    return render_template("tiles_manage.html", products=products, edit_product=edit_product)

@app.route('/tiles/manage/delete/<code>', methods=['POST'])
def tiles_manage_delete(code):
    if not session.get("admin_logged"):
        return redirect(url_for("admin_login", next="tiles_manage"))
    products = load_surface_products()
    if any(item.get("code") == code for item in products):
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
        return render_template("products.html", product_data={})

    with open(DATA_FILE, "r") as f:
        product_data = json.load(f)

    return render_template("products.html", product_data=product_data)

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






def process_image(image_file, save_path, keep_original=False):

    img = Image.open(image_file)

    # Convert to RGB safely
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    max_width = 1600

    # Resize proportionally (NO distortion)
    if img.width > max_width:
        ratio = max_width / float(img.width)
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)

    img.save(save_path, "WEBP", quality=85, optimize=True)

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
                if os.path.exists(full_old_path):
                    os.remove(full_old_path)

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
                    item["specs"] = specs
                    item["images"] = image_paths
                    break
            flash("Product Updated Successfully", "success")
        else:
            data[category]["items"].append({
                "code": code,
                "title": title,
                "description": description,
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

    if not session.get("admin_logged_in"):
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
