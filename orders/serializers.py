from decimal import Decimal

from django.db import models, transaction
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from .models import Order, OrderFinancials, OrderItem, Message, get_commission_rate  # noqa: F401 (get_commission_rate used in create)
from products.models import Product


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    subtotal = serializers.IntegerField(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "quantity", "unit_price", "subtotal"]


class OrderFinancialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderFinancials
        fields = [
            "subtotal", "delivery_fee", "total",
            "commission_rate", "platform_fee", "seller_amount",
            "buyer_refund_amount", "vendor_release_amount",
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    financials = OrderFinancialsSerializer(read_only=True)
    shop_name = serializers.CharField(source="shop.name", read_only=True)
    buyer_name = serializers.CharField(source="buyer.get_full_name", read_only=True)
    agent_name = serializers.CharField(source="agent.get_full_name", read_only=True)
    vendor_user_id = serializers.IntegerField(source="shop.owner.id", read_only=True)
    agent_user_id = serializers.IntegerField(source="agent.id", allow_null=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "order_id", "status", "city", "delivery_address", "total",
            "escrow_released", "placed_at", "updated_at",
            "shop_name", "buyer_name", "agent_name", "vendor_user_id", "agent_user_id",
            "items", "financials",
        ]
        read_only_fields = [
            "order_id", "total", "escrow_released", "placed_at", "updated_at",
            "shop_name", "buyer_name", "agent_name", "vendor_user_id", "agent_user_id",
        ]


class CreateOrderSerializer(serializers.Serializer):
    """
    Used by buyers to place an order.

    All prices are recalculated server-side from canonical DB values.
    The entire creation is wrapped in a single atomic transaction with
    row-level locks on the shop and each product to prevent overselling
    and concurrent conflicting orders.
    """
    shop_id = serializers.IntegerField()
    city = serializers.CharField(max_length=80)
    delivery_address = serializers.CharField()
    items = serializers.ListField(child=serializers.DictField())

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("Order must have at least one item.")
        for item in items:
            if "product_id" not in item or "quantity" not in item:
                raise serializers.ValidationError("Each item needs product_id and quantity.")
            try:
                qty = int(item["quantity"])
            except (ValueError, TypeError):
                raise serializers.ValidationError("quantity must be a positive integer.")
            if qty < 1:
                raise serializers.ValidationError("quantity must be at least 1.")
        return items

    def create(self, validated_data):
        from shops.models import Shop

        buyer = self.context["request"].user

        with transaction.atomic():
            shop = Shop.objects.select_for_update().get(id=validated_data["shop_id"])

            if shop.status != "active":
                raise serializers.ValidationError("This shop is not currently accepting orders.")

            subtotal = Decimal(0)
            order_items = []

            for item in validated_data["items"]:
                product = Product.objects.select_for_update().get(id=item["product_id"])

                if product.shop_id != shop.id:
                    raise serializers.ValidationError(
                        f"Product '{product.name}' does not belong to this shop."
                    )
                if product.status != "live":
                    raise serializers.ValidationError(
                        f"Product '{product.name}' is no longer available."
                    )

                qty = int(item["quantity"])
                if product.stock < qty:
                    raise serializers.ValidationError(
                        f"'{product.name}' only has {product.stock} unit(s) available."
                    )

                unit_price = Decimal(product.price)
                subtotal += qty * unit_price
                order_items.append((product, qty, int(unit_price)))

            # Delivery fee — waived if order meets free shipping threshold
            delivery_fee = Decimal(shop.delivery_fee)
            if shop.free_shipping_threshold > 0 and subtotal >= shop.free_shipping_threshold:
                delivery_fee = Decimal(0)
            total = subtotal + delivery_fee

            commission_rate = get_commission_rate(shop)
            platform_fee = (total * commission_rate).quantize(Decimal("1"))
            seller_amount = total - platform_fee

            order = Order.objects.create(
                buyer=buyer,
                shop=shop,
                city=validated_data["city"],
                delivery_address=validated_data["delivery_address"],
                total=int(total),
            )

            items_to_create = []
            for product, qty, unit_price in order_items:
                items_to_create.append(
                    OrderItem(order=order, product=product, quantity=qty, unit_price=unit_price)
                )
                # Decrement stock at DB level to avoid Python-level race
                Product.objects.filter(pk=product.pk).update(stock=models.F("stock") - qty)

            OrderItem.objects.bulk_create(items_to_create)

            OrderFinancials.objects.create(
                order=order,
                subtotal=int(subtotal),
                delivery_fee=int(delivery_fee),
                total=int(total),
                commission_rate=commission_rate,
                platform_fee=int(platform_fee),
                seller_amount=int(seller_amount),
            )

        return order


class ReceiptSerializer(serializers.ModelSerializer):
    """
    Read-only serializer that assembles all data a frontend needs to render a purchase receipt.
    Returned by GET /orders/<order_id>/receipt/.
    """
    items        = OrderItemSerializer(many=True, read_only=True)
    subtotal     = serializers.IntegerField(source="financials.subtotal", default=None)
    delivery_fee = serializers.IntegerField(source="financials.delivery_fee", default=None)

    buyer_name  = serializers.CharField(source="buyer.get_full_name")
    buyer_email = serializers.EmailField(source="buyer.email")
    buyer_phone = serializers.CharField(source="buyer.phone")

    shop_name     = serializers.CharField(source="shop.name")
    shop_handle   = serializers.CharField(source="shop.handle")
    shop_city     = serializers.CharField(source="shop.city")
    shop_email    = serializers.EmailField(source="shop.email")
    shop_whatsapp = serializers.CharField(source="shop.whatsapp")

    payment_id     = serializers.SerializerMethodField()
    payment_method = serializers.SerializerMethodField()
    payment_phone  = serializers.SerializerMethodField()
    paid_at        = serializers.SerializerMethodField()

    def _payment(self, obj):
        try:
            return obj.payment
        except Exception:
            return None

    def get_payment_id(self, obj):
        p = self._payment(obj)
        return p.payment_id if p else None

    def get_payment_method(self, obj):
        p = self._payment(obj)
        return p.method if p else None

    def get_payment_phone(self, obj):
        p = self._payment(obj)
        return p.phone_number if p else None

    def get_paid_at(self, obj):
        p = self._payment(obj)
        return p.updated_at if p and p.status == "paid" else None

    class Meta:
        model = Order
        fields = [
            "order_id", "placed_at", "status",
            "delivery_address", "city",
            "items", "subtotal", "delivery_fee", "total",
            "buyer_name", "buyer_email", "buyer_phone",
            "shop_name", "shop_handle", "shop_city", "shop_email", "shop_whatsapp",
            "payment_id", "payment_method", "payment_phone", "paid_at",
        ]


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.get_full_name", read_only=True)

    class Meta:
        model = Message
        fields = ["id", "order", "sender", "sender_name", "recipient", "body", "read", "created_at"]
        read_only_fields = ["id", "sender", "sender_name", "read", "created_at"]


class ConversationSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    user_name = serializers.CharField()
    user_avatar = serializers.CharField(allow_null=True)
    last_message = serializers.CharField()
    last_message_at = serializers.DateTimeField()
    unread_count = serializers.IntegerField()
