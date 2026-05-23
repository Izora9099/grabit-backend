"""
Seed the database with realistic test data for local development.

Usage:
    python manage.py seed_data           # add data (safe to run on empty DB)
    python manage.py seed_data --clear   # wipe everything first, then seed
"""
import datetime

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.utils import timezone
from rest_framework.authtoken.models import Token

from accounts.models import Address, User
from disputes.models import Dispute
from notifications.models import Notification
from orders.models import EscrowEvent, Message, Order, OrderItem
from payments.models import Payment, Payout
from products.models import Product, Review, WishlistItem
from shops.models import KYCDocument, Shop, ShopFollow

PASSWORD = make_password("Grabit2024!")
NOW = timezone.now()


def _ago(days):
    return NOW - datetime.timedelta(days=days)


class Command(BaseCommand):
    help = "Seeds the database with realistic test data for local development"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing data before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self._clear()

        self.stdout.write("Creating users & addresses...")
        u = self._users()

        self.stdout.write("Creating shops...")
        s = self._shops(u)

        self.stdout.write("Creating KYC documents...")
        self._kyc(s)

        self.stdout.write("Creating products...")
        p = self._products(s)

        self.stdout.write("Creating orders...")
        o = self._orders(u, s, p)

        self.stdout.write("Creating payments...")
        self._payments(o)

        self.stdout.write("Creating escrow events...")
        self._escrow(o)

        self.stdout.write("Creating reviews...")
        self._reviews(u, p)

        self.stdout.write("Creating disputes...")
        self._disputes(u, o)

        self.stdout.write("Creating messages...")
        self._messages(u, o)

        self.stdout.write("Creating payouts...")
        self._payouts(u)

        self.stdout.write("Creating notifications...")
        self._notifications(u, o)

        self.stdout.write("Creating shop follows & wishlist...")
        self._follows(u, s)
        self._wishlist(u, p)

        self._print_summary()

    # -------------------------------------------------------------------------
    # clear
    # -------------------------------------------------------------------------

    def _clear(self):
        self.stdout.write(self.style.WARNING("Clearing all data..."))
        Notification.objects.all().delete()
        WishlistItem.objects.all().delete()
        ShopFollow.objects.all().delete()
        Payout.objects.all().delete()
        Message.objects.all().delete()
        Dispute.objects.all().delete()
        Review.objects.all().delete()
        EscrowEvent.objects.all().delete()
        Payment.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        KYCDocument.objects.all().delete()
        Product.objects.all().delete()
        Shop.objects.all().delete()
        Address.objects.all().delete()
        Token.objects.all().delete()
        User.objects.all().delete()
        self.stdout.write(self.style.WARNING("Done clearing.\n"))

    # -------------------------------------------------------------------------
    # users
    # -------------------------------------------------------------------------

    def _make_user(self, email, first, last, role, phone, city,
                   kyc=False, superuser=False):
        u = User(
            username=email,
            email=email,
            first_name=first,
            last_name=last,
            role=role,
            phone=phone,
            city=city,
            password=PASSWORD,
            is_kyc_verified=kyc,
            is_staff=superuser,
            is_superuser=superuser,
            is_active=True,
        )
        u.save()
        Token.objects.get_or_create(user=u)
        return u

    def _users(self):
        admin    = self._make_user("admin@grabit.cm",          "Platform", "Admin",   "admin",  "+237 670 000 001", "Douala",  kyc=True,  superuser=True)
        amina    = self._make_user("amina.nji@gmail.com",      "Amina",    "Nji",     "buyer",  "+237 677 123 456", "Douala")
        paul     = self._make_user("paul.etonde@gmail.com",    "Paul",     "Etonde",  "buyer",  "+237 691 234 567", "Yaoundé")
        claire   = self._make_user("claire.mbah@gmail.com",    "Claire",   "Mbah",    "buyer",  "+237 652 345 678", "Buea")
        boris    = self._make_user("boris.ngwa@gmail.com",     "Boris",    "Ngwa",    "buyer",  "+237 677 456 789", "Douala")
        eric     = self._make_user("eric.tabi@sonichub.cm",    "Eric",     "Tabi",    "vendor", "+237 677 500 100", "Douala",  kyc=True)
        adele    = self._make_user("adele.fonkou@gmail.com",   "Adèle",    "Fonkou",  "vendor", "+237 691 500 200", "Yaoundé", kyc=True)
        jeanpaul = self._make_user("jeanpaul.nkeng@gmail.com", "Jean-Paul","Nkeng",   "vendor", "+237 653 500 300", "Kribi",   kyc=True)
        sophie   = self._make_user("sophie.abouem@gmail.com",  "Sophie",   "Abouem",  "vendor", "+237 677 500 400", "Douala",  kyc=True)
        ndeh     = self._make_user("ndeh.wirba@gmail.com",     "Ndeh",     "Wirba",   "vendor", "+237 691 500 500", "Bamenda", kyc=True)
        victor   = self._make_user("victor.ngum@gmail.com",    "Victor",   "Ngum",    "vendor", "+237 652 500 600", "Buea")
        romuald  = self._make_user("pulsetech.yde@gmail.com",  "Romuald",  "Kom",     "vendor", "+237 677 500 700", "Yaoundé")
        grace    = self._make_user("ecocharge.dla@gmail.com",  "Grace",    "Neba",    "vendor", "+237 691 500 800", "Douala",  kyc=True)
        lionel   = self._make_user("nightglow@gmail.com",      "Lionel",   "Fotso",   "vendor", "+237 652 500 900", "Douala")
        moses    = self._make_user("moses.che@grabit.cm",      "Moses",    "Che",     "agent",  "+237 677 700 001", "Douala",  kyc=True)
        diane    = self._make_user("diane.fokam@grabit.cm",    "Diane",    "Fokam",   "agent",  "+237 691 700 002", "Yaoundé", kyc=True)
        felix    = self._make_user("felix.awah@grabit.cm",     "Felix",    "Awah",    "agent",  "+237 652 700 003", "Buea")

        Address.objects.create(user=amina,  label="Home",   line="Rue Njo Njo, Akwa",                city="Douala",  is_primary=True)
        Address.objects.create(user=amina,  label="Office", line="Immeuble Wouri, Bonapriso",        city="Douala",  is_primary=False)
        Address.objects.create(user=paul,   label="Home",   line="Quartier Bastos, Av. Foch",        city="Yaoundé", is_primary=True)
        Address.objects.create(user=claire, label="Home",   line="Mile 17, Bonduma",                 city="Buea",    is_primary=True)
        Address.objects.create(user=boris,  label="Home",   line="Quartier Logbaba, Douala IV",      city="Douala",  is_primary=True)

        return dict(
            admin=admin, amina=amina, paul=paul, claire=claire, boris=boris,
            eric=eric, adele=adele, jeanpaul=jeanpaul, sophie=sophie,
            ndeh=ndeh, victor=victor, romuald=romuald, grace=grace,
            lionel=lionel, moses=moses, diane=diane, felix=felix,
        )

    # -------------------------------------------------------------------------
    # shops
    # -------------------------------------------------------------------------

    def _mk_shop(self, owner, name, handle, tagline, desc, cat, city, nbhd,
                 whatsapp, email, fee, threshold, return_policy, processing_time,
                 plan, status, verified, followers, rating, reviews_count, response_time):
        return Shop.objects.create(
            owner=owner, name=name, handle=handle, tagline=tagline,
            description=desc, category=cat, city=city, neighbourhood=nbhd,
            whatsapp=whatsapp, email=email,
            delivery_fee=fee, free_shipping_threshold=threshold,
            return_policy=return_policy, processing_time=processing_time,
            plan=plan, status=status, is_verified=verified,
            followers_count=followers, rating=rating,
            reviews_count=reviews_count, response_time=response_time,
        )

    def _shops(self, u):
        sonichub = self._mk_shop(
            u["eric"], "SonicHub Cameroun", "sonichub",
            "Your sound, delivered fast",
            "We stock the best headphones, earbuds, and smart audio devices sourced from verified global distributors. Based in Akwa, Douala, we deliver across Cameroon within 48 hours.",
            "electronics", "Douala", "Akwa",
            "+237 677 500 100", "hello@sonichub.cm",
            1500, 30000,
            "Items can be returned within 7 days if unopened and in original packaging. Contact us via WhatsApp for a return code.",
            "1–2 business days",
            "growth", "active", True, 1240, "4.80", 87, "< 2 hours",
        )
        maison_adele = self._mk_shop(
            u["adele"], "Maison Adèle", "maison-adele",
            "Elegance woven in Cameroon",
            "Curating the finest Cameroonian fashion — Ankara prints, hand-embroidered pieces, and contemporary African design. Based in Bastos, Yaoundé.",
            "fashion", "Yaoundé", "Bastos",
            "+237 691 500 200", "contact@maisonadele.cm",
            2000, 50000,
            "We accept returns within 14 days on unworn items with tags attached. Custom or altered pieces are non-returnable.",
            "2–3 business days",
            "premium", "active", True, 2105, "4.90", 134, "< 1 hour",
        )
        cocoa_coast = self._mk_shop(
            u["jeanpaul"], "Cocoa Coast Co-op", "cocoa-coast",
            "Farm-to-table cacao & spices",
            "A farmers' co-operative from the Kribi coast bringing you organic cocoa beans, single-origin coffee, and artisan spices. 100% traceable supply chain.",
            "food", "Kribi", "Centre-ville",
            "+237 653 500 300", "orders@cocoacoast.cm",
            3500, 20000,
            "Perishable items cannot be returned. Non-perishable items accepted within 5 days if unopened.",
            "3–5 business days",
            "starter", "active", True, 876, "4.70", 58, "< 4 hours",
        )
        maison_cafe = self._mk_shop(
            u["sophie"], "Maison du Café", "maison-du-cafe",
            "Coffee culture in Douala",
            "Specialty coffee equipment, accessories, and premium beans. We stock espresso machines, French presses, grinders, and everything you need for the perfect cup.",
            "home", "Douala", "Bonanjo",
            "+237 677 500 400", "bonjour@maisoncafe.cm",
            1000, 40000,
            "Equipment returns accepted within 10 days if unused. All returns must include original box and accessories.",
            "1–3 business days",
            "growth", "active", True, 654, "4.60", 42, "< 3 hours",
        )
        atelier_ndeh = self._mk_shop(
            u["ndeh"], "Atelier Ndeh", "atelier-ndeh",
            "Crafted in the highlands",
            "Traditional Bamenda craftsmanship — woven bags, raffia clutches, and hand-stitched leather goods. Every piece is handmade by artisans in the North-West Region.",
            "fashion", "Bamenda", "Nkwen",
            "+237 691 500 500", "ndeh@atelierndeh.cm",
            2500, 25000,
            "All handcrafted items are final sale unless there is a defect. Defective items will be replaced or refunded.",
            "3–5 business days",
            "starter", "active", True, 412, "4.50", 29, "< 6 hours",
        )
        mt_bikes = self._mk_shop(
            u["victor"], "Mt Cameroon Bikes", "mt-cameroon-bikes",
            "Ride the mountain",
            "Bicycles, cycling accessories, and outdoor sports gear. Located at the foot of Mount Cameroon in Buea. We ship nationwide — assembly required for bikes.",
            "sports", "Buea", "Molyko",
            "+237 652 500 600", "ride@mtcameronbikes.cm",
            5000, 0,
            "Bikes can be returned within 3 days of delivery if unridden and in original packaging. Accessories within 7 days.",
            "3–7 business days",
            "starter", "active", False, 187, "3.90", 14, "< 8 hours",
        )
        pulsetech = self._mk_shop(
            u["romuald"], "PulseTech", "pulsetech",
            "Fast tech at fair prices",
            "Affordable electronics for everyday Cameroonians — tablets, charging solutions, and smart accessories. Serving Yaoundé with same-day delivery in Melen zone.",
            "electronics", "Yaoundé", "Melen",
            "+237 677 500 700", "pulse@pulsetech.cm",
            1500, 35000,
            "Returns accepted within 5 days for devices. All defects covered under 30-day warranty.",
            "1–2 business days",
            "starter", "active", False, 93, "3.70", 11, "< 4 hours",
        )
        ecocharge = self._mk_shop(
            u["grace"], "EcoCharge", "ecocharge",
            "Clean energy, everywhere",
            "Solar-powered products and portable charging solutions for homes, businesses, and outdoor use. Proudly bridging the energy gap in Cameroon.",
            "electronics", "Douala", "Akwa",
            "+237 691 500 800", "hello@ecocharge.cm",
            2000, 45000,
            "Solar equipment returns accepted within 14 days if unused. All products carry a 6-month manufacturer warranty.",
            "2–4 business days",
            "growth", "active", True, 763, "4.75", 56, "< 2 hours",
        )
        nightglow = self._mk_shop(
            u["lionel"], "NightGlow Electronics", "nightglow",
            "Premium imports at local prices",
            "Import-quality electronics at Douala prices. Currently under review.",
            "electronics", "Douala", "Akwa",
            "+237 652 500 900", "nightglow@gmail.com",
            2000, 30000,
            "No returns accepted.",
            "—",
            "starter", "suspended", False, 12, "0.00", 0, "—",
        )

        return dict(
            sonichub=sonichub, maison_adele=maison_adele, cocoa_coast=cocoa_coast,
            maison_cafe=maison_cafe, atelier_ndeh=atelier_ndeh, mt_bikes=mt_bikes,
            pulsetech=pulsetech, ecocharge=ecocharge, nightglow=nightglow,
        )

    # -------------------------------------------------------------------------
    # KYC documents
    # -------------------------------------------------------------------------

    def _kyc(self, s):
        docs = [
            (s["sonichub"],     "identity", "National ID Card",                    "approved"),
            (s["sonichub"],     "address",  "ENEO utility bill",                   "approved"),
            (s["maison_adele"], "identity", "National ID Card",                    "approved"),
            (s["maison_adele"], "business", "Business registration (RCCM)",        "approved"),
            (s["cocoa_coast"],  "identity", "National ID Card",                    "approved"),
            (s["maison_cafe"],  "identity", "National ID Card",                    "approved"),
            (s["maison_cafe"],  "business", "Business registration (RCCM)",        "approved"),
            (s["atelier_ndeh"], "identity", "National ID Card",                    "approved"),
            (s["ecocharge"],    "identity", "National ID Card",                    "approved"),
            (s["ecocharge"],    "address",  "CAMWATER utility bill",               "approved"),
            (s["mt_bikes"],     "identity", "National ID Card",                    "pending"),
            (s["pulsetech"],    "identity", "National ID Card",                    "not_submitted"),
            (s["nightglow"],    "identity", "National ID Card",                    "rejected"),
        ]
        for shop, doc_type, label, status in docs:
            KYCDocument.objects.create(
                shop=shop, doc_type=doc_type, label=label, status=status
            )

    # -------------------------------------------------------------------------
    # products
    # -------------------------------------------------------------------------

    def _mk_product(self, shop, name, desc, price, cat, cond, stock, status,
                    premium=False, rating="0.00", reviews_count=0, views=0, sales=0):
        return Product.objects.create(
            shop=shop, name=name, description=desc, price=price,
            category=cat, condition=cond, stock=stock, status=status,
            is_premium=premium, rating=rating,
            reviews_count=reviews_count, views=views, sales=sales,
        )

    def _products(self, s):
        headphones = self._mk_product(
            s["sonichub"], "Wireless Noise-Cancelling Headphones",
            "Experience deep, immersive sound with 40-hour battery life and Active Noise Cancellation. Soft memory-foam ear cushions, foldable design, and USB-C fast charging. Compatible with all Bluetooth 5.3 devices.",
            24500, "electronics", "new", 18, "live",
            premium=True, rating="4.80", reviews_count=24, views=812, sales=38,
        )
        smart_watch = self._mk_product(
            s["sonichub"], "Smart Fitness Watch",
            "Track your steps, heart rate, sleep, and stress levels with precision. 1.4\" AMOLED display, 7-day battery, IP68 waterproof, SpO2 monitoring, and 20+ sport modes.",
            45000, "electronics", "new", 7, "live",
            rating="4.60", reviews_count=15, views=534, sales=19,
        )
        ankara_dress = self._mk_product(
            s["maison_adele"], "Ankara Print Wrap Dress",
            "A celebration of African heritage in every stitch. 100% high-density Ankara fabric, tailored to a flattering wrap silhouette. Available in sizes S to 3XL. Hand-wash recommended.",
            18500, "fashion", "new", 24, "live",
            premium=True, rating="4.90", reviews_count=41, views=1205, sales=67,
        )
        headwrap = self._mk_product(
            s["maison_adele"], "Hand-Embroidered Kente Headwrap",
            "Handcrafted in Yaoundé using authentic Kente strip weaving. Bold geometric patterns, 100% cotton base with silk thread embroidery. One size fits all, comes in a gift bag.",
            7500, "fashion", "new", 40, "live",
            rating="4.70", reviews_count=18, views=445, sales=33,
        )
        midi_dress = self._mk_product(
            s["maison_adele"], "Adire Tie-Dye Midi Dress",
            "A new arrival using traditional West African Adire indigo dyeing technique. Free-flowing silhouette, 100% breathable cotton. Limited first run of 15 pieces.",
            22000, "fashion", "new", 15, "pending_review",
            views=87,
        )
        cocoa_beans = self._mk_product(
            s["cocoa_coast"], "Organic Cocoa Beans 1kg",
            "Sun-dried, fermented, and minimally processed cocoa beans from the farms of Kribi. Perfect for home chocolate-making, baking, and hot cocoa. Certified organic.",
            4500, "food", "new", 200, "live",
            rating="4.70", reviews_count=22, views=678, sales=91,
        )
        coffee = self._mk_product(
            s["cocoa_coast"], "Single-Origin Cameroon Coffee 500g",
            "Arabica beans from the slopes of Mount Cameroon, medium roast. Notes of dark chocolate, dried fruit, and subtle citrus. Whole bean or ground on request.",
            6000, "food", "new", 120, "live",
            premium=True, rating="4.60", reviews_count=17, views=389, sales=44,
        )
        espresso = self._mk_product(
            s["maison_cafe"], "Compact Espresso Machine",
            "Brew barista-quality espresso at home with 15-bar pump pressure. Removable 1.2L water tank, steam wand for frothing, built-in descaling program. 220V compatible.",
            65000, "home", "new", 5, "live",
            premium=True, rating="4.60", reviews_count=9, views=302, sales=12,
        )
        french_press = self._mk_product(
            s["maison_cafe"], "Stainless Steel French Press 600ml",
            "Double-walled vacuum insulation keeps your coffee hot for 2 hours. 600ml capacity, 4-stage filter system for sediment-free brew. Dishwasher safe lid and plunger.",
            14500, "home", "new", 22, "live",
            rating="4.50", reviews_count=11, views=198, sales=28,
        )
        bamenda_bag = self._mk_product(
            s["atelier_ndeh"], "Bamenda Woven Market Bag",
            "Hand-woven by artisans in the North-West highlands using traditional grass-weaving techniques. Reinforced base, natural fibre handles, holds up to 15kg. Each bag is uniquely patterned.",
            8500, "fashion", "new", 35, "live",
            rating="4.50", reviews_count=13, views=267, sales=24,
        )
        raffia_clutch = self._mk_product(
            s["atelier_ndeh"], "Leather-Stitched Raffia Clutch",
            "Traditional raffia palm weaving with hand-stitched leather trim and magnetic clasp. Interior lining, card slots, and detachable wrist strap.",
            12000, "fashion", "new", 15, "live",
            rating="4.40", reviews_count=8, views=134, sales=11,
        )
        mountain_bike = self._mk_product(
            s["mt_bikes"], "Mountain Bike 26\" Alloy Frame",
            "21-speed Shimano indexed gearing, front suspension fork, mechanical disc brakes. Lightweight 6061 alloy frame, ideal for trails and city commuting. Self-assembly with included tools.",
            195000, "sports", "new", 3, "live",
            rating="3.90", reviews_count=6, views=445, sales=4,
        )
        helmet_set = self._mk_product(
            s["mt_bikes"], "Cycling Helmet & Gloves Set",
            "CE-certified ABS shell helmet with adjustable rear dial fit system. Paired with half-finger gel-padded cycling gloves. Available in S, M, L sizes.",
            22000, "sports", "new", 8, "live",
            rating="4.20", reviews_count=5, views=178, sales=7,
        )
        tablet = self._mk_product(
            s["pulsetech"], "Dual-Core Android Tablet 10\"",
            "10-inch IPS display at 1280×800, Android 12, 3GB RAM, 32GB storage (expandable to 128GB). Front 5MP + rear 8MP cameras, 6000mAh battery, dual SIM 4G LTE.",
            78000, "electronics", "new", 6, "live",
            rating="3.20", reviews_count=4, views=312, sales=6,
        )
        iphone_12 = self._mk_product(
            s["pulsetech"], "Refurbished iPhone 12 64GB",
            "Grade A refurbished iPhone 12 — professionally cleaned, battery health > 85%, all functions tested. Unlocked for all networks. 30-day store warranty. No original box.",
            185000, "electronics", "like_new", 0, "out_of_stock",
            rating="3.80", reviews_count=3, views=876, sales=12,
        )
        charging_hub = self._mk_product(
            s["pulsetech"], "USB-C Fast Charging Hub 7-port",
            "7-port USB hub: 1×USB-C 65W PD + 3×USB-A QC3.0 + 3×USB-A 5W. Aluminium shell, over-current protection, 1.2m braided cable.",
            16500, "electronics", "new", 30, "draft",
            views=45,
        )
        solar_bank = self._mk_product(
            s["ecocharge"], "Solar Power Bank 30,000mAh",
            "Dual-panel solar charging + USB-C 18W fast charge input. 3 USB-A outputs + 1 USB-C PD output. Built-in LED torch, IP66 rainproof. Charges phones 7–8 times per cycle.",
            35000, "electronics", "new", 14, "live",
            premium=True, rating="4.75", reviews_count=32, views=1089, sales=55,
        )
        solar_panel = self._mk_product(
            s["ecocharge"], "Foldable Solar Panel 60W",
            "Monocrystalline silicon cells at 23% efficiency. Folds to A4 size, charges laptops and tablets directly. Waterproof canvas backing, aluminium kickstand, USB-C 60W output.",
            89000, "electronics", "new", 9, "live",
            rating="4.60", reviews_count=12, views=523, sales=18,
        )

        return dict(
            headphones=headphones, smart_watch=smart_watch,
            ankara_dress=ankara_dress, headwrap=headwrap, midi_dress=midi_dress,
            cocoa_beans=cocoa_beans, coffee=coffee,
            espresso=espresso, french_press=french_press,
            bamenda_bag=bamenda_bag, raffia_clutch=raffia_clutch,
            mountain_bike=mountain_bike, helmet_set=helmet_set,
            tablet=tablet, iphone_12=iphone_12, charging_hub=charging_hub,
            solar_bank=solar_bank, solar_panel=solar_panel,
        )

    # -------------------------------------------------------------------------
    # orders
    # -------------------------------------------------------------------------

    def _mk_order(self, order_id, buyer, shop, agent, status, city, address,
                  total, escrow_released, items, placed_days_ago):
        o = Order(
            order_id=order_id,
            buyer=buyer, shop=shop, agent=agent,
            status=status, city=city, delivery_address=address,
            total=total, escrow_released=escrow_released,
        )
        o.save()
        for product, qty in items:
            OrderItem.objects.create(
                order=o, product=product,
                quantity=qty, unit_price=product.price,
            )
        Order.objects.filter(pk=o.pk).update(placed_at=_ago(placed_days_ago))
        return o

    def _orders(self, u, s, p):
        # GR-10001  Amina → SonicHub → Headphones → COMPLETED (30 days ago)
        o1 = self._mk_order(
            "GR-10001", u["amina"], s["sonichub"], u["moses"],
            "completed", "Douala", "Rue Njo Njo, Akwa, Douala",
            26000, True, [(p["headphones"], 1)], 30,
        )
        # GR-10002  Amina → Maison Adèle → Ankara Dress → DELIVERED_CONFIRM (3 days ago)
        o2 = self._mk_order(
            "GR-10002", u["amina"], s["maison_adele"], None,
            "delivered_confirm", "Douala", "Rue Njo Njo, Akwa, Douala",
            20500, False, [(p["ankara_dress"], 1)], 3,
        )
        # GR-10003  Paul → Cocoa Coast → Cocoa Beans ×2 → IN_TRANSIT (2 days ago)
        o3 = self._mk_order(
            "GR-10003", u["paul"], s["cocoa_coast"], u["diane"],
            "in_transit", "Yaoundé", "Quartier Bastos, Av. Foch, Yaoundé",
            12500, False, [(p["cocoa_beans"], 2)], 2,
        )
        # GR-10004  Claire → SonicHub → Smart Watch → PREPARING (1 day ago)
        o4 = self._mk_order(
            "GR-10004", u["claire"], s["sonichub"], None,
            "preparing", "Buea", "Mile 17, Bonduma, Buea",
            46500, False, [(p["smart_watch"], 1)], 1,
        )
        # GR-10005  Paul → Mt Bikes → Mountain Bike → AWAITING_PAYMENT (failed MTN attempt)
        o5 = self._mk_order(
            "GR-10005", u["paul"], s["mt_bikes"], None,
            "awaiting_payment", "Yaoundé", "Quartier Bastos, Av. Foch, Yaoundé",
            200000, False, [(p["mountain_bike"], 1)], 1,
        )
        # GR-10006  Amina → EcoCharge → Solar Bank → PAID_ESCROW (2 days ago)
        o6 = self._mk_order(
            "GR-10006", u["amina"], s["ecocharge"], None,
            "paid_escrow", "Douala", "Immeuble Wouri, Bonapriso, Douala",
            37000, False, [(p["solar_bank"], 1)], 2,
        )
        # GR-10007  Claire → Maison du Café → French Press + Espresso → DISPUTED / in_review
        o7 = self._mk_order(
            "GR-10007", u["claire"], s["maison_cafe"], u["moses"],
            "disputed", "Buea", "Mile 17, Bonduma, Buea",
            80500, False,
            [(p["french_press"], 1), (p["espresso"], 1)], 5,
        )
        # GR-10008  Boris → PulseTech → Tablet → CANCELLED (payment refunded)
        o8 = self._mk_order(
            "GR-10008", u["boris"], s["pulsetech"], None,
            "cancelled", "Douala", "Quartier Logbaba, Douala IV",
            79500, False, [(p["tablet"], 1)], 4,
        )
        # GR-10009  Amina → Atelier Ndeh → Bamenda Bag ×2 → PICKED_UP (today)
        o9 = self._mk_order(
            "GR-10009", u["amina"], s["atelier_ndeh"], u["moses"],
            "picked_up", "Douala", "Rue Njo Njo, Akwa, Douala",
            19500, False, [(p["bamenda_bag"], 2)], 1,
        )
        # GR-10010  Paul → SonicHub → Headphones → COMPLETED (45 days ago, old order)
        o10 = self._mk_order(
            "GR-10010", u["paul"], s["sonichub"], u["diane"],
            "completed", "Yaoundé", "Quartier Bastos, Av. Foch, Yaoundé",
            26000, True, [(p["headphones"], 1)], 45,
        )
        # GR-10011  Claire → Cocoa Coast → Cocoa Beans ×3 + Coffee ×1 → COMPLETED (20 days ago)
        o11 = self._mk_order(
            "GR-10011", u["claire"], s["cocoa_coast"], u["diane"],
            "completed", "Buea", "Mile 17, Bonduma, Buea",
            23000, True,
            [(p["cocoa_beans"], 3), (p["coffee"], 1)], 20,
        )
        # GR-10012  Paul → EcoCharge → Solar Panel → COMPLETED after resolved dispute
        o12 = self._mk_order(
            "GR-10012", u["paul"], s["ecocharge"], u["moses"],
            "completed", "Yaoundé", "Quartier Bastos, Av. Foch, Yaoundé",
            91000, False, [(p["solar_panel"], 1)], 15,
        )

        return dict(
            o1=o1, o2=o2, o3=o3, o4=o4, o5=o5, o6=o6,
            o7=o7, o8=o8, o9=o9, o10=o10, o11=o11, o12=o12,
        )

    # -------------------------------------------------------------------------
    # payments
    # -------------------------------------------------------------------------

    def _payments(self, o):
        Payment.objects.create(payment_id="PAY-1000", order=o["o1"],  method="mtn_momo",     amount=26000,  phone_number="+237 677 123 456", status="paid",     external_ref="MTN-20260410-001")
        Payment.objects.create(payment_id="PAY-1001", order=o["o2"],  method="orange_money", amount=20500,  phone_number="+237 677 123 456", status="paid",     external_ref="OM-20260520-002")
        Payment.objects.create(payment_id="PAY-1002", order=o["o3"],  method="mtn_momo",     amount=12500,  phone_number="+237 691 234 567", status="paid",     external_ref="MTN-20260521-003")
        Payment.objects.create(payment_id="PAY-1003", order=o["o4"],  method="mtn_momo",     amount=46500,  phone_number="+237 652 345 678", status="paid",     external_ref="MTN-20260522-004")
        # GR-10005: failed payment — buyer tried MTN MoMo, insufficient funds
        Payment.objects.create(payment_id="PAY-1004", order=o["o5"],  method="mtn_momo",     amount=200000, phone_number="+237 691 234 567", status="failed",   external_ref="MTN-FAILED-20260522")
        Payment.objects.create(payment_id="PAY-1005", order=o["o6"],  method="orange_money", amount=37000,  phone_number="+237 677 123 456", status="paid",     external_ref="OM-20260521-005")
        Payment.objects.create(payment_id="PAY-1006", order=o["o7"],  method="bank_transfer", amount=80500, phone_number="",                 status="paid",     external_ref="BANK-20260518-006")
        # GR-10008: cancelled order — payment refunded
        Payment.objects.create(payment_id="PAY-1007", order=o["o8"],  method="mtn_momo",     amount=79500,  phone_number="+237 677 456 789", status="refunded", external_ref="MTN-REFUND-20260519")
        Payment.objects.create(payment_id="PAY-1008", order=o["o9"],  method="orange_money", amount=19500,  phone_number="+237 677 123 456", status="paid",     external_ref="OM-20260522-007")
        Payment.objects.create(payment_id="PAY-1009", order=o["o10"], method="mtn_momo",     amount=26000,  phone_number="+237 691 234 567", status="paid",     external_ref="MTN-20260408-008")
        Payment.objects.create(payment_id="PAY-1010", order=o["o11"], method="orange_money", amount=23000,  phone_number="+237 652 345 678", status="paid",     external_ref="OM-20260503-009")
        # GR-10012: resolved dispute — payment partially refunded
        Payment.objects.create(payment_id="PAY-1011", order=o["o12"], method="mtn_momo",     amount=91000,  phone_number="+237 691 234 567", status="refunded", external_ref="MTN-PARTIAL-20260508")

    # -------------------------------------------------------------------------
    # escrow events
    # -------------------------------------------------------------------------

    def _escrow(self, o):
        ev = [
            # GR-10001  completed: held → released
            (o["o1"],  "held",          26000, "Funds held at payment confirmation"),
            (o["o1"],  "released",      26000, "Buyer confirmed delivery — funds released to SonicHub"),
            # GR-10002  delivered_confirm: held, awaiting buyer confirmation
            (o["o2"],  "held",          20500, "Funds held at payment confirmation"),
            # GR-10003  in_transit: held
            (o["o3"],  "held",          12500, "Funds held at payment confirmation"),
            # GR-10004  preparing: held
            (o["o4"],  "held",          46500, "Funds held at payment confirmation"),
            # GR-10006  paid_escrow: held
            (o["o6"],  "held",          37000, "Funds held at payment confirmation"),
            # GR-10007  disputed: held, extended
            (o["o7"],  "held",          80500, "Funds held — dispute opened, hold extended indefinitely"),
            # GR-10008  cancelled: held → refunded
            (o["o8"],  "held",          79500, "Funds held at payment confirmation"),
            (o["o8"],  "refunded",      79500, "Order cancelled by buyer — full refund issued to MTN MoMo"),
            # GR-10009  picked_up: held
            (o["o9"],  "held",          19500, "Funds held at payment confirmation"),
            # GR-10010  completed: held → released
            (o["o10"], "held",          26000, "Funds held at payment confirmation"),
            (o["o10"], "released",      26000, "Buyer confirmed delivery — funds released to SonicHub"),
            # GR-10011  completed: held → released
            (o["o11"], "held",          23000, "Funds held at payment confirmation"),
            (o["o11"], "released",      23000, "Buyer confirmed delivery — funds released to Cocoa Coast"),
            # GR-10012  resolved dispute: held → partial_refund → released (remainder)
            (o["o12"], "held",          91000, "Funds held at payment confirmation"),
            (o["o12"], "partial_refund", 45500, "Dispute DSP-301 resolved: 50% refund to buyer per admin decision"),
            (o["o12"], "released",      45500, "Remaining 50% released to EcoCharge after partial refund"),
        ]
        for order, event, amount, note in ev:
            EscrowEvent.objects.create(order=order, event=event, amount=amount, note=note)

    # -------------------------------------------------------------------------
    # reviews
    # -------------------------------------------------------------------------

    def _reviews(self, u, p):
        reviews = [
            # 5-star reviews
            (p["headphones"],  u["amina"],  5, "Incredible sound isolation! Arrived well-packaged and 2 hours early. SonicHub is now my go-to for electronics.",                                                       True),
            (p["headphones"],  u["paul"],   4, "Great headphones overall. Bass is punchy, ANC works well in traffic. Only complaint is the USB-C cable feels flimsy.",                                                  True),
            (p["ankara_dress"],u["claire"], 5, "Maison Adèle never disappoints. The fabric quality is top-tier — every compliment I get, I send people here.",                                                         False),
            (p["cocoa_beans"], u["amina"],  5, "These cocoa beans smell like the rainforest. Perfect for hot chocolate season. Will order every month.",                                                                 True),
            (p["cocoa_beans"], u["claire"], 4, "Great quality beans. Delivery to Buea took 4 days which was expected. The aroma is absolutely authentic.",                                                               True),
            (p["espresso"],    u["paul"],   4, "Solid machine for home use. Took a week to deliver to Yaoundé but the coffee quality makes up for it. The steam wand is a nice touch.",                                False),
            (p["solar_bank"],  u["claire"], 5, "Load-shedding hero! Charged my phone and laptop 3 times during that outage last month. Worth every franc.",                                                              True),
            (p["bamenda_bag"], u["amina"],  5, "Absolutely beautiful craftsmanship. You can feel the quality of every weave. I get asked about this bag everywhere I go. Atelier Ndeh is a gem!",                      True),
            (p["smart_watch"], u["claire"], 4, "Accurate health tracking and the battery lasts 6 days for me. The strap material is a bit rough initially but softens with use.",                                       False),
            (p["solar_panel"], u["paul"],   3, "Panel works but the kickstand is very flimsy. Had a dispute about delivery damage — the partial refund resolution was fair. Panel still functions.",                    True),
            # Negative reviews — realistic complaints
            (p["tablet"],      u["boris"],  2, "Disappointed. Screen has dead pixels in the top corner and the camera lags badly. Tried to return but was given the run-around. Not recommended.",                     True),
            (p["mountain_bike"],u["paul"],  3, "The bike itself is decent but arrived with a bent derailleur. Assembly instructions are in Chinese only. Had to pay a local mechanic. Vendor response was very slow.", True),
        ]
        for product, buyer, rating, text, verified in reviews:
            Review.objects.create(
                product=product, buyer=buyer, rating=rating,
                text=text, is_verified_purchase=verified,
            )

    # -------------------------------------------------------------------------
    # disputes
    # -------------------------------------------------------------------------

    def _disputes(self, u, o):
        # DSP-300  Claire vs Maison du Café — wrong item — in_review (urgent queue)
        d1 = Dispute(
            dispute_id="DSP-300",
            order=o["o7"],
            opened_by=u["claire"],
            reason="wrong_item",
            description=(
                "I ordered a Stainless Steel French Press (600ml) and a Compact Espresso Machine "
                "but received a standard drip coffee maker and a branded mug. The items are "
                "completely different from what was listed. I have photos. Please arrange a pickup "
                "of the wrong items and send my correct order immediately."
            ),
            status="in_review",
        )
        d1.save()
        Dispute.objects.filter(pk=d1.pk).update(created_at=_ago(3))

        # DSP-301  Paul vs EcoCharge — damaged on arrival — RESOLVED (partial_refund)
        d2 = Dispute(
            dispute_id="DSP-301",
            order=o["o12"],
            opened_by=u["paul"],
            reason="damaged",
            description=(
                "The Foldable Solar Panel arrived with a cracked aluminium frame and two of the "
                "solar cells are visibly shattered. The outer packaging was intact so this appears "
                "to be a manufacturing defect or improper internal packing by the vendor. "
                "I want a full replacement or a full refund."
            ),
            status="resolved",
            resolution="partial_refund",
            resolved_by=u["admin"],
            admin_note=(
                "Vendor provided packaging photos showing proper packing. Damage is consistent "
                "with transit handling, not vendor fault. Platform ruling: 50% partial refund "
                "(45,500 XAF) to buyer; 50% released to vendor. Both parties notified. Case closed."
            ),
        )
        d2.save()
        Dispute.objects.filter(pk=d2.pk).update(
            created_at=_ago(12), resolved_at=_ago(8)
        )

    # -------------------------------------------------------------------------
    # messages
    # -------------------------------------------------------------------------

    def _messages(self, u, o):
        threads = [
            # Thread 1: Amina ↔ Eric — GR-10001 (completed, fully read)
            (u["amina"],   u["eric"],     o["o1"],  True,  "Hi, can you confirm dispatch for my headphones order? I need it before the weekend."),
            (u["eric"],    u["amina"],    o["o1"],  True,  "Hi Amina! Your order is packed and ready. Agent Moses will pick up in about 1 hour and you'll get a notification when he's on his way."),
            (u["amina"],   u["eric"],     o["o1"],  True,  "Perfect, thank you so much!"),
            (u["eric"],    u["amina"],    o["o1"],  True,  "Delivered and done! Thanks for shopping with SonicHub. Hope you love the headphones."),

            # Thread 2: Claire ↔ Sophie — GR-10007 (disputed, unread on sophie's side)
            (u["claire"],  u["sophie"],   o["o7"],  True,  "Hi, I received the wrong items. I ordered a French press and espresso machine but got a drip maker and a branded mug."),
            (u["sophie"],  u["claire"],   o["o7"],  True,  "Claire, I am so sorry about this. This is completely unacceptable. Let me check with my warehouse right now."),
            (u["claire"],  u["sophie"],   o["o7"],  False, "I've raised a formal dispute. I need this resolved urgently — I have an event this weekend."),
            (u["sophie"],  u["claire"],   o["o7"],  False, "I understand and I've escalated this internally. The dispute team will contact you within 24 hours. I'm truly sorry for the inconvenience."),

            # Thread 3: Paul ↔ Jean-Paul — GR-10003 (in transit)
            (u["paul"],    u["jeanpaul"], o["o3"],  True,  "Bonjour, when will my order arrive in Yaoundé? It's been 2 days."),
            (u["jeanpaul"],u["paul"],     o["o3"],  True,  "Bonjour Paul! Agent Diane picked it up this morning and is currently in transit. Expected arrival by end of day today."),
            (u["paul"],    u["jeanpaul"], o["o3"],  False, "Perfect, merci beaucoup!"),

            # Thread 4: Amina ↔ Ndeh — GR-10009 (picked_up)
            (u["amina"],   u["ndeh"],     o["o9"],  True,  "Hi Ndeh, confirming my order for 2 Bamenda bags — is it ready for pickup?"),
            (u["ndeh"],    u["amina"],    o["o9"],  False, "Yes Amina! Both bags are wrapped and ready. Agent Moses will be at my Nkwen shop in about 30 minutes."),

            # Thread 5: Paul ↔ Grace — GR-10012 (resolved dispute, completed)
            (u["paul"],    u["grace"],    o["o12"], True,  "My solar panel arrived damaged — the frame is cracked and two cells are shattered. What is your return process?"),
            (u["grace"],   u["paul"],     o["o12"], True,  "Paul, I'm very sorry to hear this. Please open a dispute through the platform with photos and we'll work to resolve it immediately."),
            (u["paul"],    u["grace"],    o["o12"], True,  "Dispute has been opened. I hope this is resolved fairly."),
            (u["grace"],   u["paul"],     o["o12"], True,  "The admin team has reviewed and issued a partial refund. I'm sorry the panel arrived damaged — I've flagged the transit issue with our courier."),
        ]
        for sender, recipient, order, read, body in threads:
            Message.objects.create(
                sender=sender, recipient=recipient, order=order,
                body=body, read=read,
            )

    # -------------------------------------------------------------------------
    # payouts
    # -------------------------------------------------------------------------

    def _payouts(self, u):
        import datetime as dt
        payouts = [
            # Eric — SonicHub (growth plan, 3.5% fee)
            ("PO-1", u["eric"],    "mtn_momo",     24700,  "paid",       dt.date(2026, 5, 10)),
            ("PO-4", u["eric"],    "mtn_momo",     24700,  "paid",       dt.date(2026, 4, 10)),
            # Adèle — Maison Adèle (premium plan, 2.8% fee)
            ("PO-2", u["adele"],   "orange_money", 18880,  "paid",       dt.date(2026, 5, 10)),
            # Jean-Paul — Cocoa Coast (starter plan, 5% fee)
            ("PO-3", u["jeanpaul"],"mtn_momo",     11875,  "processing", dt.date(2026, 5, 24)),
            # Grace — EcoCharge (growth plan, 3.5% fee)
            ("PO-5", u["grace"],   "orange_money", 33725,  "paid",       dt.date(2026, 5, 10)),
            # Victor — Mt Cameroon Bikes (failed payout — wrong MoMo number)
            ("PO-6", u["victor"],  "mtn_momo",     185000, "failed",     dt.date(2026, 5, 15)),
            # Sophie — Maison du Café (processing — dispute hold)
            ("PO-7", u["sophie"],  "bank_transfer", 61988, "processing", dt.date(2026, 5, 24)),
            # Ndeh — Atelier Ndeh (starter plan, 5% fee)
            ("PO-8", u["ndeh"],    "mtn_momo",     16625,  "paid",       dt.date(2026, 5, 10)),
        ]
        for payout_id, recipient, method, amount, status, payout_date in payouts:
            Payout.objects.create(
                payout_id=payout_id, recipient=recipient, method=method,
                amount=amount, status=status, payout_date=payout_date,
            )

    # -------------------------------------------------------------------------
    # notifications
    # -------------------------------------------------------------------------

    def _notifications(self, u, o):
        notifs = [
            # Amina — buyer
            (u["amina"],  "order",    "Order GR-10001 completed",         "Your order from SonicHub Cameroun has been marked complete. Escrow funds released to vendor.",                            "/orders/GR-10001", True),
            (u["amina"],  "delivery", "Agent assigned to GR-10002",       "Moses Che will deliver your Maison Adèle order today between 2 pm and 5 pm.",                                            "/orders/GR-10002", True),
            (u["amina"],  "price",    "Price drop: Solar Power Bank",      "EcoCharge dropped the Solar Power Bank from 40,000 to 35,000 XAF. It's in your wishlist!",                              "/product/solar-bank", False),
            (u["amina"],  "order",    "GR-10009 picked up by agent",       "Moses Che has collected your Atelier Ndeh order and is on his way to Akwa, Douala.",                                    "/orders/GR-10009", False),
            (u["amina"],  "shop",     "Maison Adèle: new arrivals",        "3 new pieces from the Adire collection just dropped at Maison Adèle. Limited stock.",                                   "/shop/maison-adele", False),

            # Paul — buyer
            (u["paul"],   "order",    "GR-10003 is in transit",            "Diane Fokam is on the way with your Cocoa Coast order. Estimated delivery: today.",                                     "/orders/GR-10003", True),
            (u["paul"],   "order",    "Payment failed for GR-10005",       "Your MTN MoMo payment of 200,000 XAF could not be processed (insufficient funds). Please retry or switch method.",      "/orders/GR-10005", False),
            (u["paul"],   "shop",     "Cocoa Coast: coffee back in stock", "Single-Origin Cameroon Coffee 500g is back in stock. You followed this shop.",                                          "/shop/cocoa-coast", True),
            (u["paul"],   "dispute",  "Dispute DSP-301 resolved",          "Your dispute has been resolved with a 50% partial refund. 45,500 XAF will be returned to your MTN MoMo account.",      "/disputes/DSP-301", False),
            (u["paul"],   "order",    "GR-10010 completed",                "Your old SonicHub order is confirmed complete. Escrow funds have been released.",                                       "/orders/GR-10010", True),

            # Claire — buyer
            (u["claire"], "dispute",  "Dispute DSP-300 under review",      "Our team is reviewing your dispute against Maison du Café. Expect a response within 24 hours.",                        "/disputes/DSP-300", False),
            (u["claire"], "order",    "GR-10007 marked as disputed",        "Order GR-10007 is now disputed. Escrow funds are held until the dispute is resolved.",                                 "/orders/GR-10007", True),
            (u["claire"], "delivery", "GR-10002 delivered — confirm?",     "Your Ankara Dress from Maison Adèle has been delivered. Please confirm receipt so the vendor gets paid.",              "/orders/GR-10002", False),
            (u["claire"], "order",    "GR-10011 completed",                 "Your Cocoa Coast order is confirmed complete. Thank you for shopping with GrabIT.",                                    "/orders/GR-10011", True),

            # Boris — buyer
            (u["boris"],  "order",    "Order GR-10008 cancelled",          "Your Tablet order has been cancelled. Your refund of 79,500 XAF will arrive in your MTN MoMo account within 3–5 days.", "/orders/GR-10008", False),

            # Eric — vendor
            (u["eric"],   "order",    "New order: GR-10004",               "Claire Mbah ordered a Smart Fitness Watch. Please prepare it for pickup within 24 hours.",                             "/dashboard/vendor/orders", False),
            (u["eric"],   "system",   "Payout PO-1 sent",                  "24,700 XAF has been sent to your MTN MoMo account ending in **100.",                                                   "/dashboard/vendor/payouts", True),
            (u["eric"],   "order",    "New order: GR-10001",               "Amina Nji ordered Wireless Noise-Cancelling Headphones. Agent Moses assigned for pickup.",                             "/dashboard/vendor/orders", True),

            # Sophie — vendor
            (u["sophie"], "dispute",  "Dispute opened on GR-10007",        "Claire Mbah opened a dispute (wrong item) on order GR-10007. Please respond within 48 hours or escrow will be refunded.", "/dashboard/vendor/orders", False),
            (u["sophie"], "order",    "Payout PO-7 pending",               "Your payout of 61,988 XAF is on hold pending resolution of the active dispute on GR-10007.",                          "/dashboard/vendor/payouts", False),

            # Victor — vendor
            (u["victor"], "system",   "Payout PO-6 failed",                "Your payout of 185,000 XAF via MTN MoMo could not be processed. Please update your payout account details.",          "/dashboard/vendor/payouts", False),

            # Moses — agent
            (u["moses"],  "delivery", "New pickup assignment: GR-10009",   "Pick up 2× Bamenda bags from Atelier Ndeh (Nkwen, Bamenda). Deliver to Akwa, Douala by 6 pm.",                        "/dashboard/agent/assignments", False),
            (u["moses"],  "delivery", "GR-10001 delivery confirmed",       "Amina Nji confirmed receipt of GR-10001. Your delivery earnings have been updated.",                                    "/dashboard/agent/earnings", True),

            # Diane — agent
            (u["diane"],  "delivery", "New pickup assignment: GR-10003",   "Pick up 2× Organic Cocoa Beans 1kg from Cocoa Coast Co-op, Kribi. Deliver to Bastos, Yaoundé.",                       "/dashboard/agent/assignments", False),
            (u["diane"],  "delivery", "GR-10011 delivery confirmed",       "Claire Mbah confirmed receipt of GR-10011. Your delivery earnings have been updated.",                                  "/dashboard/agent/earnings", True),

            # Admin
            (u["admin"],  "dispute",  "New urgent dispute: DSP-300",       "Claire Mbah opened a wrong-item dispute on order GR-10007 (Maison du Café). Review required.",                        "/internal/console-7f3a9b2c4e8d1a6f/disputes", False),
            (u["admin"],  "system",   "Shop suspended: NightGlow",         "NightGlow Electronics has been suspended following a rejected KYC document submission.",                               "/internal/console-7f3a9b2c4e8d1a6f/shops", True),
        ]
        for user, type_, title, body, href, read in notifs:
            Notification.objects.create(
                user=user, type=type_, title=title,
                body=body, href=href, read=read,
            )

    # -------------------------------------------------------------------------
    # shop follows
    # -------------------------------------------------------------------------

    def _follows(self, u, s):
        follows = [
            (u["amina"],  s["sonichub"]),
            (u["amina"],  s["maison_adele"]),
            (u["amina"],  s["ecocharge"]),
            (u["amina"],  s["atelier_ndeh"]),
            (u["paul"],   s["cocoa_coast"]),
            (u["paul"],   s["maison_cafe"]),
            (u["paul"],   s["ecocharge"]),
            (u["claire"], s["atelier_ndeh"]),
            (u["claire"], s["ecocharge"]),
            (u["claire"], s["cocoa_coast"]),
            (u["boris"],  s["pulsetech"]),
        ]
        for user, shop in follows:
            ShopFollow.objects.create(user=user, shop=shop)

    # -------------------------------------------------------------------------
    # wishlist
    # -------------------------------------------------------------------------

    def _wishlist(self, u, p):
        items = [
            (u["amina"],  p["mountain_bike"]),
            (u["amina"],  p["solar_panel"]),
            (u["paul"],   p["smart_watch"]),
            (u["paul"],   p["espresso"]),
            (u["claire"], p["headphones"]),
            (u["claire"], p["ankara_dress"]),
            (u["boris"],  p["iphone_12"]),   # out_of_stock product in wishlist
            (u["boris"],  p["solar_bank"]),
        ]
        for user, product in items:
            WishlistItem.objects.create(user=user, product=product)

    # -------------------------------------------------------------------------
    # summary
    # -------------------------------------------------------------------------

    def _print_summary(self):
        from accounts.models import Address, User
        from disputes.models import Dispute
        from notifications.models import Notification
        from orders.models import EscrowEvent, Message, Order, OrderItem
        from payments.models import Payment, Payout
        from products.models import Product, Review, WishlistItem
        from shops.models import KYCDocument, Shop, ShopFollow

        self.stdout.write("\n" + "=" * 52)
        self.stdout.write(self.style.SUCCESS("  GRABIT SEED DATA — COMPLETE"))
        self.stdout.write("=" * 52)
        rows = [
            ("Users",          User.objects.count()),
            ("Addresses",      Address.objects.count()),
            ("Auth Tokens",    Token.objects.count()),
            ("Shops",          Shop.objects.count()),
            ("KYC Documents",  KYCDocument.objects.count()),
            ("Products",       Product.objects.count()),
            ("Orders",         Order.objects.count()),
            ("Order Items",    OrderItem.objects.count()),
            ("Payments",       Payment.objects.count()),
            ("Escrow Events",  EscrowEvent.objects.count()),
            ("Reviews",        Review.objects.count()),
            ("Disputes",       Dispute.objects.count()),
            ("Messages",       Message.objects.count()),
            ("Payouts",        Payout.objects.count()),
            ("Notifications",  Notification.objects.count()),
            ("Shop Follows",   ShopFollow.objects.count()),
            ("Wishlist Items", WishlistItem.objects.count()),
        ]
        for label, count in rows:
            self.stdout.write(f"  {label:<22} {count}")
        self.stdout.write("=" * 52)
        self.stdout.write(self.style.SUCCESS("\nAll passwords: Grabit2024!\n"))
        accounts = [
            ("admin@grabit.cm",          "Admin console + full access"),
            ("amina.nji@gmail.com",       "Buyer — orders, wishlist, follows, messages"),
            ("paul.etonde@gmail.com",     "Buyer — in-transit order, failed payment, resolved dispute"),
            ("claire.mbah@gmail.com",     "Buyer — open dispute, delivered_confirm awaiting"),
            ("boris.ngwa@gmail.com",      "Buyer — cancelled order + refund"),
            ("eric.tabi@sonichub.cm",     "Vendor — SonicHub (verified, growth, paid out)"),
            ("adele.fonkou@gmail.com",    "Vendor — Maison Adèle (verified, premium)"),
            ("sophie.abouem@gmail.com",   "Vendor — Maison du Café (order under dispute)"),
            ("victor.ngum@gmail.com",     "Vendor — Mt Cameroon Bikes (failed payout)"),
            ("nightglow@gmail.com",       "Vendor — NightGlow (suspended shop)"),
            ("moses.che@grabit.cm",       "Agent — active + completed deliveries"),
            ("diane.fokam@grabit.cm",     "Agent — in-transit delivery"),
            ("felix.awah@grabit.cm",      "Agent — newly registered, no deliveries yet"),
        ]
        for email, note in accounts:
            self.stdout.write(f"  {email:<34} {note}")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Extra scenarios covered:"))
        extras = [
            "Cancelled order (GR-10008) with refunded payment (PAY-1007)",
            "Failed payment attempt (PAY-1004) — MTN MoMo insufficient funds",
            "Picked-up order in transit (GR-10009) — agent Moses en route",
            "Resolved dispute (DSP-301) with partial_refund escrow split",
            "In-review dispute (DSP-300) — wrong item received",
            "Suspended shop (NightGlow) with rejected KYC",
            "Out-of-stock product (Refurbished iPhone 12) in a buyer's wishlist",
            "Pending review product (Adire Midi Dress) — newly listed",
            "Draft product (USB-C Hub) — not yet published",
            "Like_new condition product (Refurbished iPhone 12)",
            "2-star review (tablet) and 3-star reviews — realistic negative feedback",
            "Failed vendor payout (PO-6) — wrong MoMo number",
            "New agent with no deliveries (Felix Awah)",
            "Multi-item order (GR-10007, GR-10011) with mixed products",
        ]
        for e in extras:
            self.stdout.write(f"  • {e}")
        self.stdout.write("")
