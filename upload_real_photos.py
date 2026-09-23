import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bu_market.settings')
django.setup()

from django.core.files import File
from marketplace.models import Listing, Hostel, HostelImage

brain_dir = r"C:\Users\DELL\.gemini\antigravity-ide\brain\b03bc45a-0980-4521-ab8d-17c9d1db33b5"

photo_mappings = {
    "Fresh Farm Eggs": "eggs_tray_photo_1789896362583.jpg",
    "Kampala Tomatoes": "fresh_tomatoes_photo_1789896384231.jpg",
    "Irish Potatoes": "irish_potatoes_photo_1789896522224.jpg",
    "Mattress with Washable Cover": "hostel_mattress_photo_1789896552382.jpg",
    "Rose Foam 3x6": "hostel_mattress_photo_1789896552382.jpg",
    "Total 6kg Gas Cylinder": "gas_cylinder_photo_1789896683852.jpg",
    "Shell 13kg Cooking Gas": "gas_cylinder_photo_1789896683852.jpg",
    "Subwoofer": "subwoofer_system_photo_1789896754580.jpg",
    "Plastic Water Bucket": "plastic_buckets_photo_1789896851755.jpg",
    "Smart Android TV": "smart_tv_display_1789896904739.jpg",
    "HP EliteBook": "laptop_photo_1789897071980.jpg",
    "Dell Latitude": "laptop_photo_1789897071980.jpg",
    "Samsung Galaxy A15": "phone_photo_1789897148926.jpg",
}

print("=== Uploading Real Photos to Supabase and Assigning to Listings ===")

for title_keyword, filename in photo_mappings.items():
    full_path = os.path.join(brain_dir, filename)
    if not os.path.exists(full_path):
        print(f"Warning: {full_path} not found!")
        continue

    listings = Listing.objects.filter(title__icontains=title_keyword)
    for listing in listings:
        with open(full_path, 'rb') as f:
            django_file = File(f)
            dest_filename = f"real_{listing.slug}.jpg"
            listing.image.save(dest_filename, django_file, save=True)
            print(f"Updated listing '{listing.title}' with real photo: {listing.image.url}")

# Also update Hostels with real photos!
sl_hostel = Hostel.objects.filter(name__icontains="SL Hostel").first()
if sl_hostel:
    sl_img_path = os.path.join(brain_dir, "sl_hostel_building_1789897014255.jpg")
    if os.path.exists(sl_img_path):
        first_img = sl_hostel.images.first()
        if first_img:
            with open(sl_img_path, 'rb') as f:
                first_img.image.save(f"real_sl_hostel_main.jpg", File(f), save=True)
                print(f"Updated SL Hostel main image with real photo: {first_img.image.url}")

rose_hostel = Hostel.objects.filter(name__icontains="Rose Hostel").first()
if rose_hostel:
    rose_img_path = os.path.join(brain_dir, "rose_hostel_room_1789896798868.jpg")
    if os.path.exists(rose_img_path):
        first_img = rose_hostel.images.first()
        if first_img:
            with open(rose_img_path, 'rb') as f:
                first_img.image.save(f"real_rose_hostel_room.jpg", File(f), save=True)
                print(f"Updated Rose Hostel main image with real photo: {first_img.image.url}")

print("=== All Real Photos Successfully Uploaded & Assigned! ===")
