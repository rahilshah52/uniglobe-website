import code
from unicodedata import category

from flask import Flask, render_template, request, redirect, flash, url_for, session
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
            session["admin_logged_in"] = True
            return redirect(url_for("upload"))
        else:
            flash("Incorrect password", "danger")

    return render_template("admin_login.html")

@app.route("/upload", methods=["GET", "POST"])
def upload():

    # ---------------------------
    # AUTH CHECK
    # ---------------------------
    if not session.get("admin_logged_in"):
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
