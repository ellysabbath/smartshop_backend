from django.apps import AppConfig


class FirebaseSyncConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "firebase_sync"

    def ready(self):
        from accounts.models import User
        from stores.models import Store
        from staff.models import Salary
        from customers.models import Customer
        from suppliers.models import Supplier
        from products.models import Category, Unit, Product
        from inventory.models import StockLevel, StockMovement
        from sales.models import Order, OrderItem, Payment
        from expenses.models import ExpenseCategory, ExpenseRequest, Expense
        from finance.models import ProfitCalc, TitheOffering
        from reports.models import ProductReport
        from notifications.models import OTP, NotificationLog

        from firebase_sync.signals import register, connect

        register("accounts", "User", "users", User)
        register("stores", "Store", "stores", Store)
        register("staff", "Salary", "staff_salaries", Salary)
        register("customers", "Customer", "customers", Customer)
        register("suppliers", "Supplier", "suppliers", Supplier)
        register("products", "Category", "categories", Category)
        register("products", "Unit", "units", Unit)
        register("products", "Product", "products", Product)
        register("inventory", "StockLevel", "stock_levels", StockLevel)
        register("inventory", "StockMovement", "stock_movements", StockMovement)
        register("sales", "Order", "orders", Order)
        register("sales", "OrderItem", "order_items", OrderItem)
        register("sales", "Payment", "payments", Payment)
        register("expenses", "ExpenseCategory", "expense_categories", ExpenseCategory)
        register("expenses", "ExpenseRequest", "expense_requests", ExpenseRequest)
        register("expenses", "Expense", "expenses", Expense)
        register("finance", "ProfitCalc", "profit_calcs", ProfitCalc)
        register("finance", "TitheOffering", "tithe_offerings", TitheOffering)
        register("reports", "ProductReport", "product_reports", ProductReport)
        register("notifications", "OTP", "otps", OTP)
        register("notifications", "NotificationLog", "notification_logs", NotificationLog)

        connect()