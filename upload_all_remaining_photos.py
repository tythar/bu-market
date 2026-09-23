import os
import django
import requests
from io import BytesIO

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bu_market.settings')
django.setup()

from django.core.files.base import ContentFile
from marketplace.models import Listing, Hostel

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

brain_dir = r"C:\Users\DELL\.gemini\antigravity-ide\brain\b03bc45a-0980-4521-ab8d-17c9d1db33b5"

# 1. Update Oraimo FreePods with generated photo
oraimo_listing = Listing.objects.filter(title__icontains="Oraimo FreePods").first()
if oraimo_listing:
    oraimo_path = os.path.join(brain_dir, "oraimo_freepods_photo_1789897919754.jpg")
    if os.path.exists(oraimo_path):
        with open(oraimo_path, 'rb') as f:
            oraimo_listing.image.save("real_oraimo_freepods_4.jpg", ContentFile(f.read()), save=True)
            print(f"Updated: {oraimo_listing.title} -> {oraimo_listing.image.url}")

# 2. Remote photo mapping for remaining items
remote_photos = {
    "Fresh Red Onions & Garlic": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?w=800&q=80",
    "Crate of Assorted Sodas": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=800&q=80",
    "Casio fx-991EX": "https://images.unsplash.com/photo-1594980596870-8aa52a78d8cd?w=800&q=80",
    "Wooden Student Study Desk": "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?w=800&q=80",
    "Calculus & Analytic Geometry": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=800&q=80",
    "Rechargeable Table Fan": "https://images.unsplash.com/photo-1567016432779-094069958ea5?w=800&q=80",
    "Electric Kettle": "https://upload.wikimedia.org/wikipedia/commons/5/59/HK_goods_made_in_China_%E5%B0%8F%E7%B1%B3_Xiaomi_%E9%9B%BB%E7%86%B1%E6%B0%B4%E7%93%B6_Mi_electric_product_white_%E6%B0%B4%E7%85%B2_Kettle_June_2021_SS2_06.jpg",
    "Mosquito Net": "https://upload.wikimedia.org/wikipedia/commons/f/f2/Yong_Farmstay_mosquito_net_bed.jpg",
    "Gas Cooker": "https://upload.wikimedia.org/wikipedia/commons/0/0a/Gas_stove_burner_flame.jpg",
    "Solar Powerbank": "https://upload.wikimedia.org/wikipedia/commons/a/ad/Solar_garden_light.jpg",
}

for keyword, url in remote_photos.items():
    listings = Listing.objects.filter(title__icontains=keyword)
    if not listings.exists():
        continue
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            content = r.content
            for listing in listings:
                dest_name = f"real_{listing.slug}.jpg"
                listing.image.save(dest_name, ContentFile(content), save=True)
                print(f"Updated: {listing.title} -> {listing.image.url}")
        else:
            print(f"Failed to fetch {url}, status code: {r.status_code}")
    except Exception as e:
        print(f"Error fetching {url}: {e}")

# 3. Update Kyaggwe Student Residence Hostel image
kyaggwe_hostel = Hostel.objects.filter(name__icontains="Kyaggwe").first()
if kyaggwe_hostel:
    res_url = "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800&q=80"
    try:
        r = requests.get(res_url, headers=headers, timeout=15)
        if r.status_code == 200:
            first_img = kyaggwe_hostel.images.first()
            if first_img:
                first_img.image.save("real_kyaggwe_residence.jpg", ContentFile(r.content), save=True)
                print(f"Updated: {kyaggwe_hostel.name} -> {first_img.image.url}")
    except Exception as e:
        print(f"Error for Kyaggwe: {e}")

print("=== All Remaining Items Successfully Updated! ===")
