from flask import Flask, render_template, request, redirect, flash, url_for
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import os
import json
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


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

UPLOAD_FOLDER = os.path.join(app.static_folder, "uploads")
DATA_FILE = os.path.join(app.static_folder, "data", "products.json")

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

@app.route('/catalogs')
def catalogs():
    return render_template('catalogs.html')

@app.route('/about')
def about():
    return render_template('about.html')

import os

@app.route('/products')
def products():
    base_path = os.path.join(app.static_folder, 'images')

    category_display_names = {
        'bedroom': 'Bedroom & Beds',
        'living': 'Sofa & Lounge Seating',
        'dining': 'Dining & Coffee Tables',
        'modular': 'Modular Furniture and Cabinets',
        'lighting': 'Lighting & Fixtures',
        'sanitaryware': 'Sanitaryware & Bathroom Fittings',
        'Premium': 'Premuim Collection'
    }

    category_prefixes = {
        'bedroom': 'BD',
        'living': 'LV',
        'dining': 'DG',
        'modular': 'MC',
        'lighting': 'LG',
        'sanitaryware': 'SW',
        'premium': 'PC'
    }

    product_images = {}

    for category, prefix in category_prefixes.items():
        folder_path = os.path.join(base_path, category)
        if os.path.isdir(folder_path):
            images = sorted(os.listdir(folder_path))
            product_images[category] = {
                'display_name': category_display_names.get(category, category.title()),
                'items': []
            }
            for i, img in enumerate(images, start=1):
                if img.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    code = f"{prefix}{i}"
                    product_images[category]['items'].append({
                        'filename': img,
                        'code': code
                    })

    return render_template('products.html', product_images=product_images)

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


@app.route("/upload", methods=["GET", "POST"])
def upload():

    # Load existing data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {}

    existing_categories = list(data.keys())

    if request.method == "POST":

        # ---------------------------
        # CATEGORY HANDLING
        # ---------------------------
        selected_category = request.form.get("category_select")
        new_category = request.form.get("new_category")

        if selected_category == "new":
            if not new_category or new_category.strip() == "":
                return "Please provide a valid category name."
            category = new_category.strip().lower()
        else:
            category = selected_category

        category = category.replace(" ", "_")

        # ---------------------------
        # AUTO PRODUCT CODE (PER CATEGORY)
        # ---------------------------
        prefix = category[:3].upper()   # first 3 letters
        existing_count = len(data.get(category, {}).get("items", []))
        code = f"{prefix}{existing_count + 1:03d}"

        # ---------------------------
        # OTHER FORM DATA
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
        other_images = request.files.getlist("other_images")

        # ---------------------------
        # MAIN IMAGE VALIDATION
        # ---------------------------
        if not main_image or main_image.filename == "":
            return "Main image is required."

        # ---------------------------
        # CREATE PRODUCT FOLDER
        # ---------------------------
        product_folder = os.path.join(UPLOAD_FOLDER, category, code)
        os.makedirs(product_folder, exist_ok=True)

        image_paths = []

        # ---------------------------
        # PROCESS MAIN IMAGE
        # ---------------------------
        filename = secure_filename(main_image.filename)
        base_name = os.path.splitext(filename)[0]
        webp_name = base_name + ".webp"
        save_path = os.path.join(product_folder, webp_name)

        process_image(main_image, save_path, keep_original)
        image_paths.append(f"uploads/{category}/{code}/{webp_name}")

        # ---------------------------
        # PROCESS ADDITIONAL IMAGES
        # ---------------------------
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

        data[category]["items"].append({
            "code": code,
            "title": title,
            "description": description,
            "specs": specs,
            "images": image_paths
        })

        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

        return f"Product Uploaded Successfully — Code: {code}"

    return render_template("upload.html", categories=existing_categories)

if __name__ == '__main__':
    app.run(debug=True)
