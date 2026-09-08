# pos/signals.py
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.auth.models import User
from .models import (
    Product, Category, Customer, Supplier, Sale, Purchase, 
    Expense, Discount, Batch, Company, UserProfile, Role,
    SupplierPayment, CustomerPayment, PendingSale, PendingPurchase,
    Receipt, StockJournal, StockJournalItem
)
from .logger import log_create, log_update, log_delete, log_login, log_logout
import sys

# Store request in thread local for signals
from threading import local
_request_local = local()

class RequestMiddleware:
    """Middleware to capture request object for signals"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _request_local.request = request
        response = self.get_response(request)
        return response

def get_current_request():
    """Get the current request from thread local storage"""
    return getattr(_request_local, 'request', None)

def get_current_user():
    """Get the current user from thread local storage"""
    request = get_current_request()
    if request and hasattr(request, 'user'):
        return request.user
    return None


# ============== MODEL SIGNALS ==============

# PRODUCT SIGNALS
@receiver(post_save, sender=Product)
def log_product_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        if created:
            log_create(user, instance, request, f'Added product: {instance.name}')
        else:
            log_update(user, instance, request, f'Updated product: {instance.name}')


@receiver(pre_delete, sender=Product)
def log_product_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        log_delete(user, instance, request, f'Deleted product: {instance.name}')


# CUSTOMER SIGNALS
@receiver(post_save, sender=Customer)
def log_customer_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        if created:
            log_create(user, instance, request, f'Added customer: {instance.name}')
        else:
            log_update(user, instance, request, f'Updated customer: {instance.name}')


@receiver(pre_delete, sender=Customer)
def log_customer_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        log_delete(user, instance, request, f'Deleted customer: {instance.name}')


# SUPPLIER SIGNALS
@receiver(post_save, sender=Supplier)
def log_supplier_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        if created:
            log_create(user, instance, request, f'Added supplier: {instance.name}')
        else:
            log_update(user, instance, request, f'Updated supplier: {instance.name}')


@receiver(pre_delete, sender=Supplier)
def log_supplier_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        log_delete(user, instance, request, f'Deleted supplier: {instance.name}')


# SALE SIGNALS
@receiver(post_save, sender=Sale)
def log_sale_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        if created:
            item_count = instance.items.count()
            log_create(user, instance, request, 
                      f'Created sale #{instance.sale_number} with {item_count} items - Total: {instance.total}')
        else:
            log_update(user, instance, request, 
                      f'Updated sale #{instance.sale_number} - Total: {instance.total}')


@receiver(pre_delete, sender=Sale)
def log_sale_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        log_delete(user, instance, request, f'Deleted sale #{instance.sale_number}')


# PURCHASE SIGNALS
@receiver(post_save, sender=Purchase)
def log_purchase_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        if created:
            log_create(user, instance, request, 
                      f'Created purchase #{instance.invoice_number} from {instance.supplier.name} - Total: {instance.total}')
        else:
            log_update(user, instance, request, 
                      f'Updated purchase #{instance.invoice_number} from {instance.supplier.name}')


@receiver(pre_delete, sender=Purchase)
def log_purchase_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        log_delete(user, instance, request, f'Deleted purchase #{instance.invoice_number}')


# EXPENSE SIGNALS
@receiver(post_save, sender=Expense)
def log_expense_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        if created:
            log_create(user, instance, request, 
                      f'Added expense: {instance.description} ({instance.category}) - {instance.amount}')
        else:
            log_update(user, instance, request, 
                      f'Updated expense: {instance.description}')


@receiver(pre_delete, sender=Expense)
def log_expense_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        log_delete(user, instance, request, f'Deleted expense: {instance.description}')


# BATCH SIGNALS
@receiver(post_save, sender=Batch)
def log_batch_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        if created:
            log_create(user, instance, request, 
                      f'Created batch: {instance.batch_number} for {instance.product.name} - Qty: {instance.quantity}')
        else:
            log_update(user, instance, request, 
                      f'Updated batch: {instance.batch_number} for {instance.product.name}')


@receiver(pre_delete, sender=Batch)
def log_batch_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        log_delete(user, instance, request, f'Deleted batch: {instance.batch_number}')


# CATEGORY SIGNALS
@receiver(post_save, sender=Category)
def log_category_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        if created:
            log_create(user, instance, request, f'Added category: {instance.name}')
        else:
            log_update(user, instance, request, f'Updated category: {instance.name}')


@receiver(pre_delete, sender=Category)
def log_category_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        log_delete(user, instance, request, f'Deleted category: {instance.name}')


# DISCOUNT SIGNALS
@receiver(post_save, sender=Discount)
def log_discount_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        if created:
            log_create(user, instance, request, 
                      f'Added discount: {instance.name} ({instance.discount_type}) - {instance.amount}')
        else:
            log_update(user, instance, request, f'Updated discount: {instance.name}')


@receiver(pre_delete, sender=Discount)
def log_discount_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        log_delete(user, instance, request, f'Deleted discount: {instance.name}')


# SUPPLIER PAYMENT SIGNALS
@receiver(post_save, sender=SupplierPayment)
def log_supplier_payment_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        if created:
            log_create(user, instance, request, 
                      f'Recorded supplier payment: {instance.supplier.name} - {instance.amount}')
        else:
            log_update(user, instance, request, 
                      f'Updated supplier payment: {instance.supplier.name} - {instance.amount}')


# CUSTOMER PAYMENT SIGNALS
@receiver(post_save, sender=CustomerPayment)
def log_customer_payment_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        if created:
            customer_name = instance.customer.name if instance.customer else 'Walk-in'
            log_create(user, instance, request, 
                      f'Recorded customer payment: {customer_name} - {instance.amount}')


# USER PROFILE SIGNALS
@receiver(post_save, sender=UserProfile)
def log_user_profile_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        if created:
            log_create(user, instance, request, 
                      f'Created profile for user: {instance.user.username}')
        else:
            log_update(user, instance, request, 
                      f'Updated profile for user: {instance.user.username}')


# ROLE SIGNALS
@receiver(post_save, sender=Role)
def log_role_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        if created:
            log_create(user, instance, request, f'Created role: {instance.get_name_display()}')
        else:
            log_update(user, instance, request, f'Updated role: {instance.get_name_display()}')


@receiver(pre_delete, sender=Role)
def log_role_delete(sender, instance, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        log_delete(user, instance, request, f'Deleted role: {instance.get_name_display()}')


# PENDING SALE SIGNALS
@receiver(post_save, sender=PendingSale)
def log_pending_sale_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        if created:
            log_create(user, instance, request, f'Created pending sale with {len(instance.data.get("items", []))} items')
        else:
            log_update(user, instance, request, f'Updated pending sale with {len(instance.data.get("items", []))} items')


# RECEIPT SIGNALS
@receiver(post_save, sender=Receipt)
def log_receipt_save(sender, instance, created, **kwargs):
    request = get_current_request()
    user = get_current_user()
    if user and user.is_authenticated:
        if created:
            log_create(user, instance, request, f'Generated receipt: {instance.receipt_number}')


# ============== AUTHENTICATION SIGNALS ==============

@receiver(user_logged_in)
def log_user_logged_in(sender, request, user, **kwargs):
    log_login(user, request)


@receiver(user_logged_out)
def log_user_logged_out(sender, request, user, **kwargs):
    if user:
        log_logout(user, request)