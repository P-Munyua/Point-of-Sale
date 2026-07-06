from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Avg, Max, Min, Q, F, ExpressionWrapper, DecimalField, Case, When
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal

# Add these to your models.py file

class Role(models.Model):
    """User roles with specific permissions"""
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('cashier', 'Cashier'),
        ('inventory', 'Inventory Manager'),
        ('accountant', 'Accountant'),
        ('sales', 'Sales Staff'),
        ('custom', 'Custom Role'),
    )
    
    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Permission flags
    # Dashboard & POS
    can_access_dashboard = models.BooleanField(default=False)
    can_access_pos = models.BooleanField(default=False)
    can_process_sales = models.BooleanField(default=False)
    can_edit_sales = models.BooleanField(default=False)
    can_delete_sales = models.BooleanField(default=False)
    can_view_all_sales = models.BooleanField(default=False)
    can_view_own_sales = models.BooleanField(default=False)
    
    # Products
    can_view_products = models.BooleanField(default=False)
    can_add_products = models.BooleanField(default=False)
    can_edit_products = models.BooleanField(default=False)
    can_delete_products = models.BooleanField(default=False)
    can_import_products = models.BooleanField(default=False)
    
    # Inventory
    can_view_inventory = models.BooleanField(default=False)
    can_manage_stock = models.BooleanField(default=False)
    can_view_reports = models.BooleanField(default=False)
    
    # Purchases
    can_view_purchases = models.BooleanField(default=False)
    can_add_purchases = models.BooleanField(default=False)
    can_edit_purchases = models.BooleanField(default=False)
    can_delete_purchases = models.BooleanField(default=False)
    
    # Customers
    can_view_customers = models.BooleanField(default=False)
    can_add_customers = models.BooleanField(default=False)
    can_edit_customers = models.BooleanField(default=False)
    can_delete_customers = models.BooleanField(default=False)
    
    # Suppliers
    can_view_suppliers = models.BooleanField(default=False)
    can_add_suppliers = models.BooleanField(default=False)
    can_edit_suppliers = models.BooleanField(default=False)
    can_delete_suppliers = models.BooleanField(default=False)
    
    # Reports
    can_view_sales_reports = models.BooleanField(default=False)
    can_view_inventory_reports = models.BooleanField(default=False)
    can_view_profit_reports = models.BooleanField(default=False)
    can_view_customer_reports = models.BooleanField(default=False)
    can_export_reports = models.BooleanField(default=False)
    
    # Settings
    can_manage_settings = models.BooleanField(default=False)
    can_manage_users = models.BooleanField(default=False)
    can_manage_roles = models.BooleanField(default=False)
    
    # Financial
    can_view_financials = models.BooleanField(default=False)
    can_process_refunds = models.BooleanField(default=False)
    can_view_credit_sales = models.BooleanField(default=False)
    can_process_credit_payments = models.BooleanField(default=False)
    
    def __str__(self):
        return self.get_name_display()
    
    def get_permissions_list(self):
        """Return a list of enabled permissions"""
        permissions = []
        for field in self._meta.get_fields():
            if field.name.startswith('can_') and getattr(self, field.name):
                permissions.append(field.name)
        return permissions
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'


class UserProfile(models.Model):
    """Extended user profile with role and additional info"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    id_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # Additional permissions (can override role permissions)
    can_override_role = models.BooleanField(default=False)
    custom_permissions = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.user.username} Profile"
    
    @property
    def full_name(self):
        return self.user.get_full_name()
    
    @property
    def email(self):
        return self.user.email
    
    def has_permission(self, permission_name):
        """Check if user has specific permission"""
        # Check custom permissions first (if override is enabled)
        if self.can_override_role and permission_name in self.custom_permissions:
            return self.custom_permissions.get(permission_name, False)
        
        # Check role permissions
        if self.role:
            return getattr(self.role, permission_name, False)
        
        return False
    
    def get_all_permissions(self):
        """Get all permissions for this user"""
        permissions = {}
        
        # Get role permissions
        if self.role:
            for field in self.role._meta.get_fields():
                if field.name.startswith('can_'):
                    permissions[field.name] = getattr(self.role, field.name, False)
        
        # Override with custom permissions if enabled
        if self.can_override_role:
            for perm, value in self.custom_permissions.items():
                permissions[perm] = value
        
        return permissions
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


class UserActivityLog(models.Model):
    """Log user activities for audit trail"""
    ACTION_TYPES = (
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('print', 'Print'),
        ('error', 'Error'),
    )
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='activities')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username if self.user else 'System'} - {self.action_type} - {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'


class PermissionGroup(models.Model):
    """Group permissions for easier management"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=list)  # List of permission names
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Permission Group'
        verbose_name_plural = 'Permission Groups'

class Company(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    vat_number = models.CharField(max_length=50, blank=True, null=True)
    logo = models.ImageField(upload_to='company/', blank=True, null=True)
    
    def __str__(self):
        return self.name

class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

from django.db import models
from django.core.validators import MinValueValidator

class Product(models.Model):
    name = models.CharField(max_length=100)
    barcode = models.CharField(max_length=50, unique=True, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    # Base prices (used as defaults)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=4)
    selling_price = models.DecimalField(max_digits=50, decimal_places=4)
    least_selling_price = models.DecimalField(max_digits=50, decimal_places=4, default=0)
    wholesale_price = models.DecimalField(max_digits=50, decimal_places=4, default=0)
    wholesale_min_quantity = models.DecimalField(max_digits=50, decimal_places=6, default=0)
    
    # Total quantity across all batches (calculated/updated via triggers)
    quantity = models.DecimalField(max_digits=50, decimal_places=6, default=0)
    reorder_level = models.DecimalField(max_digits=50, decimal_places=6, default=5)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name}"
    
    def save(self, *args, **kwargs):
        if not self.barcode:
            self.barcode = f"PRD{self.id:08d}" if self.id else None
        
        # Ensure least_selling_price is not higher than selling_price
        if self.least_selling_price > self.selling_price:
            self.least_selling_price = self.selling_price
            
        # Ensure least_selling_price is not lower than purchase_price
        if self.least_selling_price < self.purchase_price:
            self.least_selling_price = self.purchase_price
            
        # Ensure wholesale_price is not lower than purchase_price
        if self.wholesale_price < self.purchase_price:
            self.wholesale_price = self.purchase_price
            
        # Ensure wholesale_price is not higher than selling_price
        if self.wholesale_price > self.selling_price:
            self.wholesale_price = self.selling_price
            
        super().save(*args, **kwargs)
    
    def get_available_batches(self, quantity_needed=None):
        """Get available batches sorted by expiry date (FIFO)"""
        batches = self.batches.filter(quantity__gt=0).order_by('expiry_date', 'id')
        
        if quantity_needed:
            # Return only batches that can fulfill the quantity
            available_batches = []
            remaining = quantity_needed
            for batch in batches:
                if remaining <= 0:
                    break
                available_batches.append(batch)
                remaining -= batch.quantity
            return available_batches
        
        return batches
    
    def get_batch_prices(self):
        """Get unique selling prices from batches"""
        return self.batches.filter(is_active=True).values_list('selling_price', flat=True).distinct()
    
    @property
    def profit_margin(self):
        """Calculate average profit margin percentage"""
        if self.purchase_price > 0:
            return ((self.selling_price - self.purchase_price) / self.purchase_price) * 100
        return 0
    
    @property
    def is_low_stock(self):
        """Check if product is below reorder level"""
        return self.quantity <= self.reorder_level

    @property
    def total_profit_by_batch(self):
        """Calculate total profit across all batches"""
        total = Decimal('0')
        for batch in self.batches.all():
            total += batch.total_profit
        return total
    
    def get_batch_profit_details(self):
        """Get detailed profit breakdown by batch"""
        details = []
        for batch in self.batches.all():
            if batch.sold_quantity > 0:
                details.append({
                    'batch': batch,
                    'batch_number': batch.batch_number,
                    'purchase_price': batch.purchase_price,
                    'selling_price': batch.selling_price,
                    'quantity_purchased': batch.quantity + batch.sold_quantity,
                    'quantity_sold': batch.sold_quantity,
                    'quantity_remaining': batch.quantity,
                    'revenue': batch.saleitem_set.aggregate(total=Sum('total'))['total'] or Decimal('0'),
                    'cost': batch.sold_quantity * batch.purchase_price,
                    'profit': batch.total_profit,
                    'profit_margin': batch.profit_margin,
                    'purchase_date': batch.date_received,
                })
        return details
    
    @property
    def current_batch_value(self):
        """Calculate current stock value based on batch purchase prices"""
        total = Decimal('0')
        for batch in self.batches.all():
            total += batch.quantity * batch.purchase_price
        return total
    
    @property
    def average_profit_margin_by_batch(self):
        """Calculate average profit margin weighted by quantity"""
        total_quantity = Decimal('0')
        total_margin_weighted = Decimal('0')
        
        for batch in self.batches.all():
            if batch.sold_quantity > 0:
                total_quantity += batch.sold_quantity
                total_margin_weighted += batch.profit_margin * batch.sold_quantity
        
        if total_quantity > 0:
            return total_margin_weighted / total_quantity
        return Decimal('0')
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'



class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    credit_limit = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    address = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class Sale(models.Model):
    SALE_TYPES = (
        ('retail', 'Retail'),
        ('wholesale', 'Wholesale'),
    )
    
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('card', 'Credit Card'),
        ('bank', 'Bank Transfer'),
        ('credit', 'Credit'),
        ('multiple', 'Multiple Methods'),
    )
    
    sale_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    sale_type = models.CharField(max_length=20, choices=SALE_TYPES, default='retail')
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    subtotal = models.DecimalField(max_digits=50, decimal_places=4, default=0)
    tax = models.DecimalField(max_digits=50, decimal_places=4, default=0)
    discount_amount = models.DecimalField(max_digits=50, decimal_places=4, default=0)
    discount_percent = models.DecimalField(max_digits=50, decimal_places=4, default=0)
    total = models.DecimalField(max_digits=50, decimal_places=4, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount_paid = models.DecimalField(max_digits=50, decimal_places=4, default=0)
    balance = models.DecimalField(max_digits=50, decimal_places=4, default=0)
    mpesa_code = models.CharField(max_length=50, blank=True, null=True)
    cheque_number = models.CharField(max_length=50, blank=True, null=True)
    is_credit = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    is_pending = models.BooleanField(default=False)
    pending_reference = models.CharField(max_length=100, blank=True, null=True)
    payment_details = models.JSONField(blank=True, null=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.sale_number} - {self.total}"
    
    def save(self, *args, **kwargs):
        if not self.sale_number:
            today = timezone.now().date()
            today_sales = Sale.objects.filter(date__date=today)
            next_number = today_sales.aggregate(models.Max('id'))['id__max'] + 1 if today_sales.exists() else 1
            self.sale_number = f"SALE-{today.strftime('%Y%m%d')}-{next_number:04d}"
        super().save(*args, **kwargs)


from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# models.py - Update Purchase model
from django.db import models
from django.db.models import Max
import random
import string

class Purchase(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    invoice_number = models.CharField(max_length=50, unique=True, editable=True)
    date = models.DateTimeField(default=timezone.now)
    subtotal = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    is_paid = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='purchases')
    item_count = models.PositiveIntegerField(default=0)
    
    # Return fields
    is_return = models.BooleanField(default=False)
    original_purchase = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='returns'
    )
    return_reason = models.TextField(blank=True)
    return_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ],
        default='pending'
    )
    
    def __str__(self):
        prefix = "RETURN-" if self.is_return else ""
        return f"{prefix}{self.invoice_number} - {self.supplier.name}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generate invoice number based on date and sequence
            date_str = timezone.now().strftime('%Y%m%d')
            
            # Get the last invoice number for today
            last_invoice = Purchase.objects.filter(
                invoice_number__startswith=f"INV-{date_str}-"
            ).order_by('-invoice_number').first()
            
            if last_invoice:
                try:
                    # Extract the sequence number
                    last_num = int(last_invoice.invoice_number.split('-')[-1])
                    next_num = last_num + 1
                except:
                    next_num = 1
            else:
                next_num = 1
            
            # Format: INV-YYYYMMDD-XXXX
            self.invoice_number = f"INV-{date_str}-{next_num:04d}"
        
        super().save(*args, **kwargs)
    @property
    def total_paid(self):
        """Calculate total amount paid for this purchase"""
        return self.payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.0000')
    
    @property
    def balance_due(self):
        """Calculate remaining balance for this purchase"""
        return max(self.total - self.total_paid, Decimal('0.0000'))
    
    @property
    def payment_status(self):
        """Get payment status"""
        if self.total_paid >= self.total:
            return 'Paid'
        elif self.total_paid > 0:
            return 'Partial'
        else:
            return 'Unpaid'
    
    def update_payment_status(self):
        """Update is_paid based on payments"""
        self.is_paid = self.total_paid >= self.total
        self.save()

    class Meta:
        ordering = ['-date']
        verbose_name = 'Purchase'
        verbose_name_plural = 'Purchases'


# models.py - Add these to your existing models

class Batch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=50)
    quantity = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    expiry_date = models.DateField(blank=True, null=True)
    
    # Purchase details (what we bought at)
    purchase_price = models.DecimalField(max_digits=50, decimal_places=4)
    purchase_date = models.DateField(auto_now_add=True)
    
    # Selling details (what we sell at - can vary per batch)
    selling_price = models.DecimalField(max_digits=50, decimal_places=4, null=True, blank=True)
    wholesale_price = models.DecimalField(max_digits=50, decimal_places=4, null=True, blank=True)
    
    # Link to the purchase that created this batch
    purchase = models.ForeignKey('Purchase', on_delete=models.SET_NULL, null=True, blank=True, related_name='batches')
    purchase_item = models.OneToOneField('PurchaseItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='batch_ref')
    
    date_received = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # Tracking fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.batch_number}"
    
    def save(self, *args, **kwargs):
        # If selling price not set, use product's selling price
        if self.selling_price is None:
            self.selling_price = self.product.selling_price
        
        # If wholesale price not set, use product's wholesale price
        if self.wholesale_price is None:
            self.wholesale_price = self.product.wholesale_price
        
        super().save(*args, **kwargs)
    
    @property
    def profit_margin(self):
        """Calculate profit margin for this batch"""
        if self.purchase_price > 0:
            return ((self.selling_price - self.purchase_price) / self.purchase_price) * 100
        return 0
    
    @property
    def total_value(self):
        """Calculate total value of this batch at purchase price"""
        return self.quantity * self.purchase_price
    
    @property
    def total_selling_value(self):
        """Calculate total potential selling value of this batch"""
        return self.quantity * self.selling_price

    @property
    def total_profit(self):
        """Calculate total profit realized from this batch"""
        from django.db.models import Sum
        sales = self.saleitem_set.all()
        total_revenue = sales.aggregate(total=Sum('total'))['total'] or Decimal('0')
        total_sold_qty = sales.aggregate(total=Sum('quantity'))['total'] or Decimal('0')
        total_cost = total_sold_qty * self.purchase_price
        return total_revenue - total_cost
    
    @property
    def realized_profit(self):
        """Alias for total_profit - profit already realized from sold items"""
        return self.total_profit
    
    @property
    def potential_profit(self):
        """Calculate potential profit from remaining stock"""
        remaining_value = self.quantity * self.selling_price
        remaining_cost = self.quantity * self.purchase_price
        return remaining_value - remaining_cost
    
    @property
    def sold_quantity(self):
        """Get total quantity sold from this batch"""
        from django.db.models import Sum
        return self.saleitem_set.aggregate(total=Sum('quantity'))['total'] or Decimal('0')
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage"""
        if self.purchase_price > 0:
            return ((self.selling_price - self.purchase_price) / self.purchase_price) * 100
        return 0
    
    @property
    def days_in_stock(self):
        """Calculate how many days this batch has been in stock"""
        if self.date_received:
            return (timezone.now().date() - self.date_received).days
        return 0
    
    class Meta:
        ordering = ['expiry_date', 'batch_number']

    


class PurchaseItem(models.Model):
    purchase = models.ForeignKey('Purchase', on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    
    # Each purchase item creates ONE batch (one-to-one relationship)
    batch = models.OneToOneField(Batch, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_item_source')
    
    quantity = models.DecimalField(max_digits=15, decimal_places=5, default=1) 
    price = models.DecimalField(max_digits=10, decimal_places=6)  # Purchase price
    total = models.DecimalField(max_digits=10, decimal_places=4)
    
    # Track if this item has been fully sold
    remaining_quantity = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    is_fully_sold = models.BooleanField(default=False)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.product.name if self.product else 'Unknown'} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        # Set remaining quantity on first save
        if not self.pk:
            self.remaining_quantity = self.quantity
            
        super().save(*args, **kwargs)
        
        # Create batch if this is a new purchase item and batch doesn't exist
        if not self.batch and self.product and self.quantity > 0:
            batch = Batch.objects.create(
                product=self.product,
                batch_number=f"BATCH-{timezone.now().strftime('%Y%m%d')}-{self.product.id}-{self.id}",
                quantity=self.quantity,
                purchase_price=self.price,
                selling_price=self.product.selling_price,
                wholesale_price=self.product.wholesale_price,
                date_received=timezone.now().date(),
                purchase=self.purchase,
                purchase_item=self,
                is_active=True
            )
            self.batch = batch
            self.save(update_fields=['batch'])
    
    def update_sold_status(self, quantity_sold):
        """Update remaining quantity when items are sold"""
        self.remaining_quantity -= quantity_sold
        if self.remaining_quantity <= 0:
            self.remaining_quantity = Decimal('0')
            self.is_fully_sold = True
        self.save()
    
    @property
    def sold_quantity(self):
        """Calculate total quantity sold from this purchase item"""
        return self.quantity - self.remaining_quantity
    
    @property
    def total_revenue(self):
        """Calculate total revenue from sales of this purchase item"""
        from django.db.models import Sum
        total = SaleItem.objects.filter(
            batch=self.batch
        ).aggregate(total=Sum('total'))['total'] or Decimal('0')
        return total
    
    @property
    def total_profit(self):
        """Calculate total profit from sales of this purchase item"""
        return self.total_revenue - (self.sold_quantity * self.price)
    
    class Meta:
        ordering = ['-created_at']


# models.py - Update SaleItem model

class SaleItem(models.Model):
    sale = models.ForeignKey('Sale', on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    
    # Link to the specific batch this item came from (CRITICAL for profit tracking)
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Link to the purchase item this came from (for direct tracking)
    purchase_item = models.ForeignKey(PurchaseItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='sale_items')
    
    quantity = models.DecimalField(max_digits=10, decimal_places=5, default=1)
    price = models.DecimalField(max_digits=10, decimal_places=4)  # Selling price at time of sale
    purchase_price = models.DecimalField(max_digits=10, decimal_places=4, default=0)  # Store the purchase price from batch
    discount_amount = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=4)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product.name if self.product else 'Unknown'} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        # If this is a new item and we have a batch, store the purchase price
        if not self.pk:
            if self.batch:
                self.purchase_price = self.batch.purchase_price
                # Try to find the purchase item
                if hasattr(self.batch, 'purchase_item_source'):
                    self.purchase_item = self.batch.purchase_item_source
                    
                    # Update the purchase item's remaining quantity
                    if self.purchase_item:
                        self.purchase_item.update_sold_status(self.quantity)
        
        super().save(*args, **kwargs)

    @property
    def profit(self):
        """Calculate profit for this sale item"""
        try:
            cost = self.purchase_price * self.quantity
            return self.total - cost
        except:
            return Decimal('0.00')
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage"""
        try:
            if self.total > 0:
                cost = self.purchase_price * self.quantity
                return ((self.total - cost) / self.total) * 100
        except:
            return Decimal('0.00')
        return Decimal('0.00')
    
    @property
    def purchase_item_details(self):
        """Get details of the original purchase item"""
        if self.purchase_item:
            return {
                'purchase_id': self.purchase_item.purchase_id,
                'purchase_date': self.purchase_item.purchase.date,
                'invoice_number': self.purchase_item.purchase.invoice_number,
                'supplier': self.purchase_item.purchase.supplier.name,
                'original_quantity': self.purchase_item.quantity,
                'purchase_price': self.purchase_item.price,
            }
        return None


# models.py - Update PendingPurchase model
class PendingPurchase(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=50, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    data = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Pending Purchase #{self.id} - {self.supplier.name}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generate temporary invoice number
            date_str = timezone.now().strftime('%Y%m%d')
            
            # Get count of pending purchases today
            today_pending = PendingPurchase.objects.filter(
                created_at__date=timezone.now().date()
            ).count()
            
            next_num = today_pending + 1
            self.invoice_number = f"PEND-{date_str}-{next_num:04d}"
        
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Pending Purchase'
        verbose_name_plural = 'Pending Purchases'

        
    
# In models.py - Update StockJournal model
class StockJournal(models.Model):
    # Remove MOVEMENT_TYPES from here
    movement_number = models.CharField(max_length=50, unique=True, editable=False)
    # Remove movement_type field from here
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(auto_now_add=True)
    total_items = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.movement_number}"
    
    def save(self, *args, **kwargs):
        if not self.movement_number:
            today = timezone.now().date()
            today_movements = StockJournal.objects.filter(date__date=today)
            next_number = today_movements.aggregate(models.Max('id'))['id__max'] + 1 if today_movements.exists() else 1
            self.movement_number = f"MOV-{today.strftime('%Y%m%d')}-{next_number:04d}"
        super().save(*args, **kwargs)



class StockJournalItem(models.Model):
    MOVEMENT_TYPES = (
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
        ('missing', 'Missing'),
        ('damaged', 'Damaged'),
        ('broken', 'Broken'),
        ('expired', 'Expired'),
        ('adjustment', 'Adjustment'),
        ('transfer', 'Transfer'),
    )
    
    journal = models.ForeignKey(StockJournal, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=4)
    current_stock = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    new_stock = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.product.name if self.product else 'Unknown'} - {self.get_movement_type_display()} - {self.quantity}"

class Expense(models.Model):
    CATEGORIES = (
        ('rent', 'Rent'),
        ('salaries', 'Salaries'),
        ('utilities', 'Utilities'),
        ('transport', 'Transport'),
        ('other', 'Other'),
    )
    
    date = models.DateField()
    category = models.CharField(max_length=20, choices=CATEGORIES)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=4)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.date} - {self.description} - {self.amount}"

# models.py - Update SupplierPayment model
class SupplierPayment(models.Model):
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('bank', 'Bank Transfer'),
        ('cheque', 'Cheque'),
    )
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    purchase = models.ForeignKey(Purchase, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=4)
    date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True, null=True)
    is_partial = models.BooleanField(default=False)  # Add this field
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=4, default=0)  # Add this field
    
    def __str__(self):
        return f"{self.supplier.name} - {self.amount}"
    
    class Meta:
        ordering = ['-date']

class Discount(models.Model):
    DISCOUNT_TYPES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    )
    
    name = models.CharField(max_length=100)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=4)
    start_date = models.DateField()
    end_date = models.DateField()
    products = models.ManyToManyField(Product, blank=True)
    categories = models.ManyToManyField(Category, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_discount_type_display()})"



from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class PendingSale(models.Model):
    data = models.JSONField()  # Stores sale items, customer, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    customer = models.ForeignKey('Customer', on_delete=models.SET_NULL, null=True, blank=True)

    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    def __str__(self):
        return f"Pending Sale #{self.id}"

class CompanyPrice(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=4)
    
    class Meta:
        unique_together = ('company', 'product')
    
    def __str__(self):
        return f"{self.company.name} - {self.product.name}"

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    id_number = models.CharField(max_length=20)
    position = models.CharField(max_length=50)
    
    def __str__(self):
        return self.user.get_full_name() or self.user.username
    



class SupplierReturn(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    reason = models.TextField()
    return_date = models.DateField(auto_now_add=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed')
    ], default='pending')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Return #{self.id} - {self.product.name}"  




# models.py
from django.db import models
from django.contrib.auth.models import User

class Receipt(models.Model):
    RECEIPT_TYPES = (
        ('sale', 'Sale Receipt'),
        ('refund', 'Refund Receipt'),
        ('credit', 'Credit Note'),
    )
    
    receipt_number = models.CharField(max_length=50, unique=True)
    receipt_type = models.CharField(max_length=10, choices=RECEIPT_TYPES)
    sale = models.ForeignKey('Sale', on_delete=models.CASCADE, null=True, blank=True)
    content = models.JSONField()  # Stores the receipt data in JSON format
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_printed = models.BooleanField(default=False)
    printed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.receipt_number} ({self.get_receipt_type_display()})"
    




class CustomerPayment(models.Model):
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('card', 'Credit Card'),
        ('cheque', 'Cheque'),
    )
    
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='payments')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)  # Made optional
    amount = models.DecimalField(max_digits=10, decimal_places=4)
    date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Payment #{self.id} - {self.amount}"




# models.py
class CreditSaleItem(models.Model):
    """Track individual product payments in credit sales"""
    sale_item = models.ForeignKey(SaleItem, on_delete=models.CASCADE, related_name='credit_payments')
    quantity_credited = models.DecimalField(max_digits=10, decimal_places=5, default=0)
    original_quantity = models.DecimalField(max_digits=10, decimal_places=5, default=0)
    quantity_paid = models.DecimalField(max_digits=10, decimal_places=5, default=0)
    remaining_quantity = models.DecimalField(max_digits=10, decimal_places=5, default=0)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    balance_amount = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    is_fully_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Calculate remaining quantity
        self.remaining_quantity = self.quantity_credited - self.quantity_paid
        self.balance_amount = self.total_amount - self.amount_paid
        self.is_fully_paid = self.remaining_quantity <= Decimal('0.00001')
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.sale_item.product.name} - Paid: {self.quantity_paid}/{self.quantity_credited}"

class CreditPayment(models.Model):
    """Track credit payments at the sale level"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='credit_payments')
    amount = models.DecimalField(max_digits=10, decimal_places=4)
    payment_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=20, choices=Sale.PAYMENT_METHODS, default='cash')
    reference = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Payment for Sale #{self.sale.sale_number} - {self.amount}"
    
    class Meta:
        ordering = ['-payment_date']

class CreditPaymentDetail(models.Model):
    """Track which products were paid for in each payment"""
    credit_payment = models.ForeignKey(CreditPayment, on_delete=models.CASCADE, related_name='details')
    credit_sale_item = models.ForeignKey(CreditSaleItem, on_delete=models.CASCADE, related_name='payment_details')
    quantity_paid = models.DecimalField(max_digits=10, decimal_places=5, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    
    def __str__(self):
        return f"{self.credit_sale_item.sale_item.product.name} - {self.quantity_paid} units"