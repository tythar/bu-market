import os
import sys
import django
from io import BytesIO
from decimal import Decimal
from PIL import Image, ImageDraw, ImageFont

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bu_market.settings')
django.setup()

from django.utils import timezone
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from accounts.models import User
from subscriptions.models import SubscriptionPlan, SellerSubscription
from marketplace.models import Category, Listing, Hostel, HostelImage


def create_card_image(title, category_name, price_str, condition, location, subtitle, bg_color, accent_color=(255, 193, 7)):
    """
    Creates a visually stunning, high-res 800x600 product/hostel image card using PIL.
    """
    width, height = 800, 600
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Decorative top and bottom bars
    draw.rectangle([(0, 0), (width, 8)], fill=accent_color)
    draw.rectangle([(0, height - 8), (width, height)], fill=accent_color)

    # Subtle inner decorative frame
    draw.rectangle([(16, 16), (width - 16, height - 16)], outline=(255, 255, 255, 30), width=1)

    # Try to load a clean font or use default
    font_large = None
    font_medium = None
    font_small = None
    font_title = None

    try:
        # Check standard Windows fonts
        font_title = ImageFont.truetype("arialbd.ttf", 38)
        font_large = ImageFont.truetype("arialbd.ttf", 32)
        font_medium = ImageFont.truetype("arial.ttf", 22)
        font_small = ImageFont.truetype("arial.ttf", 18)
    except Exception:
        font_title = ImageFont.load_default()
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Top Brand / Header
    header_text = "BU-MARKET  •  BUGEMA UNIVERSITY COMMUNITY MARKETPLACE"
    draw.text((40, 36), header_text, fill=(200, 215, 240), font=font_small)

    # Badges row: Category pill + Condition pill
    cat_badge_text = f"  {category_name.upper()}  "
    draw.rounded_rectangle([(40, 75), (40 + len(cat_badge_text) * 11, 110)], radius=6, fill=(255, 255, 255), outline=None)
    draw.text((48, 82), cat_badge_text.strip(), fill=(14, 25, 49), font=font_small)

    if condition:
        cond_badge_text = f"  {condition.upper()}  "
        start_x = 55 + len(cat_badge_text) * 11
        cond_bg = accent_color if condition == 'NEW' else (240, 240, 240)
        cond_fg = (14, 25, 49)
        draw.rounded_rectangle([(start_x, 75), (start_x + len(cond_badge_text) * 11, 110)], radius=6, fill=cond_bg)
        draw.text((start_x + 8, 82), cond_badge_text.strip(), fill=cond_fg, font=font_small)

    # Main Product / Hostel Title (wrap if long)
    title_y = 150
    words = title.split()
    line1 = ""
    line2 = ""
    for w in words:
        if len(line1 + " " + w) < 32:
            line1 = (line1 + " " + w).strip()
        else:
            line2 = (line2 + " " + w).strip()

    draw.text((40, title_y), line1, fill=(255, 255, 255), font=font_title)
    if line2:
        draw.text((40, title_y + 48), line2, fill=(255, 255, 255), font=font_title)
        title_y += 48

    # Subtitle / Feature details
    if subtitle:
        draw.text((40, title_y + 60), subtitle, fill=(185, 205, 230), font=font_medium)

    # Location pill
    loc_y = title_y + 115
    loc_text = f"LOCATION: {location}"
    draw.text((40, loc_y), loc_text, fill=(255, 220, 100), font=font_medium)

    # Big Price Box at bottom
    price_box_top = height - 140
    draw.rounded_rectangle([(40, price_box_top), (width - 40, height - 40)], radius=12, fill=(14, 25, 49), outline=accent_color, width=2)
    draw.text((60, price_box_top + 28), price_str, fill=accent_color, font=font_large)
    draw.text((width - 240, price_box_top + 34), "VERIFIED LISTING", fill=(255, 255, 255), font=font_medium)

    buf = BytesIO()
    img.save(buf, format='JPEG', quality=88)
    return ContentFile(buf.getvalue())


def run_seed():
    print("=== Starting BU-MARKET Comprehensive Database Seeding ===")

    # 1. Ensure Subscription Plans exist with high listing limits
    gold_plan, _ = SubscriptionPlan.objects.get_or_create(
        name='GOLD',
        defaults={
            'monthly_fee': Decimal('50000.00'),
            'duration_days': 365,
            'max_active_listings': 50,
            'badge': 'GOLD',
            'has_promoted_ads': True,
        }
    )
    gold_plan.max_active_listings = 50
    gold_plan.has_promoted_ads = True
    gold_plan.save()

    silver_plan, _ = SubscriptionPlan.objects.get_or_create(
        name='SILVER',
        defaults={
            'monthly_fee': Decimal('30000.00'),
            'duration_days': 365,
            'max_active_listings': 25,
            'badge': 'SILVER',
            'has_promoted_ads': True,
        }
    )
    silver_plan.max_active_listings = 25
    silver_plan.has_promoted_ads = True
    silver_plan.save()

    # 2. Setup Categories
    categories_data = [
        {'name': 'Phones', 'slug': 'phones', 'icon': 'bi-phone'},
        {'name': 'Electronics', 'slug': 'electronics', 'icon': 'bi-tv'},
        {'name': 'Furniture', 'slug': 'furniture', 'icon': 'bi-lamp'},
        {'name': 'Hostel Items', 'slug': 'hostel-items', 'icon': 'bi-house-heart'},
        {'name': 'Kitchen', 'slug': 'kitchen', 'icon': 'bi-cup-hot'},
        {'name': 'Books', 'slug': 'books', 'icon': 'bi-book'},
        {'name': 'Groceries & Produce', 'slug': 'groceries', 'icon': 'bi-basket2-fill'},
        {'name': 'Clothing', 'slug': 'clothing', 'icon': 'bi-tag'},
        {'name': 'Services', 'slug': 'services', 'icon': 'bi-gear'},
        {'name': 'Others', 'slug': 'others', 'icon': 'bi-box-seam'},
    ]

    cat_map = {}
    for cdata in categories_data:
        cat, _ = Category.objects.get_or_create(
            slug=cdata['slug'],
            defaults={'name': cdata['name'], 'icon': cdata['icon'], 'is_active': True}
        )
        cat_map[cdata['slug']] = cat
        print(f"Category checked: {cat.name}")

    admin_user = User.objects.filter(is_superuser=True).first() or User.objects.first()

    # 3. Create Sellers
    sellers_info = [
        {
            'username': 'brian_kato',
            'first_name': 'Brian',
            'last_name': 'Kato',
            'email': 'brian.kato@student.bugema.ac.ug',
            'phone_number': '+256772112233',
            'whatsapp_number': '+256772112233',
            'location': 'Bugema University Main Campus',
            'bio': 'Graduating BBA Student selling room belongings before departure.',
        },
        {
            'username': 'sarah_nam',
            'first_name': 'Sarah',
            'last_name': 'Namubiru',
            'email': 'sarah.namubiru@gmail.com',
            'phone_number': '+256701445566',
            'whatsapp_number': '+256701445566',
            'location': 'Small Gate',
            'bio': 'Campus Nursing Student & Entrepreneur selling new & gently used home appliances.',
        },
        {
            'username': 'denis_tech',
            'first_name': 'Denis',
            'last_name': 'Mugisha',
            'email': 'denis.tech@outlook.com',
            'phone_number': '+256782334455',
            'whatsapp_number': '+256782334455',
            'location': 'Kiziri',
            'bio': 'IT Student dealing in laptops, repairs, power supplies & accessories.',
        },
        {
            'username': 'mama_chwa',
            'first_name': 'Mama',
            'last_name': 'Chwa',
            'email': 'mamachwa.shop@gmail.com',
            'phone_number': '+256773556677',
            'whatsapp_number': '+256773556677',
            'location': 'Small Gate',
            'bio': 'Well-known local campus shop selling fresh eggs, mattresses, buckets & drinks.',
        },
        {
            'username': 'hajjat_fresh',
            'first_name': 'Hajjat',
            'last_name': 'Amina',
            'email': 'hajjat.freshproduce@gmail.com',
            'phone_number': '+256704667788',
            'whatsapp_number': '+256704667788',
            'location': 'Kiwenda',
            'bio': 'Town fresh produce stall: Irish potatoes, tomatoes, onions & fruits.',
        },
        {
            'username': 'busiika_store',
            'first_name': 'Busiika',
            'last_name': 'Hardware',
            'email': 'busiika.traders@yahoo.com',
            'phone_number': '+256785778899',
            'whatsapp_number': '+256785778899',
            'location': 'Busiika',
            'bio': 'General hardware, gas cylinders, padlocks, tools & mosquito nets in Busiika.',
        },
        {
            'username': 'gayaza_digital',
            'first_name': 'Gayaza',
            'last_name': 'Electronics',
            'email': 'gayaza.digital@gmail.com',
            'phone_number': '+256756889900',
            'whatsapp_number': '+256756889900',
            'location': 'Gayaza',
            'bio': 'Gayaza Town showroom: Smart TVs, Woofers, Home Theaters, New Phones & Audio.',
        },
        {
            'username': 'sl_hostels',
            'first_name': 'SL Hostels',
            'last_name': 'Management',
            'email': 'sl.hostels.bugema@gmail.com',
            'phone_number': '+256772990011',
            'whatsapp_number': '+256772990011',
            'location': 'Small Gate',
            'bio': 'Official SL Student Hostels: Clean, secure & budget-friendly rooms.',
        },
        {
            'username': 'rose_hostel',
            'first_name': 'Rose',
            'last_name': 'Hostels',
            'email': 'rose.executive.hostels@gmail.com',
            'phone_number': '+256701882233',
            'whatsapp_number': '+256701882233',
            'location': 'Kiziri',
            'bio': 'Rose Executive Hostels: Self-contained student rooms with private toilet, shower & kitchen.',
        },
        {
            'username': 'kyaggwe_rentals',
            'first_name': 'Kyaggwe',
            'last_name': 'Residence',
            'email': 'kyaggwe.rentals@gmail.com',
            'phone_number': '+256784551122',
            'whatsapp_number': '+256784551122',
            'location': 'Kiwenda',
            'bio': 'Kyaggwe Student Apartments: Spacious, serene compound along Kiwenda road.',
        },
    ]

    seller_user_map = {}
    default_password = "Password123!"

    for sdata in sellers_info:
        user, created = User.objects.get_or_create(
            username=sdata['username'],
            defaults={
                'email': sdata['email'],
                'first_name': sdata['first_name'],
                'last_name': sdata['last_name'],
                'role': User.Role.SELLER,
                'phone_number': sdata['phone_number'],
                'whatsapp_number': sdata['whatsapp_number'],
            }
        )
        user.set_password(default_password)
        user.role = User.Role.SELLER
        user.phone_number = sdata['phone_number']
        user.whatsapp_number = sdata['whatsapp_number']
        user.save()
        seller_user_map[sdata['username']] = user

        # Ensure approved GOLD subscription
        sub, _ = SellerSubscription.objects.get_or_create(
            seller=user,
            defaults={
                'plan': gold_plan,
                'amount_paid': gold_plan.monthly_fee,
                'payment_reference': f"SEED-PAY-{user.username}",
                'status': SellerSubscription.Status.APPROVED,
                'approved_by': admin_user,
                'approved_at': timezone.now(),
                'expires_at': timezone.now() + timezone.timedelta(days=365),
            }
        )
        sub.status = SellerSubscription.Status.APPROVED
        sub.expires_at = timezone.now() + timezone.timedelta(days=365)
        sub.save()
        print(f"Seller configured: {user.username} with GOLD subscription")

    # 4. Create Diverse Products & Listings
    listings_data = [
        # --- BRIAN KATO (Graduating Student - Bugema Main Campus) ---
        {
            'seller': 'brian_kato',
            'category': 'furniture',
            'title': 'High Density 4x6 Mattress with Washable Cover',
            'price': Decimal('120000.00'),
            'condition': Listing.Condition.USED,
            'location': 'Bugema University Main Campus',
            'description': 'Used for 2 semesters only. Still very firm and clean. Comes with a complimentary zipped blue washable cover. Reason for sale: Graduating this semester.',
            'subtitle': '4x6 High Density • Clean & Firm • Zipped Cover',
            'bg_color': (43, 45, 66),
            'is_promoted': False,
        },
        {
            'seller': 'brian_kato',
            'category': 'kitchen',
            'title': 'Total 6kg Gas Cylinder with Burner & Regulator',
            'price': Decimal('110000.00'),
            'condition': Listing.Condition.USED,
            'location': 'Bugema University Main Campus',
            'description': 'Original Total 6kg gas cylinder with heavy duty single burner top and pressure regulator. Works perfectly, zero leaks. Ideal for hostel cooking.',
            'subtitle': '6kg Gas Cylinder • Includes Heavy Duty Burner',
            'bg_color': (29, 53, 87),
            'is_promoted': False,
        },
        {
            'seller': 'brian_kato',
            'category': 'furniture',
            'title': 'Wooden Student Study Desk & Ergonomic Chair',
            'price': Decimal('85000.00'),
            'condition': Listing.Condition.USED,
            'location': 'Bugema University Main Campus',
            'description': 'Sturdy varnished mahogany student desk with a side shelf for textbooks, plus a comfortable study chair. Pick up near Campus Halls.',
            'subtitle': 'Varnished Mahogany Desk + Padded Chair',
            'bg_color': (58, 48, 66),
            'is_promoted': False,
        },

        # --- SARAH NAMUBIRU (Small Gate Entrepreneur) ---
        {
            'seller': 'sarah_nam',
            'category': 'kitchen',
            'title': 'Stainless Steel Electric Kettle 2.0L (Auto-Cut)',
            'price': Decimal('35000.00'),
            'condition': Listing.Condition.NEW,
            'location': 'Small Gate',
            'description': 'Brand new in box! Fast boiling stainless steel 2-litre kettle with automatic shut-off safety protection. Available for pickup at Small Gate.',
            'subtitle': 'Brand New in Box • 2L Fast Boil • Auto-Cut Safety',
            'bg_color': (20, 40, 70),
            'is_promoted': True,
        },
        {
            'seller': 'sarah_nam',
            'category': 'kitchen',
            'title': 'Double Burner Tabletop Gas Cooker',
            'price': Decimal('90000.00'),
            'condition': Listing.Condition.USED,
            'location': 'Small Gate',
            'description': 'Stainless steel double burner stove with smooth brass gas taps. Clean and well maintained, heats fast.',
            'subtitle': 'Double Burner Stove • Stainless Steel Top',
            'bg_color': (30, 60, 90),
            'is_promoted': False,
        },
        {
            'seller': 'sarah_nam',
            'category': 'electronics',
            'title': 'Rechargeable Table Fan with LED Nightlight',
            'price': Decimal('45000.00'),
            'condition': Listing.Condition.NEW,
            'location': 'Small Gate',
            'description': '3-speed portable desk fan with built-in emergency LED lamp. Keeps running up to 6 hours during power outages.',
            'subtitle': 'Rechargeable Battery • 3 Speeds • Emergency LED',
            'bg_color': (24, 76, 120),
            'is_promoted': False,
        },

        # --- DENIS MUGISHA (Tech Student - Kiziri) ---
        {
            'seller': 'denis_tech',
            'category': 'electronics',
            'title': 'HP EliteBook 840 G5 Core i5 (16GB RAM, 256GB SSD)',
            'price': Decimal('850000.00'),
            'condition': Listing.Condition.USED,
            'location': 'Kiziri',
            'description': 'Slim aluminum business laptop. 8th Gen Intel Core i5, 16GB DDR4 RAM, 256GB NVMe SSD, backlit keyboard, 4-hour battery health. Windows 11 Pro & Office activated.',
            'subtitle': 'Intel Core i5 • 16GB RAM • 256GB SSD • Backlit Keys',
            'bg_color': (14, 25, 49),
            'is_promoted': True,
        },
        {
            'seller': 'denis_tech',
            'category': 'electronics',
            'title': 'Casio fx-991EX ClassWiz Scientific Calculator',
            'price': Decimal('65000.00'),
            'condition': Listing.Condition.NEW,
            'location': 'Kiziri',
            'description': 'Original Casio ClassWiz 991EX high-resolution calculator with QR code verification. Essential for Engineering, Business & Science courses.',
            'subtitle': 'Genuine Casio 991EX • High-Resolution Natural Display',
            'bg_color': (20, 35, 60),
            'is_promoted': False,
        },

        # --- MAMA CHWA GENERAL MERCHANDISE (Small Gate Shop) ---
        {
            'seller': 'mama_chwa',
            'category': 'groceries',
            'title': 'Fresh Farm Eggs (Full Tray of 30 Large Eggs)',
            'price': Decimal('13000.00'),
            'condition': Listing.Condition.NEW,
            'location': 'Small Gate',
            'description': 'Direct from local poultry farm! Clean, fresh, large grade brown eggs. Bulk orders for student hostels and canteens delivered directly to your hostel gate.',
            'subtitle': 'Fresh Daily Poultry • Tray of 30 Grade-A Eggs',
            'bg_color': (180, 100, 20),
            'is_promoted': True,
        },
        {
            'seller': 'mama_chwa',
            'category': 'hostel-items',
            'title': 'Heavy-Duty 20L Plastic Water Bucket with Lid',
            'price': Decimal('12000.00'),
            'condition': Listing.Condition.NEW,
            'location': 'Small Gate',
            'description': 'Thick durable plastic buckets with strong metallic handles and tight sealing lids. Available in dark blue, green, and red.',
            'subtitle': 'Heavy-Duty 20 Litres • Metallic Handle & Lid',
            'bg_color': (15, 80, 100),
            'is_promoted': False,
        },
        {
            'seller': 'mama_chwa',
            'category': 'furniture',
            'title': 'Rose Foam 3x6 Student High Density Mattress',
            'price': Decimal('160000.00'),
            'condition': Listing.Condition.NEW,
            'location': 'Small Gate',
            'description': 'Brand new wrapped Rose Foam 3x6 high-density student mattress with manufacturer warranty. Free delivery across Small Gate and Kiziri hostels.',
            'subtitle': 'Brand New • Rose Foam High Density • 3x6 Size',
            'bg_color': (60, 20, 40),
            'is_promoted': True,
        },
        {
            'seller': 'mama_chwa',
            'category': 'groceries',
            'title': 'Crate of Assorted Sodas & Energy Drinks (24 Bottles)',
            'price': Decimal('24000.00'),
            'condition': Listing.Condition.NEW,
            'location': 'Small Gate',
            'description': 'Cold soda crates and Riham energy drinks for hostel parties, group discussions, and daily chilling. Glass bottles or plastic bottles available.',
            'subtitle': 'Full Crate (24 Pcs) • Coca-Cola, Pepsi & Energy Drinks',
            'bg_color': (140, 30, 30),
            'is_promoted': False,
        },

        # --- HAJJAT FRESH FARM PRODUCE (Kiwenda Market Stall) ---
        {
            'seller': 'hajjat_fresh',
            'category': 'groceries',
            'title': 'Fresh Red Ripe Kampala Tomatoes (Heap / Basin)',
            'price': Decimal('5000.00'),
            'condition': Listing.Condition.NEW,
            'location': 'Kiwenda',
            'description': 'Farm fresh, firm, juicy red tomatoes harvested this morning. Generous heaps starting at 5,000 UGX, or full wooden crates at wholesale discounts.',
            'subtitle': 'Farm Fresh Morning Harvest • Sweet & Juicy',
            'bg_color': (160, 40, 20),
            'is_promoted': True,
        },
        {
            'seller': 'hajjat_fresh',
            'category': 'groceries',
            'title': 'Kabale Irish Potatoes (5kg Fresh Heap)',
            'price': Decimal('15000.00'),
            'condition': Listing.Condition.NEW,
            'location': 'Kiwenda',
            'description': 'Clean, red-skin Irish potatoes direct from Kabale growers. Perfect for student chips, stews, and boiling. Free measure bonus for Bugema students!',
            'subtitle': 'Direct from Kabale • Clean Red-Skin 5kg Heap',
            'bg_color': (100, 70, 20),
            'is_promoted': False,
        },
        {
            'seller': 'hajjat_fresh',
            'category': 'groceries',
            'title': 'Fresh Red Onions & Garlic Kitchen Bundle',
            'price': Decimal('6000.00'),
            'condition': Listing.Condition.NEW,
            'location': 'Kiwenda',
            'description': 'Bundle of firm red onions and aromatic ginger/garlic combo. Keep your hostel meals aromatic and healthy all week.',
            'subtitle': 'Aromatic Red Onions + Garlic/Ginger Combo',
            'bg_color': (80, 40, 90),
            'is_promoted': False,
        },

        # --- BUSIIKA HARDWARE & HOME (Busiika Town) ---
        {
            'seller': 'busiika_store',
            'category': 'kitchen',
            'title': 'Shell 13kg Cooking Gas Cylinder (Full Refill & Hose)',
            'price': Decimal('220000.00'),
            'condition': Listing.Condition.NEW,
            'location': 'Busiika',
            'description': 'Official Shell 13kg gas cylinder with safety relief valve, 2-metre reinforced gas hose, and certified brass clips. Long lasting for serious home & hostel cooking.',
            'subtitle': 'Full 13kg Cylinder • Includes Safety Hose & Clips',
            'bg_color': (200, 140, 0),
            'is_promoted': True,
        },
        {
            'seller': 'busiika_store',
            'category': 'hostel-items',
            'title': 'Treated 4x6 Mosquito Net with Circular Steel Ring',
            'price': Decimal('28000.00'),
            'condition': Listing.Condition.NEW,
            'location': 'Busiika',
            'description': 'Pre-treated long-lasting insecticidal canopy net. Easy single-hook ceiling mount, breathable mesh, fits 3x6 and 4x6 beds comfortably.',
            'subtitle': 'Pre-Treated Mesh • Steel Ring Top • 100% Malaria Safe',
            'bg_color': (20, 100, 80),
            'is_promoted': False,
        },
        {
            'seller': 'busiika_store',
            'category': 'electronics',
            'title': 'Solar Powerbank & Emergency Lighting Kit',
            'price': Decimal('55000.00'),
            'condition': Listing.Condition.NEW,
            'location': 'Busiika',
            'description': 'Includes a 10,000mAh solar charging powerbank, dual USB ports, and 2 wired LED bulbs with hanging switches. Study uninterrupted during blackouts.',
            'subtitle': 'Solar Panel + 10,000mAh Battery + 2 LED Bulbs',
            'bg_color': (30, 80, 40),
            'is_promoted': False,
        },

        # --- GAYAZA DIGITAL HUB & ELECTRONICS (Gayaza Main Road) ---
        {
            'seller': 'gayaza_digital',
            'category': 'electronics',
            'title': 'Hisense 43" Frameless 4K Smart Android TV',
            'price': Decimal('980000.00'),
            'condition': Listing.Condition.NEW,
            'location': 'Gayaza',
            'description': 'Brand new in box with 1-year official Hisense warranty. Ultra HD 4K, built-in Netflix, YouTube, Prime Video, Bluetooth audio, dual HDMI & USB ports.',
            'subtitle': '43-Inch 4K UHD • Android Smart TV • 1-Year Warranty',
            'bg_color': (14, 25, 49),
            'is_promoted': True,
        },
        {
            'seller': 'gayaza_digital',
            'category': 'electronics',
            'title': 'Geepas 2.1 Deep Bass Subwoofer & Home Theater',
            'price': Decimal('240000.00'),
            'condition': Listing.Condition.NEW,
            'location': 'Gayaza',
            'description': 'High-power 2.1 channel speaker system with thunderous bass. Bluetooth 5.0, FM radio, SD card, remote control, and equalizer display. Crystal clear sound for movies & music.',
            'subtitle': '2.1 Channel Subwoofer • High Bass • Bluetooth & Remote',
            'bg_color': (18, 30, 55),
            'is_promoted': True,
        },
        {
            'seller': 'gayaza_digital',
            'category': 'phones',
            'title': 'Samsung Galaxy A15 (128GB, 6GB RAM, Dual SIM)',
            'price': Decimal('540000.00'),
            'condition': Listing.Condition.NEW,
            'location': 'Gayaza',
            'description': 'Brand new sealed Samsung Galaxy A15. 6.5" Super AMOLED 90Hz display, 50MP triple camera, 5000mAh battery with 25W fast charging. Includes original charger & screen protector.',
            'subtitle': 'Super AMOLED 90Hz • 50MP Triple Camera • 5000mAh',
            'bg_color': (10, 20, 40),
            'is_promoted': True,
        },
        {
            'seller': 'gayaza_digital',
            'category': 'electronics',
            'title': 'Oraimo FreePods 4 Noise Cancelling Earbuds',
            'price': Decimal('85000.00'),
            'condition': Listing.Condition.NEW,
            'location': 'Gayaza',
            'description': 'Original Oraimo FreePods 4 with active noise cancellation, transparency mode, 35.5-hour total playtime, and low-latency gaming mode. 100% genuine with scratch code.',
            'subtitle': 'Active Noise Cancellation • 35.5h Playtime • Bass Boost',
            'bg_color': (25, 45, 80),
            'is_promoted': False,
        },
    ]

    for pdata in listings_data:
        seller = seller_user_map[pdata['seller']]
        cat = cat_map[pdata['category']]
        
        # Check if listing exists with this title
        existing = Listing.objects.filter(title=pdata['title']).first()
        if existing:
            print(f"Listing '{pdata['title']}' already exists. Skipping.")
            continue

        price_fmt = f"UGX {pdata['price']:,.2f}"
        cond_label = "Brand New" if pdata['condition'] == Listing.Condition.NEW else "Gently Used"
        image_file = create_card_image(
            title=pdata['title'],
            category_name=cat.name,
            price_str=price_fmt,
            condition=pdata['condition'],
            location=pdata['location'],
            subtitle=pdata['subtitle'],
            bg_color=pdata['bg_color']
        )

        listing = Listing(
            seller=seller,
            category=cat,
            title=pdata['title'],
            description=pdata['description'],
            price=pdata['price'],
            condition=pdata['condition'],
            status=Listing.Status.ACTIVE,
            location=pdata['location'],
            is_promoted=pdata['is_promoted'],
            phone_number=seller.phone_number,
            whatsapp_number=seller.whatsapp_number,
        )
        # Save image directly
        filename = f"{pdata['seller']}_{cat.slug}_{int(timezone.now().timestamp())}.jpg"
        listing.image.save(filename, image_file, save=False)
        listing.save()
        print(f"Created Listing: {listing.title} ({price_fmt}) by {seller.username}")

    # 5. Create Hostels & Multi-angle Images
    hostels_data = [
        {
            'owner': 'sl_hostels',
            'name': 'SL Hostel (Student Residence)',
            'price': Decimal('300000.00'),
            'location': 'Small Gate, Bugema University',
            'description': (
                'Affordable and highly accessible student hostel located just 2 minutes walk from Bugema University Small Gate. '
                'Features single and double rooms, 24/7 dedicated security guard, continuous piped national water, study reading tables, '
                'and paved security-lit walkways. Room rate is 300,000 UGX per semester inclusive of water.'
            ),
            'images_specs': [
                {'sub': 'Main Front Building & Security Gate', 'bg': (15, 30, 60)},
                {'sub': 'Spacious Bedroom with Bed & Reading Desk', 'bg': (25, 45, 75)},
                {'sub': 'Clean Corridor & Paved Walkways', 'bg': (30, 50, 80)},
            ]
        },
        {
            'owner': 'rose_hostel',
            'name': 'Rose Hostel (Executive Suites)',
            'price': Decimal('800000.00'),
            'location': 'Kiziri, near Bugema University',
            'description': (
                'Premium modern student suites designed for maximum comfort and privacy. '
                'Each self-contained apartment includes a private en-suite bathroom with hot shower, modern ceramic flush toilet, '
                'and a personal kitchenette with sink and storage cabinets. High-speed student WiFi, 24/7 CCTV surveillance, '
                'perimeter stone wall with electric fencing, and spacious paved vehicle/boda parking compound.'
            ),
            'images_specs': [
                {'sub': 'Executive Exterior & Gated Compound', 'bg': (20, 35, 65)},
                {'sub': 'Private Bedroom with Tiled Floor & Balcony', 'bg': (35, 55, 90)},
                {'sub': 'Private En-Suite Bathroom & Flush Toilet', 'bg': (25, 60, 85)},
                {'sub': 'Built-in Kitchenette with Sink & Cupboards', 'bg': (40, 65, 100)},
            ]
        },
        {
            'owner': 'kyaggwe_rentals',
            'name': 'Kyaggwe Student Residence',
            'price': Decimal('400000.00'),
            'location': 'Kiwenda, Bugema University Road',
            'description': (
                'Peaceful and serene student residence located along Kiwenda road with regular campus shuttle access. '
                'Offers quiet individual rooms, large green compound ideal for evening revision and relaxation, '
                'solar perimeter floodlights, 10,000-litre rainwater harvesting tanks, and on-site caretaker. '
                'Special student rate of 400,000 UGX per semester.'
            ),
            'images_specs': [
                {'sub': 'Main Compound & Green Study Gardens', 'bg': (18, 40, 50)},
                {'sub': 'Well-Ventilated Student Room with Wardrobe', 'bg': (28, 55, 65)},
                {'sub': 'Water Reserves & Perimeter Solar Lighting', 'bg': (38, 70, 80)},
            ]
        },
    ]

    for hdata in hostels_data:
        owner = seller_user_map[hdata['owner']]
        hostel = Hostel.objects.filter(name=hdata['name']).first()
        if not hostel:
            hostel = Hostel.objects.create(
                owner=owner,
                name=hdata['name'],
                price=hdata['price'],
                location=hdata['location'],
                description=hdata['description'],
                phone_number=owner.phone_number,
                whatsapp_number=owner.whatsapp_number,
                status=Hostel.Status.ACTIVE,
                is_active=True,
            )
            print(f"Created Hostel: {hostel.name} ({hdata['price']:,.2f} UGX)")

        # Create multi-angle images if fewer than required
        current_img_count = hostel.images.count()
        if current_img_count < len(hdata['images_specs']):
            for idx, img_spec in enumerate(hdata['images_specs']):
                img_file = create_card_image(
                    title=f"{hostel.name} - View {idx+1}",
                    category_name="Hostels & Rentals",
                    price_str=f"UGX {hdata['price']:,.0f} / Semester",
                    condition="RENTAL",
                    location=hdata['location'],
                    subtitle=img_spec['sub'],
                    bg_color=img_spec['bg']
                )
                hostel_img = HostelImage(hostel=hostel)
                filename = f"hostel_{hostel.id}_angle_{idx+1}.jpg"
                hostel_img.image.save(filename, img_file, save=True)
                print(f"  + Added photo: {img_spec['sub']}")

    print("\n=== Seeding Completed Successfully! ===")


if __name__ == '__main__':
    run_seed()
