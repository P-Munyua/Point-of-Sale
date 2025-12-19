from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import datetime, timedelta

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
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    least_selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    wholesale_min_quantity = models.IntegerField(default=0, blank=True, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reorder_level = models.IntegerField(default=5)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)  # Add this line
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - KES {self.selling_price}"
    
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
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage"""
        if self.purchase_price > 0:
            return ((self.selling_price - self.purchase_price) / self.purchase_price) * 100
        return 0
    
    @property
    def is_low_stock(self):
        """Check if product is below reorder level"""
        return self.quantity <= self.reorder_level
    
    @property
    def is_below_minimum_price(self):
        """Check if selling price is below least selling price"""
        return self.selling_price < self.least_selling_price
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

class Batch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=50)
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    expiry_date = models.DateField(blank=True, null=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    date_received = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.batch_number}"

class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
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
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
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

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def profit(self):
        """Calculate profit for this sale item"""
        try:
            cost = self.product.purchase_price * self.quantity
            return self.total - cost
        except:
            return Decimal('0.00')
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage"""
        try:
            if self.total > 0:
                cost = self.product.purchase_price * self.quantity
                return ((self.total - cost) / self.total) * 100
        except:
            return Decimal('0.00')
        return Decimal('0.00')

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
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
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
    
    class Meta:
        ordering = ['-date']
        verbose_name = 'Purchase'
        verbose_name_plural = 'Purchases'


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"



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
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
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
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    new_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
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
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.date} - {self.description} - {self.amount}"

class SupplierPayment(models.Model):
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('bank', 'Bank Transfer'),
        ('cheque', 'Cheque'),
    )
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    purchase = models.ForeignKey(Purchase, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.supplier.name} - {self.amount}"

class Discount(models.Model):
    DISCOUNT_TYPES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    )
    
    name = models.CharField(max_length=100)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
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
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
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
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
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
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Payment #{self.id} - {self.amount}"