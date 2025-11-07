from django.contrib import admin
from .models import *

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'selling_price', 'quantity', 'reorder_level')
    list_filter = ('category', 'supplier')
    search_fields = ('name', 'barcode')

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('sale_number', 'date', 'customer', 'total', 'payment_method', 'user')
    list_filter = ('date', 'payment_method', 'is_credit')
    search_fields = ('sale_number', 'customer__name')

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'date', 'supplier', 'total', 'user')
    list_filter = ('date', 'supplier')
    search_fields = ('invoice_number', 'supplier__name')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'credit_limit', 'balance')
    search_fields = ('name', 'phone', 'email')

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email')
    search_fields = ('name', 'contact_person', 'phone')

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('date', 'category', 'description', 'amount', 'user')
    list_filter = ('date', 'category')
    search_fields = ('description',)


from django.contrib import admin
from .models import StockJournal

@admin.register(StockJournal)
class StockJournalAdmin(admin.ModelAdmin):
    list_display = ('date', 'product', 'batch', 'movement_type', 'quantity', 'user')
    list_filter = ('movement_type', 'date', 'user')
    search_fields = ('product__name', 'batch__batch_number', 'reference')


admin.site.register(Category)
admin.site.register(PendingPurchase)

admin.site.register(Employee)
admin.site.register(PendingSale)




