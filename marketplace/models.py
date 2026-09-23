from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.conf import settings
from core.validators import validate_file_size
import uuid
import urllib.parse

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    icon = models.CharField(max_length=50, help_text="Bootstrap icon class name, e.g. bi-phone")
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Community(models.Model):
    class HubType(models.TextChoices):
        CAMPUS = 'CAMPUS', 'University / College Campus'
        TOWN = 'TOWN', 'Town / Suburb / Commercial Center'

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    hub_type = models.CharField(max_length=20, choices=HubType.choices, default=HubType.CAMPUS)
    region = models.CharField(max_length=50, default='Central Region')
    icon = models.CharField(max_length=50, default='bi-mortarboard-fill', help_text="Bootstrap icon class")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Communities"
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Listing(models.Model):
    class Condition(models.TextChoices):
        NEW = 'NEW', 'New'
        USED = 'USED', 'Used'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Moderation'
        ACTIVE = 'ACTIVE', 'Active'
        SOLD = 'SOLD', 'Sold'
        REJECTED = 'REJECTED', 'Rejected'
        REMOVED = 'REMOVED', 'Removed by Admin'

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='listings'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='listings'
    )
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    condition = models.CharField(max_length=10, choices=Condition.choices, default=Condition.NEW)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    sold_at = models.DateTimeField(null=True, blank=True)
    removal_reason = models.TextField(blank=True, null=True)
    # ... any other fields you already have (views_count, created_at, etc.)
    community = models.ForeignKey(
        Community,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='listings'
    )
    location = models.CharField(max_length=100, default='Bugema University Main Campus')
    image = models.ImageField(
        upload_to='listings/',
        validators=[validate_file_size]
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    removal_reason = models.TextField(blank=True, null=True)
    is_promoted = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        help_text="Phone number for calls (e.g. +256700000000)"
    )
    whatsapp_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        help_text="WhatsApp number (e.g. +256700000000)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    is_quick_sale = models.BooleanField(default=False)
    quick_sale_expires_at = models.DateTimeField(null=True, blank=True)

    @property
    def whatsapp_url(self):
        if not self.whatsapp_number:
            return None
        cleaned = "".join(c for c in self.whatsapp_number if c.isdigit())
        if cleaned.startswith('0'):
            cleaned = '256' + cleaned[1:]
        return f"https://wa.me/{cleaned}"

    @property
    def tel_url(self):
        if not self.phone_number:
            return None
        cleaned = "".join(c for c in self.phone_number if c.isdigit() or c == '+')
        return f"tel:{cleaned}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Listing.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def clean(self):
        # 1. Enforce seller role
        if not self.seller.is_seller:
            raise ValidationError("Only users with the SELLER role can post listings.")

        # 2. Enforce active subscription
        if not self.seller.has_active_subscription:
            raise ValidationError("You must have an active approved subscription to post listings.")

        # 3. Enforce active listing limits (Only when listing is ACTIVE or PENDING)
        if self.status in [self.Status.ACTIVE, self.Status.PENDING]:
            max_limit = self.seller.max_allowed_active_listings
            # Count other active/pending listings for this seller
            current_active_count = Listing.objects.filter(
                seller=self.seller,
                status__in=[self.Status.ACTIVE, self.Status.PENDING]
            ).exclude(id=self.id).count()

            if current_active_count >= max_limit:
                raise ValidationError(
                    f"Your current subscription plan limits you to {max_limit} active listings. "
                    f"You currently have {current_active_count} active/pending listings."
                )

        # 4. Enforce promoted flag (only SILVER and GOLD allowed)
        if self.is_promoted:
            sub = self.seller.active_subscription
            if sub and not sub.plan.has_promoted_ads:
                raise ValidationError("Only Silver and Gold subscription plans support promoted ads.")

    def __str__(self):
        return self.title


# this is the hostel thing for the database 

class Hostel(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Moderation'
        ACTIVE = 'ACTIVE', 'Active'
        REJECTED = 'REJECTED', 'Rejected'

    class RentalType(models.TextChoices):
        HOSTEL = 'HOSTEL', 'Student Hostel (Single / Shared)'
        BEDSITTER = 'BEDSITTER', 'Bedsitter & Studio Apartment'
        RESIDENTIAL = 'RESIDENTIAL', '1 & 2 Bedroom Residential Rental'
        COMMERCIAL = 'COMMERCIAL', 'Commercial Space & Market Stall'

    class BillingCycle(models.TextChoices):
        PER_MONTH = 'PER_MONTH', 'Per Month'
        PER_SEMESTER = 'PER_SEMESTER', 'Per Semester'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hostels'
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    rental_type = models.CharField(
        max_length=30,
        choices=RentalType.choices,
        default=RentalType.HOSTEL,
        verbose_name="Rental Category"
    )
    billing_cycle = models.CharField(
        max_length=20,
        choices=BillingCycle.choices,
        default=BillingCycle.PER_SEMESTER,
        verbose_name="Billing Cycle"
    )
    community = models.ForeignKey(
        Community,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hostels'
    )
    location = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed info about the rental unit, rules, terms, etc."
    )
    # Universal Amenities
    is_self_contained = models.BooleanField(default=False, verbose_name="Self-Contained (Private Washroom)")
    has_yaka_meter = models.BooleanField(default=False, verbose_name="Prepaid Yaka Electricity Meter")
    has_water_reserve = models.BooleanField(default=False, verbose_name="Water Reserve / Tank / Borehole")
    has_security = models.BooleanField(default=False, verbose_name="Gated Compound / 24/7 Security")
    has_parking = models.BooleanField(default=False, verbose_name="Parking Space Available")

    phone_number = models.CharField(max_length=20, blank=True, null=True)
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    removal_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Housing & Rental"
        verbose_name_plural = "Housing & Rentals"
        ordering = ['-created_at']

    @property
    def billing_display(self):
        return "/ mo" if self.billing_cycle == self.BillingCycle.PER_MONTH else "/ sem"

    @property
    def amenities_list(self):
        items = []
        if self.is_self_contained:
            items.append({'name': 'Self-Contained', 'icon': 'bi-door-closed-fill', 'badge': 'bg-primary-subtle text-primary-emphasis'})
        if self.has_yaka_meter:
            items.append({'name': 'Prepaid Yaka Meter', 'icon': 'bi-lightning-charge-fill', 'badge': 'bg-warning-subtle text-warning-emphasis'})
        if self.has_water_reserve:
            items.append({'name': 'Water Reserve / Borehole', 'icon': 'bi-droplet-fill', 'badge': 'bg-info-subtle text-info-emphasis'})
        if self.has_security:
            items.append({'name': 'Gated / 24/7 Security', 'icon': 'bi-shield-check', 'badge': 'bg-success-subtle text-success-emphasis'})
        if self.has_parking:
            items.append({'name': 'Parking Available', 'icon': 'bi-p-circle-fill', 'badge': 'bg-secondary-subtle text-secondary-emphasis'})
        return items

    @property
    def whatsapp_url(self):
        if not self.whatsapp_number:
            return None
        cleaned = "".join(c for c in self.whatsapp_number if c.isdigit())
        if cleaned.startswith('0'):
            cleaned = '256' + cleaned[1:]
        elif not cleaned.startswith('256') and len(cleaned) == 9:
            cleaned = '256' + cleaned

        msg = (
            f"🏠 *BU-MARKET HOUSING & RENTALS INQUIRY*\n\n"
            f"Hello @{self.owner.username}, I saw your rental listing on BU-MARKET:\n"
            f"🏢 *Property:* {self.name}\n"
            f"🏷️ *Category:* {self.get_rental_type_display()}\n"
            f"💰 *Price:* {self.price:,.0f} UGX ({self.get_billing_cycle_display()})\n"
            f"📍 *Location:* {self.location}"
            + (f" ({self.community.name})" if self.community else "") + "\n\n"
            f"Is this unit currently vacant for inspection? Looking forward to your response! 🚀"
        )
        return f"https://wa.me/{cleaned}?text={urllib.parse.quote(msg)}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Hostel.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def clean(self):
        if not self.owner.is_seller:
            raise ValidationError("Only users with the SELLER role can post hostels.")
        if not self.owner.has_active_subscription:
            raise ValidationError("You must have an active approved subscription to post a hostel.")

    def __str__(self):
        return self.name


class HostelImage(models.Model):
    hostel = models.ForeignKey(
        Hostel,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        upload_to='hostels/',
        validators=[validate_file_size]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.hostel_id:
            existing_count = HostelImage.objects.filter(hostel=self.hostel).exclude(pk=self.pk).count()
            if existing_count >= 4:
                raise ValidationError("A hostel can have a maximum of 4 images.")

    def __str__(self):
        return f"Image for {self.hostel.name}"


class Offer(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review ⏳'
        COUNTERED = 'COUNTERED', 'Counter Offer ⚡'
        ACCEPTED = 'ACCEPTED', 'Offer Accepted 🎉'
        DECLINED = 'DECLINED', 'Declined ❌'
        CANCELLED = 'CANCELLED', 'Cancelled'

    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='offers'
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='offers_made'
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='offers_received'
    )
    original_price = models.DecimalField(max_digits=12, decimal_places=2)
    offered_price = models.DecimalField(max_digits=12, decimal_places=2)
    counter_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    buyer_note = models.CharField(max_length=255, blank=True, default='')
    seller_note = models.CharField(max_length=255, blank=True, default='')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    deal_code = models.CharField(max_length=32, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Offer #{self.id} on {self.listing.title} by {self.buyer.username} - {self.status}"

    @property
    def final_price(self):
        """Returns the accepted/countered price or the offered price."""
        if self.status == self.Status.ACCEPTED:
            return self.counter_price if self.counter_price else self.offered_price
        elif self.status == self.Status.COUNTERED and self.counter_price:
            return self.counter_price
        return self.offered_price

    @property
    def savings_amount(self):
        price = self.final_price
        if self.original_price and price and self.original_price > price:
            return self.original_price - price
        return 0

    @property
    def discount_percent(self):
        if self.original_price and self.original_price > 0:
            savings = self.savings_amount
            return round((savings / self.original_price) * 100)
        return 0

    def generate_deal_code(self):
        if not self.deal_code:
            short_id = uuid.uuid4().hex[:6].upper()
            self.deal_code = f"BUM-DEAL-{short_id}"

    def get_whatsapp_url(self, recipient_role='seller'):
        """
        Generates a direct WhatsApp link with prefilled deal pass text.
        """
        if recipient_role == 'seller':
            phone = self.listing.whatsapp_number or getattr(self.seller, 'phone_number', None)
            target_name = self.seller.username
        else:
            phone = getattr(self.buyer, 'phone_number', None)
            target_name = self.buyer.username

        if not phone:
            return None

        cleaned = "".join(c for c in str(phone) if c.isdigit())
        if cleaned.startswith('0'):
            cleaned = '256' + cleaned[1:]
        elif not cleaned.startswith('256') and len(cleaned) == 9:
            cleaned = '256' + cleaned

        price_formatted = f"{self.final_price:,.0f} UGX" if self.final_price else "Agreed Price"
        orig_formatted = f"{self.original_price:,.0f} UGX" if self.original_price else ""
        deal_ref = self.deal_code or f"OFFER-{self.id}"

        if self.status == self.Status.ACCEPTED:
            msg = (
                f"🤝 *BU-MARKET DEAL CONFIRMED!* 🔒\n\n"
                f"Hey @{target_name}, our bargain for *'{self.listing.title}'* is officially agreed on BU-MARKET!\n\n"
                f"💰 *Agreed Price:* {price_formatted} (Original: {orig_formatted})\n"
                f"🎟️ *Deal Pass Code:* {deal_ref}\n"
                f"📍 *Campus Hub:* {self.listing.community.name if self.listing.community else 'Main Campus'}\n\n"
                f"Let's coordinate where to meet on campus for pickup & inspection! 🚀"
            )
        else:
            msg = (
                f"👋 *BU-MARKET Bargain Offer*\n\n"
                f"Hey @{target_name}, I saw *'{self.listing.title}'* on BU-MARKET and proposed an offer of *{price_formatted}*.\n"
                f"Deal Ref: #{deal_ref}\n\n"
                f"Let me know if we can deal! 🤝"
            )

        encoded_msg = urllib.parse.quote(msg)
        return f"https://wa.me/{cleaned}?text={encoded_msg}"





