from rest_framework import serializers
from .models import Order, OrderItem, Message
from products.models import Product


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    subtotal = serializers.IntegerField(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "quantity", "unit_price", "subtotal"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shop_name = serializers.CharField(source="shop.name", read_only=True)
    buyer_name = serializers.CharField(source="buyer.get_full_name", read_only=True)
    agent_name = serializers.CharField(source="agent.get_full_name", read_only=True)

    class Meta:
        model = Order
        fields = [
            "order_id", "status", "city", "delivery_address", "total",
            "escrow_released", "placed_at", "updated_at",
            "shop_name", "buyer_name", "agent_name", "items",
        ]
        read_only_fields = ["order_id", "total", "escrow_released", "placed_at", "updated_at",
                            "shop_name", "buyer_name", "agent_name"]


class CreateOrderSerializer(serializers.Serializer):
    """Used by buyers to place an order."""
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
        return items

    def create(self, validated_data):
        from shops.models import Shop
        buyer = self.context["request"].user
        shop = Shop.objects.get(id=validated_data["shop_id"])
        total = 0
        order_items = []
        for item in validated_data["items"]:
            product = Product.objects.get(id=item["product_id"])
            qty = int(item["quantity"])
            unit_price = product.price
            total += qty * unit_price
            order_items.append(OrderItem(product=product, quantity=qty, unit_price=unit_price))

        order = Order.objects.create(
            buyer=buyer, shop=shop,
            city=validated_data["city"],
            delivery_address=validated_data["delivery_address"],
            total=total,
        )
        for oi in order_items:
            oi.order = order
        OrderItem.objects.bulk_create(order_items)
        return order


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.get_full_name", read_only=True)

    class Meta:
        model = Message
        fields = ["id", "sender", "sender_name", "recipient", "body", "read", "created_at"]
        read_only_fields = ["id", "sender", "sender_name", "read", "created_at"]
