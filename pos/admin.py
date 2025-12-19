from django.contrib import admin
from .models import *

from django.contrib import admin
from django.db.models import Q
from .models import Product, Category, Supplier

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'purchase_price', 'selling_price', 
                   'least_selling_price', 'wholesale_price', 'quantity', 'reorder_level', 'is_active')
    list_filter = ('category', 'supplier', 'is_active')
    search_fields = ('name', 'barcode', 'category__name', 'supplier__name')
    
    # Add filters for price ranges
    list_filter = ('category', 'supplier', 'is_active')
    
    # Enable editing in list view
    list_editable = ('selling_price', 'least_selling_price', 'wholesale_price', 'quantity', 'reorder_level')
    
    # Fields to display in the detail view
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'barcode', 'category', 'supplier', 'image', 'description', 'is_active')
        }),
        ('Pricing Information', {
            'fields': ('purchase_price', 'selling_price', 'least_selling_price', 
                      'wholesale_price', 'wholesale_min_quantity')
        }),
        ('Inventory Information', {
            'fields': ('quantity', 'reorder_level')
        }),
    )
    
    # Custom search that includes category and supplier names
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        
        # Also search in category and supplier names
        if search_term:
            category_matches = Category.objects.filter(name__icontains=search_term)
            supplier_matches = Supplier.objects.filter(name__icontains=search_term)
            
            # Add products with matching category or supplier
            queryset |= self.model.objects.filter(
                Q(category__in=category_matches) | 
                Q(supplier__in=supplier_matches)
            )
        
        return queryset, use_distinct
    
    # Add actions
    actions = ['activate_products', 'deactivate_products']
    
    def activate_products(self, request, queryset):
        queryset.update(is_active=True)
    activate_products.short_description = "Activate selected products"
    
    def deactivate_products(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_products.short_description = "Deactivate selected products"

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

from django.contrib import admin
# In admin.py - Update or add this
from django.contrib import admin
from .models import (
    Product, Category, Customer, Supplier, Sale, SaleItem,
    Purchase, PurchaseItem, Expense, Batch, Discount, Company,
    CompanyPrice, SupplierPayment, PendingSale, PendingPurchase,
    CustomerPayment, StockJournal, StockJournalItem
)

# ... your other admin classes ...

# First, define the inline
class StockJournalItemInline(admin.TabularInline):
    model = StockJournalItem
    extra = 0
    fields = ['product', 'batch', 'movement_type', 'quantity', 'current_stock', 'new_stock', 'notes']
    readonly_fields = ['current_stock', 'new_stock']
    classes = ['collapse']

# Then register StockJournalAdmin
@admin.register(StockJournal)
class StockJournalAdmin(admin.ModelAdmin):
    list_display = ['movement_number', 'reference', 'user', 'date', 'total_items']
    list_filter = ['date']  # Removed movement_type since it's not in the model anymore
    search_fields = ['movement_number', 'reference', 'notes']
    readonly_fields = ['movement_number', 'date', 'total_items']
    inlines = [StockJournalItemInline]  # Now this is defined
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('items')

@admin.register(StockJournalItem)
class StockJournalItemAdmin(admin.ModelAdmin):
    list_display = ['product', 'batch', 'movement_type', 'quantity', 'current_stock', 'new_stock', 'journal', 'notes']
    list_filter = ['movement_type', 'journal']  # Removed 'journal__movement_type'
    search_fields = ['product__name', 'batch__batch_number', 'notes']
    readonly_fields = ['current_stock', 'new_stock']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'batch', 'journal')


admin.site.register(Category)
admin.site.register(PendingPurchase)

admin.site.register(Employee)
admin.site.register(PendingSale)




