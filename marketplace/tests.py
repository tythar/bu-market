from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from .models import Category, Listing
from subscriptions.models import SubscriptionPlan, SellerSubscription

User = get_user_model()

class ListingLimitsTestCase(TestCase):
    def setUp(self):
        # 1. Setup default subscription plans
        self.basic_plan, _ = SubscriptionPlan.objects.get_or_create(
            name=SubscriptionPlan.PlanType.BASIC,
            defaults={
                'monthly_fee': 20000.00,
                'max_active_listings': 2,
                'badge': SubscriptionPlan.BadgeType.NONE,
                'has_promoted_ads': False
            }
        )
        self.silver_plan, _ = SubscriptionPlan.objects.get_or_create(
            name=SubscriptionPlan.PlanType.SILVER,
            defaults={
                'monthly_fee': 30000.00,
                'max_active_listings': 5,
                'badge': SubscriptionPlan.BadgeType.SILVER,
                'has_promoted_ads': True
            }
        )

        # 2. Setup Category
        self.category = Category.objects.create(name="Electronics", icon="bi-laptop")

        # 3. Create Users
        self.seller = User.objects.create_user(
            username='seller_test', 
            email='seller@test.com', 
            password='pass', 
            role=User.Role.SELLER
        )
        self.buyer = User.objects.create_user(
            username='buyer_test', 
            email='buyer@test.com', 
            password='pass', 
            role=User.Role.BUYER
        )

    def test_listing_requires_seller_role(self):
        # Attempt to create a listing under a buyer account.
        listing = Listing(
            seller=self.buyer,
            category=self.category,
            title="Cool Gadget",
            price=50000.00,
            image="test_image.jpg"
        )
        with self.assertRaises(ValidationError):
            listing.clean()

    def test_listing_requires_active_subscription(self):
        # Seller has no subscription yet
        listing = Listing(
            seller=self.seller,
            category=self.category,
            title="Laptop",
            price=800000.00,
            image="laptop.jpg"
        )
        with self.assertRaises(ValidationError):
            listing.clean()

    def test_basic_plan_listing_limits(self):
        # Assign basic plan to seller
        sub = SellerSubscription.objects.create(
            seller=self.seller,
            plan=self.basic_plan,
            amount_paid=20000.00,
            payment_reference="REF123",
            status=SellerSubscription.Status.APPROVED,
            expires_at=timezone.now() + timedelta(days=30)
        )

        # Create listing 1 (should succeed)
        l1 = Listing.objects.create(
            seller=self.seller,
            category=self.category,
            title="Item 1",
            price=100.00,
            status=Listing.Status.ACTIVE,
            image="item1.jpg"
        )
        l1.clean() # Verify clean passes

        # Create listing 2 (should succeed)
        l2 = Listing.objects.create(
            seller=self.seller,
            category=self.category,
            title="Item 2",
            price=200.00,
            status=Listing.Status.ACTIVE,
            image="item2.jpg"
        )
        l2.clean() # Verify clean passes

        # Create listing 3 (should fail validation because BASIC cap is 2)
        l3 = Listing(
            seller=self.seller,
            category=self.category,
            title="Item 3",
            price=300.00,
            status=Listing.Status.ACTIVE,
            image="item3.jpg"
        )
        with self.assertRaises(ValidationError):
            l3.clean()

    def test_promoted_ads_limits(self):
        # Assign basic plan to seller
        sub = SellerSubscription.objects.create(
            seller=self.seller,
            plan=self.basic_plan,
            amount_paid=20000.00,
            payment_reference="REF456",
            status=SellerSubscription.Status.APPROVED,
            expires_at=timezone.now() + timedelta(days=30)
        )

        # Attempt to create promoted ad under BASIC plan (should fail clean)
        listing = Listing(
            seller=self.seller,
            category=self.category,
            title="Promoted Item",
            price=50.00,
            is_promoted=True,
            image="promo.jpg"
        )
        with self.assertRaises(ValidationError):
            listing.clean()


class OfferLifecycleTestCase(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username='seller_bargain',
            email='seller_bargain@test.com',
            password='pass',
            role=User.Role.SELLER
        )
        self.buyer = User.objects.create_user(
            username='buyer_bargain',
            email='buyer_bargain@test.com',
            password='pass',
            role=User.Role.BUYER
        )
        self.category = Category.objects.create(name="Books", icon="bi-book")
        self.listing = Listing.objects.create(
            seller=self.seller,
            category=self.category,
            title="Calculus 3rd Edition Textbook",
            price=100000.00,
            status=Listing.Status.ACTIVE,
            image="book.jpg",
            whatsapp_number="0701234567"
        )

    def test_offer_lifecycle_and_deal_pass(self):
        from .models import Offer

        # 1. Buyer creates an offer for 80,000 UGX (-20%)
        offer = Offer.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            seller=self.seller,
            original_price=self.listing.price,
            offered_price=80000.00,
            buyer_note="Cash ready on campus today!",
            status=Offer.Status.PENDING
        )
        self.assertEqual(offer.savings_amount, 20000.00)
        self.assertEqual(offer.discount_percent, 20)
        self.assertEqual(offer.status, Offer.Status.PENDING)

        # 2. Seller counters with 90,000 UGX
        offer.counter_price = 90000.00
        offer.status = Offer.Status.COUNTERED
        offer.seller_note = "Lowest I can do is 90k boss"
        offer.save()

        self.assertEqual(offer.final_price, 90000.00)
        self.assertEqual(offer.savings_amount, 10000.00)
        self.assertEqual(offer.discount_percent, 10)

        # 3. Buyer accepts the counter offer
        offer.status = Offer.Status.ACCEPTED
        offer.generate_deal_code()
        offer.save()

        self.assertTrue(offer.deal_code.startswith("BUM-DEAL-"))
        self.assertEqual(offer.status, Offer.Status.ACCEPTED)

        # 4. Verify WhatsApp Deal URL contains deal code and agreed price
        whatsapp_url = offer.get_whatsapp_url(recipient_role='seller')
        self.assertIn("wa.me/256701234567", whatsapp_url)
        self.assertIn("90,000", whatsapp_url)
        self.assertIn(offer.deal_code, whatsapp_url)


