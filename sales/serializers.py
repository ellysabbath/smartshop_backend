from rest_framework import serializers
from .models import Order, OrderItem, Payment


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "order", "product", "product_name",
                  "quantity", "unit_price", "unit_cost", "subtotal"]
        read_only_fields = ["id", "order", "subtotal"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "order", "method", "phone", "reference",
                  "amount", "status", "confirmed_by", "confirmed_at"]
        read_only_fields = ["id", "order", "status",
                            "confirmed_by", "confirmed_at"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.full_name",
                                          read_only=True)

    class Meta:
        model = Order
        fields = ["id", "customer", "customer_name", "store",
                  "order_date", "status", "subtotal", "discount",
                  "total", "created_by", "items", "payments"]
        read_only_fields = ["id", "order_date", "status",
                            "subtotal", "total", "created_by",
                            "items", "payments"]