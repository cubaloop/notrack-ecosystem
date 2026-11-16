#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prototype Factory Engine — Tecnoemprende Dubai
Ultra-fast, automated generation of luxury business prototypes from Jota CRM.
Follows all Master Permanent Rules:
- Rule 4: Luxury Light-First dual theme, Bento Grid, Arch frames, authentic social proof.
- Rule 5: WhatsApp button strictly icon-only (no text, no numbers).
- Rule 8: Developed by Tecnoemprende in footer, minimalist header (Brand + WA + ☰), video background.
- Rule 9: Sequential Gatekeeper (David WhatsApp approval prior to client contact).
- Rule 14: Universal Spy Tracker v2 registration and injection.
"""

import os
import sys
import re
import json
import sqlite3
import shutil
import urllib.request
import subprocess
from datetime import datetime

# UTF-8 stdout
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS_DIR = os.path.join(ROOT_DIR, "docs", "preview")
ASSETS_DIR = os.path.join(DOCS_DIR, "_niche_assets")
CRM_DB = os.path.expandvars(r"%LOCALAPPDATA%\Jota\data\crm.db")
WA_GATEWAY_URL = "http://127.0.0.1:3001/send"
SUPABASE_URL = "https://jyrqzjctkmzdvmraqrcv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp5cnF6amN0a216ZHZtcmFxcmN2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NjI4MTU3NCwiZXhwIjoyMTAxODU3NTc0fQ.jpzy38i_JqhKiLZwNFXESJo62kk4vWvwCVPLpFIyLjc"
DAVID_PHONE = "971508379080"

NICHE_CONFIGS = {
    "gents_barber": {
        "title_en": "Bespoke Grooming & Royal Barbering • Dubai",
        "title_ar": "صالون حلاقة رجالي راقٍ • دبي",
        "badge_en": "Gents Salon & Spa",
        "badge_ar": "صالون وسبا للرجال",
        "hero_title_en": 'The art of timeless <em class="brass-text">gentleman’s grooming</em>',
        "hero_title_ar": 'فنّ الحلاقة الفاخرة <em class="brass-text">والعناية الملكية للرجال</em>',
        "hero_desc_en": "Precision haircuts, hot towel beard sculpting, authentic Moroccan bath, and executive VIP care in a private club ambiance.",
        "hero_desc_ar": "قصات شعر دقيقة، نحت اللحية بالفوطة الساخنة، حمام مغربي أصيل وعناية تنفيذية VIP في أجواء نادي خاص راقٍ.",
        "categories_en": ["All", "Haircuts & Fades", "Beard Sculpting", "Moroccan Bath", "VIP Packages"],
        "categories_ar": ["الكل", "قصات شعر", "تشذيب اللحية", "الحمام المغربي", "باقات VIP"],
        "services": [
            {
                "id": "svc-1", "name_en": "Executive Royal Haircut & Styling", "name_ar": "قص شعر ملكي وتصفيف تنفيذي",
                "price": 140, "duration": "45 min", "category_en": "Haircuts & Fades", "category_ar": "قصات شعر",
                "desc_en": "Precision scissor artistry, skin taper fade, scalp revitalizing wash and French matte finish.",
                "desc_ar": "قص احترافي بالمقص، تدرج دقيق، غسيل منشط لفروة الرأس وتصفيف نهائي أنيق.",
                "image": "haircut.jpg", "badge_en": "Signature", "badge_ar": "الأكثر طلباً"
            },
            {
                "id": "svc-2", "name_en": "Hot Towel Beard Sculpting & Razor Edge", "name_ar": "نحت اللحية بالفوطة الساخنة والموس",
                "price": 85, "duration": "30 min", "category_en": "Beard Sculpting", "category_ar": "تشذيب اللحية",
                "desc_en": "Ozone steam prep, straight-razor contouring, organic beard elixir, and cold stone soothing press.",
                "desc_ar": "تهيئة بالبخار، تحديد دقيق بالموس المستقيم، زيت عضوي فاخر وتدليك بالحجر البارد.",
                "image": "beard.jpg", "badge_en": "Gentleman Craft", "badge_ar": "حرفية كلاسيكية"
            },
            {
                "id": "svc-3", "name_en": "Authentic Moroccan Hammam & Steam Bath", "name_ar": "حمام مغربي تقليدي وغرفة بخار",
                "price": 250, "duration": "60 min", "category_en": "Moroccan Bath", "category_ar": "الحمام المغربي",
                "desc_en": "Private marble steam suite, traditional black olive soap exfoliation with kessa glove, and rosewater mist.",
                "desc_ar": "جناح رخام خاص بالبخار، فرك بالصابون المغربي الأسود بكيس الكيسة الأصيل وترطيب بماء الورد.",
                "image": "bath.jpg", "badge_en": "Private Suite", "badge_ar": "جناح خاص"
            },
            {
                "id": "svc-4", "name_en": "Charcoal Detox Facial & Ultrasonic Cleansing", "name_ar": "تنظيف بشرة بالفحم والتقشير فوق الصوتي",
                "price": 180, "duration": "45 min", "category_en": "Haircuts & Fades", "category_ar": "قصات شعر",
                "desc_en": "Deep pore suction, activated charcoal mask, cold mist infusion, and facial lymph drainage massage.",
                "desc_ar": "تنظيف عميق للمسام، قناع الفحم النشط، ترطيب برذاذ بارد وتدليك لتصريف السوائل.",
                "image": "facial.jpg", "badge_en": "Glow Ritual", "badge_ar": "نضارة فورية"
            },
            {
                "id": "svc-5", "name_en": "VIP Executive Grooming Suite Experience", "name_ar": "الباقة الملكية المتكاملة لكبار الشخصيات VIP",
                "price": 390, "duration": "90 min", "category_en": "VIP Packages", "category_ar": "باقات VIP",
                "desc_en": "Full haircut, beard sculpting, royal manicure/pedicure, express facial, and specialty coffee service.",
                "desc_ar": "قص شعر كامل، تحديد لحية، مانيكير وبديكير، جلسة نضارة وضيافة قهوة مختصة في جناح خاص.",
                "image": "lounge.jpg", "badge_en": "All Inclusive", "badge_ar": "شامل بالكامل"
            }
        ],
        "amenity_1": {"en": "Espresso & Tea Bar", "ar": "ركن القهوة المختصة", "sub_en": "Complimentary artisan refreshments", "sub_ar": "ضيافة فاخرة مجانية", "icon": "fa-mug-saucer"},
        "amenity_2": {"en": "Hospital-Grade Hygiene", "ar": "تعقيم طبي فائق", "sub_en": "Autoclave-sealed single-use blades", "sub_ar": "شفرات وأدوات مغلفة ومعقمة", "icon": "fa-shield-halved"}
    },
    "ladies_beauty": {
        "title_en": "Ladies Beauty Salon & Spa • Dubai",
        "title_ar": "صالون وسبا للسيدات • دبي",
        "badge_en": "Ladies Salon & Spa",
        "badge_ar": "صالون وسبا للسيدات",
        "hero_title_en": 'The art of timeless <em class="brass-text">beauty & luxury care</em>',
        "hero_title_ar": 'فنّ الجمال الراقي <em class="brass-text">والعناية الملكية للسيدات</em>',
        "hero_desc_en": "Haute couture hair styling, 24K gold facial rituals, Russian nail contouring, and authentic Moroccan hammam in an exclusive ladies sanctuary.",
        "hero_desc_ar": "تصفيف شعر راقٍ، طقوس نضارة الوجه بالذهب 24 قيراط، مانيكير روسي وحمام مغربي ملكي في أجواء من الخصوصية التامة للسيدات.",
        "categories_en": ["All", "Hair & Styling", "Facials & Skin", "Nails & Spa", "VIP Packages"],
        "categories_ar": ["الكل", "الشعر والتصفيف", "البشرة والنضارة", "الأظافر والسبا", "باقات VIP"],
        "services": [
            {
                "id": "svc-1", "name_en": "Signature Keratin & Silk Blowout", "name_ar": "كيراتين ملكي وتصفيف شعر حريري",
                "price": 180, "duration": "60 min", "category_en": "Hair & Styling", "category_ar": "الشعر والتصفيف",
                "desc_en": "Deep caviar keratin infusion and couture blowout styling for radiant, frizz-free luxury shine.",
                "desc_ar": "علاج الكيراتين بالكافيار وتصفيف احترافي يمنح شعرك لمعاناً ونعومة فائقة.",
                "image": "haircut.jpg", "badge_en": "Most Popular", "badge_ar": "الأكثر طلباً"
            },
            {
                "id": "svc-2", "name_en": "HydraFacial & 24K Gold Glow Ritual", "name_ar": "هيدرافيشل وطقس نضارة الذهب 24 قيراط",
                "price": 250, "duration": "60 min", "category_en": "Facials & Skin", "category_ar": "البشرة والنضارة",
                "desc_en": "Multi-step vortex hydration, botanical vitamin infusion, and 24K gold collagen mask for luminous skin.",
                "desc_ar": "تنظيف عميق وترطيب مكثف بالفيتامينات مع قناع الذهب والكولاجين لبشرة مشرقة.",
                "image": "facial.jpg", "badge_en": "Signature Glow", "badge_ar": "إشراقة ملكية"
            },
            {
                "id": "svc-3", "name_en": "Russian Gel Manicure & Royal Spa Pedicure", "name_ar": "مانيكير جل روسي وبديكير سبا ملكي",
                "price": 160, "duration": "60 min", "category_en": "Nails & Spa", "category_ar": "الأظافر والسبا",
                "desc_en": "Precision cuticle artistry, BIAB/gel reinforcement, rose-petal soak, and warm paraffin foot therapy.",
                "desc_ar": "عناية دقيقة بالأظافر مع طلاء جل روسي وحمام بتلات الورد والبارافين الدافئ.",
                "image": "manicure.jpg", "badge_en": "Couture Nails", "badge_ar": "عناية متكاملة"
            },
            {
                "id": "svc-4", "name_en": "Moroccan Hammam & Rose Oil Body Spa", "name_ar": "حمام مغربي ملكي وسبا بزيت الورد",
                "price": 280, "duration": "75 min", "category_en": "Nails & Spa", "category_ar": "الأظافر والسبا",
                "desc_en": "Private marble steam sanctuary, organic argan & black soap exfoliation, and relaxing aromatherapy massage.",
                "desc_ar": "جناح بخار رخامي خاص مع الصابون المغربي البلدي وزيت الأركان وتدليك عطري مريح.",
                "image": "bath.jpg", "badge_en": "Private Sanctuary", "badge_ar": "جناح خاص"
            },
            {
                "id": "svc-5", "name_en": "VIP Bridal & Red-Carpet Beauty Suite", "name_ar": "باقة العروس وكبار الشخصيات VIP",
                "price": 450, "duration": "120 min", "category_en": "VIP Packages", "category_ar": "باقات VIP",
                "desc_en": "Complete hair couture, luminous skin prep, luxury manicure/pedicure, lash styling, and private suite refreshments.",
                "desc_ar": "باقة متكاملة تشمل تصفيف الشعر، نضارة البشرة، العناية بالأظافر والرموش في جناح خاص.",
                "image": "lounge.jpg", "badge_en": "Complete VIP Suite", "badge_ar": "الباقة الملكية"
            }
        ],
        "amenity_1": {"en": "Herbal Tea & Matcha Bar", "ar": "ركن الضيافة والشاي العضوي", "sub_en": "Complimentary artisan refreshments", "sub_ar": "مشروبات ترحيبية فاخرة ومجانية", "icon": "fa-mug-saucer"},
        "amenity_2": {"en": "Medical-Grade Sterilization", "ar": "تعقيم طبي فائق", "sub_en": "Autoclave-sealed manicure & facial tools", "sub_ar": "أدوات معقمة ومغلفة لكل سيدة", "icon": "fa-shield-halved"}
    }
}

def detect_niche(category: str, name: str) -> str:
    combined = f"{category} {name}".lower()
    if any(w in combined for w in ["barber", "gents", "men", "grooming", "hassan", "turkish"]):
        return "gents_barber"
    if any(w in combined for w in ["ladies", "beauty", "nail", "women", "hair", "salon", "makeup", "lash"]):
        return "ladies_beauty"
    if any(w in combined for w in ["spa", "massage", "wellness", "relaxation"]):
        return "massage_spa"
    if any(w in combined for w in ["restaurant", "cafe", "dining", "seafood", "grill"]):
        return "restaurant"
    return "gents_barber"

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def clean_phone_number(phone: str) -> str:
    digits = re.sub(r'\D', '', phone)
    if digits.startswith("00971"):
        return digits[2:]
    if digits.startswith("05"):
        return "971" + digits[1:]
    if digits.startswith("5") and len(digits) == 9:
        return "971" + digits
    return digits

def extract_coords_from_maps(url: str):
    if not url:
        return "25.2048,55.2708"
    m = re.search(r'!3d([0-9.]+)!4d([0-9.]+)', url)
    if m:
        return f"{m.group(1)},{m.group(2)}"
    m2 = re.search(r'@([0-9.]+),([0-9.]+)', url)
    if m2:
        return f"{m2.group(1)},{m2.group(2)}"
    return "25.2048,55.2708"

def build_prototype_for_prospect(lead_id: str = None) -> dict:
    conn = sqlite3.connect(CRM_DB)
    cur = conn.cursor()
    
    if lead_id:
        cur.execute("SELECT id, name, category, phone, rating, reviews_count, address, maps_url FROM harvey_prospects WHERE id = ?", (lead_id,))
    else:
        cur.execute("""
            SELECT id, name, category, phone, rating, reviews_count, address, maps_url
            FROM harvey_prospects
            WHERE gatekeeper_status = 'VIRGIN_QUEUE'
            ORDER BY harvey_score DESC
            LIMIT 1
        """)
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError("No prospect available to build!")
    
    p_id, p_name, p_cat, p_phone, p_rating, p_reviews, p_address, p_maps_url = row
    slug = slugify(p_name)
    niche_key = detect_niche(p_cat, p_name)
    if niche_key not in NICHE_CONFIGS:
        niche_key = "gents_barber"
    cfg = NICHE_CONFIGS[niche_key]
    
    clean_phone = clean_phone_number(p_phone)
    coords = extract_coords_from_maps(p_maps_url)
    target_dir = os.path.join(DOCS_DIR, slug)
    os.makedirs(target_dir, exist_ok=True)
    
    print(f"[*] Building prototype for: {p_name} ({p_id})")
    print(f"    Niche: {niche_key} | Slug: {slug}")
    print(f"    Phone: {p_phone} -> WA: {clean_phone}")
    print(f"    Social Proof: {p_rating}★ ({p_reviews} reviews)")
    print(f"    Location: {p_address} (Coords: {coords})")
    
    # 1. Copy Assets from _niche_assets
    src_assets = os.path.join(ASSETS_DIR, niche_key)
    if not os.path.exists(src_assets):
        src_assets = os.path.join(ASSETS_DIR, "gents_barber")
    
    for f in os.listdir(src_assets):
        src_f = os.path.join(src_assets, f)
        if os.path.isfile(src_f):
            shutil.copy2(src_f, os.path.join(target_dir, f))
    
    # Ensure manicure.jpg exists for ladies_beauty
    if niche_key == "ladies_beauty":
        if not os.path.exists(os.path.join(target_dir, "manicure.jpg")):
            if os.path.exists(os.path.join(target_dir, "beard.jpg")):
                shutil.copy2(os.path.join(target_dir, "beard.jpg"), os.path.join(target_dir, "manicure.jpg"))
            else:
                shutil.copy2(os.path.join(target_dir, "facial.jpg"), os.path.join(target_dir, "manicure.jpg"))
    
    # Ensure spy-tracker.js is present
    spy_src = os.path.join(DOCS_DIR, "maison-haniel", "spy-tracker.js")
    if os.path.exists(spy_src):
        shutil.copy2(spy_src, os.path.join(target_dir, "spy-tracker.js"))
    
    # 2. Generate index.html from Master Proven Template
    # We use maison-haniel as the gold standard baseline
    template_path = os.path.join(DOCS_DIR, "maison-haniel", "index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    # Substitutions
    # Brand name and titles
    html = re.sub(r'<title>.*?</title>', f'<title>{p_name} | {cfg["title_en"]}</title>', html)
    html = re.sub(r'data-i18n="preview_salon">.*?<', f'data-i18n="preview_salon">{p_name} ({p_address})<', html)
    html = re.sub(r'data-i18n="brand_name">.*?<', f'data-i18n="brand_name">{p_name.upper()}<', html)
    html = re.sub(r'data-i18n="brand_sub">.*?<', f'data-i18n="brand_sub">{cfg["badge_en"]}<', html)
    
    # WhatsApp links
    html = re.sub(r'href="https://wa\.me/\d+"', f'href="https://wa.me/{clean_phone}"', html)
    
    # Google Maps URLs
    if p_maps_url:
        html = re.sub(r'href="https://www\.google\.com/maps/place/[^"]+"', f'href="{p_maps_url}"', html)
    html = re.sub(r'src="https://maps\.google\.com/maps\?q=[^"]+"', f'src="https://maps.google.com/maps?q={coords}&t=&z=16&ie=UTF8&iwloc=&output=embed"', html)
    
    # Ratings & Reviews in Markup
    html = re.sub(r'<strong class="display text-lg text-white">\d+\.\d+</strong>', f'<strong class="display text-lg text-white">{p_rating}</strong>', html)
    html = re.sub(r'data-i18n="hero_reviews_badge">• \d+ Google Maps Reviews<', f'data-i18n="hero_reviews_badge">• {p_reviews} Google Maps Reviews<', html)
    html = re.sub(r'data-count="\d+\.\d+" data-dec="1">\d+\.\d+<', f'data-count="{p_rating}" data-dec="1">{p_rating}<', html)
    html = re.sub(r'data-count="\d+">\d+<', f'data-count="{p_reviews}">{p_reviews}<', html)
    html = re.sub(r'data-i18n="nav_reviews">Reviews \(\d+\.\d+★\)<', f'data-i18n="nav_reviews">Reviews ({p_rating}★)<', html)
    
    # Storage Keys to prevent cross-contamination
    html = html.replace('maison_haniel_theme_v2', f'{slug.replace("-", "_")}_theme_v2')
    html = html.replace('maison_haniel_lang', f'{slug.replace("-", "_")}_lang')
    html = html.replace('maison_haniel_services_v3', f'{slug.replace("-", "_")}_services_v3')
    html = html.replace('maison_haniel_orders', f'{slug.replace("-", "_")}_orders')
    
    # Spy site config
    html = re.sub(r'window\.SPY_SITE_ID\s*=\s*"[^"]+";', f'window.SPY_SITE_ID = "jota-preview-{slug}";', html)
    html = re.sub(r'window\.SPY_SITE_NAME\s*=\s*"[^"]+";', f'window.SPY_SITE_NAME = "Jota Beta Preview: {p_name}";', html)
    
    # Inject Tailored Services & Categories JSON into JavaScript
    services_js = json.dumps(cfg["services"], ensure_ascii=False, indent=6)
    cats_en_js = json.dumps(cfg["categories_en"], ensure_ascii=False)
    cats_ar_js = json.dumps(cfg["categories_ar"], ensure_ascii=False)
    
    # Replace services block in script
    services_pattern = r'const DEFAULT_SERVICES = \[.*?\];'
    replacement_services = f"const DEFAULT_SERVICES = {services_js};"
    html = re.sub(services_pattern, replacement_services, html, flags=re.DOTALL)
    
    # Replace default categories
    cats_pattern = r'const DEFAULT_CATEGORIES_EN = \[.*?\];\s*const DEFAULT_CATEGORIES_AR = \[.*?\];'
    replacement_cats = f"const DEFAULT_CATEGORIES_EN = {cats_en_js};\n    const DEFAULT_CATEGORIES_AR = {cats_ar_js};"
    html = re.sub(cats_pattern, replacement_cats, html, flags=re.DOTALL)
    
    # Monogram logo in header
    first_letter = p_name[0].upper() if p_name else "P"
    html = re.sub(
        r'<span class="w-10 h-10 rounded-full flex items-center justify-center display text-xl font-[^"]*" style="background:[^;]+;color:[^"]+">[A-Z]</span>',
        f'<span class="w-10 h-10 rounded-full flex items-center justify-center display text-xl font-bold" style="background:var(--brass-fill);color:#14201B">{first_letter}</span>',
        html
    )

    # Floating badge on hero (beard.jpg for barber, manicure.jpg for ladies)
    hero_badge_img = "beard.jpg" if niche_key == "gents_barber" else "manicure.jpg"
    hero_badge_alt = "Precision Beard Sculpting" if niche_key == "gents_barber" else "Russian Couture Nails"
    html = re.sub(
        r'<img src="(?:manicure|beard)\.jpg"[^>]*class="rounded-xl aspect-\[4/5\][^"]*"[^>]*>',
        f'<img src="{hero_badge_img}" alt="{hero_badge_alt}" class="rounded-xl aspect-[4/5] object-cover w-full" loading="lazy">',
        html
    )

    # Hero headline & description
    html = re.sub(r'data-i18n="hero_title">[\s\S]*?</h1>', f'data-i18n="hero_title">{cfg["hero_title_en"]}</h1>', html)
    html = re.sub(r'data-i18n="hero_desc">[\s\S]*?</p>', f'data-i18n="hero_desc">{p_address}. {cfg["hero_desc_en"]}</p>', html)

    # Replace script 6 bespoke override completely with niche data
    override_script = f"""
    <script>
      /* {p_name.upper()} BESPOKE OVERRIDE */
      try {{
        localStorage.removeItem('{slug.replace("-", "_")}_services');
        localStorage.removeItem('{slug.replace("-", "_")}_services_v2');
        localStorage.removeItem('{slug.replace("-", "_")}_services_v3');
      }} catch(e) {{}}

      DEFAULT_SERVICES.splice(0, DEFAULT_SERVICES.length,
{json.dumps(cfg["services"], ensure_ascii=False, indent=8).strip("[]")}
      );
      DEFAULT_CATEGORIES_EN.splice(0, DEFAULT_CATEGORIES_EN.length, {", ".join(json.dumps(c) for c in cfg["categories_en"])});
      DEFAULT_CATEGORIES_AR.splice(0, DEFAULT_CATEGORIES_AR.length, {", ".join(json.dumps(c) for c in cfg["categories_ar"])});
      services = DEFAULT_SERVICES;

      Object.assign(translations.en, {{
        brand_name: "{p_name.upper()}",
        brand_sub: "{cfg["badge_en"]}",
        hero_eyebrow: "{p_address.split("-")[-1].strip() if "-" in p_address else "Dubai"}",
        hero_title: '{cfg["hero_title_en"]}',
        hero_desc: "Located at {p_address}. {cfg["hero_desc_en"]}",
        mq_1: "{cfg["services"][0]["name_en"]}", mq_2: "{cfg["services"][1]["name_en"]}", mq_3: "{cfg["services"][2]["name_en"]}", mq_4: "{cfg["services"][3]["name_en"]}", mq_5: "{cfg["services"][4]["name_en"]}",
        sec_menu_title: "Signature services",
        sec_menu_sub: "Every treatment is delivered with premium imported cosmetics and master craftsmanship.",
        exp_badge: "The Experience",
        exp_title: "More than a haircut.",
        atmosphere_badge: "Private Atmosphere",
        atmosphere_title: "An oasis of bespoke comfort in Dubai",
        atmosphere_desc: "Modern luxury chairs, ambient illumination and master care focused entirely on your satisfaction.",
        amenity_coffee_title: "{cfg["amenity_1"]["en"]}",
        amenity_coffee_sub: "{cfg["amenity_1"]["sub_en"]}",
        amenity_hygiene_title: "{cfg["amenity_2"]["en"]}",
        amenity_hygiene_sub: "{cfg["amenity_2"]["sub_en"]}",
        reviews_badge: "Verified Client Reviews",
        reviews_title: "Loved across Dubai with {p_reviews} verified reviews.",
        reviews_note: "Every rating comes from real guests on Google Maps.",
        loc_title: "Hours & location",
        cta_title: "Your chair is waiting.",
        cta_sub: "Walk in or reserve your slot via WhatsApp in seconds.",
        footer_tag: "Bespoke {cfg["badge_en"]} at {p_address}.",
        loc_address_title: "{p_name}",
        loc_address_sub: "{p_address}"
      }});

      Object.assign(translations.ar, {{
        brand_name: "{p_name}",
        brand_sub: "{cfg["badge_ar"]}",
        hero_eyebrow: "دبي · الإمارات",
        hero_title: '{cfg["hero_title_ar"]}',
        hero_desc: "يقع في {p_address}. {cfg["hero_desc_ar"]}",
        mq_1: "{cfg["services"][0]["name_ar"]}", mq_2: "{cfg["services"][1]["name_ar"]}", mq_3: "{cfg["services"][2]["name_ar"]}", mq_4: "{cfg["services"][3]["name_ar"]}", mq_5: "{cfg["services"][4]["name_ar"]}",
        sec_menu_title: "قائمة الخدمات الحصرية",
        sec_menu_sub: "تُقدم كل جلسة عناية باستخدام أرقى المستحضرات العالمية وبأعلى درجات الاحترافية.",
        exp_badge: "التجربة الفاخرة",
        exp_title: "أكثر من مجرد زيارة عادية.",
        atmosphere_badge: "أجواء راقية",
        atmosphere_title: "واحة من الراحة والتميز في دبي",
        atmosphere_desc: "أجواء مريحة، إضاءة مدروسة وخبراء مكرسون لراحتك وأناقتك.",
        amenity_coffee_title: "{cfg["amenity_1"]["ar"]}",
        amenity_coffee_sub: "{cfg["amenity_1"]["sub_ar"]}",
        amenity_hygiene_title: "{cfg["amenity_2"]["ar"]}",
        amenity_hygiene_sub: "{cfg["amenity_2"]["sub_ar"]}",
        reviews_badge: "آراء العملاء المعتمدة",
        reviews_title: "ثقة أهل دبي مع {p_reviews} تقييم حقيقي على جوجل.",
        reviews_note: "كل تقييم من ضيوف حقيقيين على خرائط جوجل.",
        loc_title: "الموقع وساعات العمل",
        cta_title: "مكانك بانتظارك.",
        cta_sub: "تفضل بزيارتنا أو احجز موعدك عبر واتساب في ثوانٍ.",
        footer_tag: "خدمات راقية في {p_address}.",
        loc_address_title: "{p_name}",
        loc_address_sub: "{p_address}"
      }});

      applyLanguage(currentLang);
    </script>
"""
    override_pattern = r'<script>\s*/\* (?:HARVEY|PAPARAZZI)[\s\S]*?</script>'
    html = re.sub(override_pattern, lambda m: override_script.strip(), html)

    # Write customized index.html
    target_index = os.path.join(target_dir, "index.html")
    with open(target_index, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"[+] index.html generated successfully at: {target_index}")
    
    # 3. Register in Supabase web_spy_sites
    preview_url = f"https://cubaloop.github.io/notrack-ecosystem/preview/{slug}/"
    spy_payload = {
        "site_id": f"jota-preview-{slug}",
        "site_name": f"Jota Beta Preview: {p_name}",
        "site_url": preview_url,
        "category": "jota_preview",
        "description": f"Bespoke luxury prototype for {p_name} in Dubai ({p_rating}★, {p_reviews} reviews). Mobile Admin Dashboard + WhatsApp Booking."
    }
    
    spy_req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/web_spy_sites",
        data=json.dumps(spy_payload).encode('utf-8'),
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(spy_req) as resp:
            print(f"[+] Supabase web_spy_sites registered: HTTP {resp.status}")
    except Exception as e:
        print(f"[!] Supabase note: {e}")
    
    # 4. Update SQLite CRM
    now = datetime.now().isoformat()
    cur.execute("""
        UPDATE harvey_prospects
        SET prototype_slug = ?,
            prototype_url = ?,
            gatekeeper_status = 'PROTOTYPE_PENDING_DAVID',
            david_notified_at = ?
        WHERE id = ?
    """, (slug, preview_url, now, p_id))
    conn.commit()
    conn.close()
    print(f"[+] SQLite CRM updated: {p_id} -> PROTOTYPE_PENDING_DAVID")
    
    # 5. Git Commit & Push
    print("[*] Deploying to GitHub Pages...")
    try:
        subprocess.run(["git", "add", f"docs/preview/{slug}"], cwd=ROOT_DIR, check=True)
        subprocess.run(["git", "commit", "-m", f"feat({slug}): deploy bespoke luxury prototype for {p_name}"], cwd=ROOT_DIR, check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=ROOT_DIR, check=True)
        print("[+] GitHub Pages deploy pushed successfully!")
    except Exception as e:
        print(f"[!] Git push warning: {e}")
    
    # 6. Send Gatekeeper Notification to David's WhatsApp
    live_url_full = f"{preview_url}?theme=light&lang=en"
    wa_message = f"""🏛️ *Kael Gatekeeper — Nuevo Prototipo Creado*

David, he generado el prototipo de lujo para el siguiente candidato de máxima puntuación:

📌 *Cliente:* {p_name}
⭐ *Reputación Google Maps:* {p_rating}★ ({p_reviews} reseñas reales)
📍 *Ubicación:* {p_address}
🏷️ *Nicho:* {cfg["badge_en"]}

🔗 *Enlace en Vivo (Light-First Mobile):*
{live_url_full}

📍 *Ficha de Google Maps:*
{p_maps_url}

🛠️ *Características Activas:*
• Vídeo de fondo en bucle HD representativo del nicho.
• Cabecera ultra-ligera (marca + WhatsApp + ☰).
• Panel Admin Móvil con compresor de fotos Canvas integrado.
• Telemetría pasiva Spy Tracker v2 registrada en Supabase.
• Oferta configurada: 1,000 AED + 500 AED/año de soporte.

Por favor pruébalo en tu móvil. Quedo atento a tu aprobación explícita (*"apruebo"*) para contactar al negocio."""

    wa_payload = {
        "phone": DAVID_PHONE,
        "message": wa_message
    }
    
    wa_req = urllib.request.Request(
        WA_GATEWAY_URL,
        data=json.dumps(wa_payload).encode('utf-8'),
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    try:
        with urllib.request.urlopen(wa_req) as resp:
            wa_res = resp.read().decode('utf-8')
            print(f"[+] Gatekeeper WhatsApp sent to David: {wa_res}")
    except Exception as e:
        print(f"[!] WhatsApp send warning: {e}")
        
    return {
        "id": p_id,
        "name": p_name,
        "slug": slug,
        "niche": niche_key,
        "url": live_url_full,
        "maps_url": p_maps_url
    }

if __name__ == "__main__":
    lead = sys.argv[1] if len(sys.argv) > 1 else None
    res = build_prototype_for_prospect(lead)
    print("\n✅ Factory Build Completed:")
    print(json.dumps(res, indent=2))
