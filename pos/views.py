
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, Q, ExpressionWrapper, DecimalField
from django.db import transaction
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST, require_GET
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json
import csv
from django.urls import reverse
from django.urls.base import reverse
# Add these imports at the top
from django.db.models.functions import ExtractHour, TruncHour, TruncMonth
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import reverse
from io import StringIO
from django.db.models.functions import TruncDate, TruncMonth
from django.contrib import messages
from django.template.loader import render_to_string
from django.http import HttpResponseBadRequest
import pandas as pd
# Add these imports at the top of views.py
from django.db.models import Case, When, Value, Sum, Count, Max, Min, Avg, Q, F
from django.db.models.functions import ExtractHour, TruncHour, TruncMonth, TruncDate
from django.db.models import DecimalField


from .models import (
    Product, Category, Customer, Supplier,
    Sale, SaleItem, Purchase, PurchaseItem,
    Expense, Batch, Discount, Company, CompanyPrice,
    SupplierPayment, PendingSale, PendingPurchase, CustomerPayment
)
from .forms import (
    ProductForm, CustomerForm, SupplierForm, PurchaseForm, 
    ExpenseForm, BatchForm, DiscountForm, CompanyPriceForm,
    BulkUploadForm, PurchaseReturnForm
)

# ============== Dashboard Views ==============
@login_required
def dashboard(request):
    # Today's sales data
    today = timezone.now().date()
    today_sales = Sale.objects.filter(
        date__date=today,
        is_completed=True
    )
    
    # Monthly sales data
    monthly_sales = Sale.objects.filter(
        date__month=timezone.now().month,
        date__year=timezone.now().year,
        is_completed=True
    )
    
    # Calculate totals
    today_total = today_sales.aggregate(total=Sum('total'))['total'] or 0
    monthly_total = monthly_sales.aggregate(total=Sum('total'))['total'] or 0
    
    # Low stock items
    low_stock_count = Product.objects.filter(
        quantity__lte=F('reorder_level'),
        is_active=True
    ).count()
    
    # Recent sales
    recent_sales = Sale.objects.filter(
        is_completed=True
    ).order_by('-date')[:5]
    
    # Recent activities (placeholder - implement as needed)
    recent_activities = []
    
    context = {
        'today_sales': today_total,
        'monthly_sales': monthly_total,
        'low_stock_count': low_stock_count,
        'recent_sales': recent_sales,
        'recent_activities': recent_activities
    }
    return render(request, 'pos/dashboard.html', context)

# ============== POS & Sales Views ==============
@login_required
def pos(request):
    company = Company.objects.first()
    products = Product.objects.filter(quantity__gt=0, is_active=True).order_by('name')
    categories = Category.objects.all()
    customers = Customer.objects.all().order_by('name')
    
    # Get currently valid discounts
    today = timezone.now().date()
    discounts = Discount.objects.filter(
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    )
    
    # Generate temporary display number
    today_sales_count = Sale.objects.filter(
        date__date=today
    ).count()
    display_number = f"SALE-{timezone.now().strftime('%Y%m%d')}-{today_sales_count + 1:04d}"
    
    context = {
        'products': products,
        'categories': categories,
        'customers': customers,
        'discounts': discounts,
        'display_number': display_number,
        'company': company
    }
    return render(request, 'pos/pos.html', context)

from django.db import transaction, OperationalError
import time
from django.db.utils import OperationalError

@login_required
@require_POST
def process_sale(request):
    max_retries = 3
    retry_delay = 0.1  # seconds
    
    for attempt in range(max_retries):
        try:
            with transaction.atomic():
                data = json.loads(request.POST.get('sale_data'))
                pending_sale_id = request.POST.get('pending_sale_id')
                
                company = Company.objects.first() or Company.objects.create(name="Default Company")
                
                # Create sale
                sale = Sale(
                    customer_id=data.get('customer_id'),
                    user=request.user,
                    sale_type=data.get('sale_type', 'retail'),
                    subtotal=Decimal(data['subtotal']),
                    discount_amount=Decimal(data.get('discount_amount', 0)),
                    discount_percent=Decimal(data.get('discount_percent', 0)),
                    total=Decimal(data['total']),
                    payment_method=data['payment_method'],
                    amount_paid=Decimal(data['amount_paid']),
                    balance=max(Decimal(data['total']) - Decimal(data['amount_paid']), Decimal(0)),
                    is_credit=data.get('is_credit', False),
                    is_completed=True
                )
                
                # Handle payment details
                payment_details = data.get('payment_details', {})
                sale.mpesa_amount = Decimal(payment_details.get('mpesa', 0))
                sale.cash_amount = Decimal(payment_details.get('cash', 0))
                sale.card_amount = Decimal(payment_details.get('card', 0))
                sale.cheque_amount = Decimal(payment_details.get('cheque', 0))
                sale.mpesa_code = payment_details.get('mpesa_code', '')
                sale.cheque_number = payment_details.get('cheque_number', '')
                
                sale.save()
                
                # Create sale items and update inventory
                for item in data['items']:
                    product = Product.objects.select_for_update().get(id=item['id'])
                    batch = None
                    
                    if item.get('batch_id'):
                        batch = Batch.objects.select_for_update().get(id=item['batch_id'])
                    
                    # Convert quantity to Decimal
                    quantity = Decimal(str(item['quantity']))
                    
                    SaleItem.objects.create(
                        sale=sale,
                        product=product,
                        batch=batch,
                        quantity=quantity,  # Now accepts decimal values
                        price=Decimal(item['price']),
                        discount_amount=Decimal(item.get('discount_amount', 0)),
                        discount_percent=Decimal(item.get('discount_percent', 0)),
                        total=Decimal(item['total'])
                    )
                    
                    # Update product quantity with row locking
                    product.quantity -= quantity
                    if product.quantity < 0:
                        product.quantity = Decimal('0')  # Prevent negative quantities
                    product.save()
                    
                    if batch:
                        batch.quantity -= quantity
                        if batch.quantity < 0:
                            batch.quantity = Decimal('0')  # Prevent negative quantities
                        batch.save()
                
                # Update customer balance if credit sale
                if sale.is_credit and sale.customer:
                    customer = Customer.objects.select_for_update().get(id=sale.customer.id)
                    customer.balance += sale.balance
                    customer.save()
                
                # Delete pending sale if it exists
                if pending_sale_id:
                    try:
                        pending_sale = PendingSale.objects.filter(id=pending_sale_id, user=request.user).first()
                        if pending_sale:
                            pending_sale.delete()
                    except PendingSale.DoesNotExist:
                        pass
                
                # Prepare receipt data
                receipt = {
                    'company': {
                        'name': company.name,
                        'address': company.address or '',
                        'phone': company.phone or '',
                        'vat_number': company.vat_number or '',
                    },
                    'sale_number': sale.sale_number,
                    'date': sale.date.strftime('%d/%m/%Y %H:%M'),
                    'customer': sale.customer.name if sale.customer else 'Walk-in Customer',
                    'payment_method': sale.get_payment_method_display(),
                    'payment_details': {
                        'mpesa': str(sale.mpesa_amount),
                        'cash': str(sale.cash_amount),
                        'card': str(sale.card_amount),
                        'cheque': str(sale.cheque_amount)
                    },
                    'items': [{
                        'name': item.product.name,
                        'quantity': float(item.quantity),  # Convert to float for JSON serialization
                        'price': str(item.price),
                        'total': str(item.total),
                        'batch_number': item.batch.batch_number if item.batch else ''
                    } for item in sale.items.all()],
                    'subtotal': str(sale.subtotal),
                    'discount': str(sale.discount_amount),
                    'total': str(sale.total),
                    'amount_paid': str(sale.amount_paid),
                    'change': str(max(sale.amount_paid - sale.total, Decimal(0))),
                    'balance': str(sale.balance)
                }
                
                return JsonResponse({
                    'success': True,
                    'receipt': receipt,
                    'sale_id': sale.id,
                    'pending_sale_deleted': bool(pending_sale_id)
                })
        
        except OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            raise
    
    return JsonResponse({
        'success': False,
        'message': 'Database is locked. Please try again.'
    }, status=500)

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import transaction
from decimal import Decimal
import json
from .models import PendingSale, Sale, SaleItem, Product, Batch, Customer, Company


# pos/views.py
@login_required
@require_POST
@login_required
@require_POST
def save_pending_sale(request):
    try:
        # Get raw POST data
        data = json.loads(request.body.decode('utf-8'))
        sale_data = data.get('sale_data')
        
        if not sale_data:
            return JsonResponse({
                'success': False,
                'message': 'No sale data provided'
            }, status=400)
        
        # Validate required fields
        required_fields = ['items', 'total']
        for field in required_fields:
            if field not in sale_data:
                return JsonResponse({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }, status=400)
        
        # Ensure items is a list
        if not isinstance(sale_data['items'], list):
            return JsonResponse({
                'success': False,
                'message': 'Items must be an array'
            }, status=400)
        
        pending_sale = PendingSale(
            user=request.user,
            customer_id=sale_data.get('customer_id'),
            data=sale_data
        )
        pending_sale.save()
        
        return JsonResponse({
            'success': True,
            'pending_sale_id': pending_sale.id,
            'message': 'Sale saved as pending successfully'
        })
    
    except json.JSONDecodeError as e:
        return JsonResponse({
            'success': False,
            'message': f'Invalid JSON data: {str(e)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)



@login_required
def pending_sales_list(request):
    pending_sales = PendingSale.objects.filter(user=request.user).order_by('-created_at')
    
    sales_data = []
    for sale in pending_sales:
        try:
            data = sale.data
            sales_data.append({
                'id': sale.id,
                'created_at': sale.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                'customer': sale.customer.name if sale.customer else "Walk-in",
                'items_count': len(data.get('items', [])),
                'total': float(data.get('total', 0)),
                'sale_type': data.get('sale_type', 'retail'),
                'data': data  # Include full sale data for reference
            })
        except Exception as e:
            print(f"Error processing pending sale {sale.id}: {str(e)}")
            continue
    
    return JsonResponse({
        'success': True,
        'pending_sales': sales_data
    })

@login_required
@login_required
def load_pending_sale(request, pk):
    try:
        pending_sale = get_object_or_404(PendingSale, pk=pk, user=request.user)
        sale_data = pending_sale.data
        
        # Ensure items exists and is a list
        if 'items' not in sale_data:
            sale_data['items'] = []
        elif not isinstance(sale_data['items'], list):
            sale_data['items'] = []
        
        # Get product details for all items
        product_ids = [item.get('id') for item in sale_data.get('items', []) if item.get('id')]
        products = Product.objects.filter(id__in=product_ids).in_bulk()
        
        # Enhance items with product names
        for item in sale_data.get('items', []):
            product = products.get(int(item.get('id'))) if item.get('id') else None
            if product:
                item['name'] = product.name
                item['barcode'] = product.barcode
        
        return JsonResponse({
            'success': True,
            'sale_data': sale_data,
            'customer': {
                'id': pending_sale.customer.id if pending_sale.customer else None,
                'name': pending_sale.customer.name if pending_sale.customer else 'Walk-in Customer'
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
@login_required
@require_POST
def complete_pending_sale(request, pk):
    pending_sale = get_object_or_404(PendingSale, pk=pk, user=request.user)
    
    try:
        with transaction.atomic():
            # Create the completed sale
            sale = Sale(
                customer_id=pending_sale.data.get('customer_id'),
                user=request.user,
                sale_type=pending_sale.data.get('sale_type', 'retail'),
                subtotal=Decimal(pending_sale.data['subtotal']),
                discount_amount=Decimal(pending_sale.data.get('discount_amount', 0)),
                discount_percent=Decimal(pending_sale.data.get('discount_percent', 0)),
                total=Decimal(pending_sale.data['total']),
                payment_method=pending_sale.data['payment_method'],
                amount_paid=Decimal(pending_sale.data['amount_paid']),
                balance=max(Decimal(pending_sale.data['total']) - Decimal(pending_sale.data['amount_paid']), Decimal(0)),
                is_credit=pending_sale.data.get('is_credit', False),
                is_completed=True
            )

            # Handle multiple payment methods
            payment_details = pending_sale.data.get('payment_details', {})
            sale.mpesa_amount = Decimal(payment_details.get('mpesa', 0))
            sale.cash_amount = Decimal(payment_details.get('cash', 0))
            sale.card_amount = Decimal(payment_details.get('card', 0))
            sale.cheque_amount = Decimal(payment_details.get('cheque', 0))
            sale.mpesa_code = payment_details.get('mpesa_code', '')
            sale.cheque_number = payment_details.get('cheque_number', '')
            
            sale.save()
            
            # Create sale items and update inventory
            for item in pending_sale.data['items']:
                product = Product.objects.get(id=item['id'])
                batch = None
                
                if item.get('batch_id'):
                    batch = Batch.objects.get(id=item['batch_id'])
                
                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    batch=batch,
                    quantity=item['quantity'],
                    price=Decimal(item['price']),
                    discount_amount=Decimal(item.get('discount_amount', 0)),
                    discount_percent=Decimal(item.get('discount_percent', 0)),
                    total=Decimal(item['total'])
                )
                
                # Update product quantity
                product.quantity -= item['quantity']
                product.save()
                
                # Update batch quantity if batch was specified
                if batch:
                    batch.quantity -= item['quantity']
                    batch.save()
            
            # Update customer balance if credit sale
            if sale.is_credit and sale.customer:
                sale.customer.balance += sale.balance
                sale.customer.save()
            
            # Delete the pending sale AFTER successful completion
            pending_sale.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Sale completed successfully',
                'sale_id': sale.id,
                'pending_sale_deleted': True  # Explicit confirmation
            })

    except Exception as e:
        logger.error(f"Error completing pending sale {pk}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e),
            'pending_sale_deleted': False
        }, status=500)


# pos/views.py
from django.shortcuts import render, get_object_or_404
from .models import PendingSale, Customer, Product, Company

@login_required
def view_pending_sale(request, pk):
    pending_sale = get_object_or_404(PendingSale, pk=pk, user=request.user)
    data = pending_sale.data  # Access the JSON data
    
    # Get customer object if exists
    customer = None
    if data.get('customer_id'):
        try:
            customer = Customer.objects.get(id=data['customer_id'])
        except Customer.DoesNotExist:
            customer = None
    
    # Get product details for display
    product_ids = [item['id'] for item in data.get('items', [])]
    products = Product.objects.filter(id__in=product_ids).in_bulk()
    
    context = {
        'pending_sale': pending_sale,
        'sale_data': {
            'customer': customer.name if customer else "Walk-in",
            'customer_id': data.get('customer_id'),
            'sale_type': data.get('sale_type', 'retail'),
            'subtotal': data.get('subtotal', 0),
            'discount_amount': data.get('discount_amount', 0),
            'discount_percent': data.get('discount_percent', 0),
            'total': data.get('total', 0),
            'payment_method': data.get('payment_method'),
            'payment_details': data.get('payment_details', {}),
            'amount_paid': data.get('amount_paid', 0),
            'balance': data.get('balance', 0),
            'is_credit': data.get('is_credit', False),
            'items': [
                {
                    'id': item['id'],
                    'name': products.get(int(item['id'])).name if products.get(int(item['id'])) else "Unknown Product",
                    'price': item['price'],
                    'quantity': item['quantity'],
                    'total': item['total'],
                    'batch_id': item.get('batch_id'),
                    'discount_amount': item.get('discount_amount', 0),
                    'discount_percent': item.get('discount_percent', 0)
                }
                for item in data.get('items', [])
            ]
        },
        'company': Company.objects.first()
    }
    
    return render(request, 'pos/view_pending_sale.html', context)


from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import PendingSale

@login_required
@require_POST
def delete_pending_sale(request, pk):
    try:
        pending_sale = get_object_or_404(PendingSale, pk=pk, user=request.user)
        pending_sale.delete()
        return JsonResponse({'success': True, 'message': 'Pending sale deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
def credit_payments(request):
    credit_sales = Sale.objects.filter(is_credit=True, balance__gt=0).order_by('-date')
    
    # Filter by customer
    customer_id = request.GET.get('customer')
    if customer_id:
        credit_sales = credit_sales.filter(customer_id=customer_id)
    
    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        credit_sales = credit_sales.filter(date__date__gte=start_date)
    if end_date:
        credit_sales = credit_sales.filter(date__date__lte=end_date)
    
    # Calculate totals
    credit_sales_total = credit_sales.aggregate(
        total=Sum('total'),
        amount_paid=Sum('amount_paid'),
        balance=Sum('balance')
    )
    
    customers = Customer.objects.all()
    
    context = {
        'credit_sales': credit_sales,
        'credit_sales_total': credit_sales_total,
        'customers': customers,
        'selected_customer': customer_id,
        'start_date': start_date,
        'end_date': end_date
    }
    return render(request, 'pos/credit_payments.html', context)

@login_required
@login_required
@login_required
def process_credit_payment(request, pk):
    sale = get_object_or_404(Sale, pk=pk, is_credit=True, balance__gt=0)
    
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', 0))
            payment_method = request.POST.get('payment_method', 'cash')
            reference = request.POST.get('mpesa_code', '') or request.POST.get('cheque_number', '')
            
            if amount <= 0:
                messages.error(request, 'Amount must be greater than 0')
            elif amount > sale.balance:
                messages.error(request, f'Amount cannot be greater than the outstanding balance of {sale.balance}')
            else:
                with transaction.atomic():
                    # Create customer payment record
                    CustomerPayment.objects.create(
                        sale=sale,
                        customer=sale.customer,  # This can be None for walk-in customers
                        amount=amount,
                        date=timezone.now().date(),
                        payment_method=payment_method,
                        reference=reference,
                        user=request.user
                    )
                    
                    # Update sale payment details
                    sale.amount_paid += amount
                    sale.balance -= amount
                    
                    # Mark as paid if balance is cleared
                    if sale.balance <= 0:
                        sale.is_paid = True
                    
                    sale.save()
                    
                    # Update customer balance only if customer exists
                    if sale.customer:
                        customer = sale.customer
                        customer.balance -= amount
                        customer.save()
                    
                    messages.success(request, f'Payment of {amount} recorded successfully')
                    return redirect('credit_payments')
        
        except Exception as e:
            messages.error(request, f'Error processing payment: {str(e)}')
    
    context = {
        'sale': sale,
        'max_amount': sale.balance
    }
    return render(request, 'pos/process_credit_payment.html', context)


@login_required
def view_sale(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    context = {
        'sale': sale,
        'company': Company.objects.first()
    }
    return render(request, 'pos/view_sale.html', context)

@login_required
def edit_sale(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    
    if request.method == 'POST':
        with transaction.atomic():
            # Restore original quantities first
            for item in sale.items.all():
                product = item.product
                product.quantity += item.quantity
                product.save()
                
                if item.batch:
                    batch = item.batch
                    batch.quantity += item.quantity
                    batch.save()
            
            # Update customer balance if credit sale
            if sale.is_credit and sale.customer:
                sale.customer.balance -= sale.balance
                sale.customer.save()
            
            # Delete old items
            sale.items.all().delete()
            
            # Process new sale data
            data = json.loads(request.POST.get('sale_data'))
            
            sale.subtotal = Decimal(data['subtotal'])
            sale.discount_amount = Decimal(data.get('discount_amount', 0))
            sale.discount_percent = Decimal(data.get('discount_percent', 0))
            sale.total = Decimal(data['total'])
            sale.payment_method = data['payment_method']
            sale.amount_paid = Decimal(data['amount_paid'])
            sale.balance = max(Decimal(data['total']) - Decimal(data['amount_paid']), Decimal(0))
            sale.is_credit = data.get('is_credit', False)
            sale.notes = data.get('notes', '')
            
            # Update payment details
            payment_details = data.get('payment_details', {})
            sale.mpesa_amount = Decimal(payment_details.get('mpesa', 0))
            sale.cash_amount = Decimal(payment_details.get('cash', 0))
            sale.card_amount = Decimal(payment_details.get('card', 0))
            sale.cheque_amount = Decimal(payment_details.get('cheque', 0))
            sale.mpesa_code = payment_details.get('mpesa_code', '')
            sale.cheque_number = payment_details.get('cheque_number', '')
            
            sale.save()
            
            # Create new sale items
            for item in data['items']:
                product = Product.objects.get(id=item['id'])
                batch = None
                
                if item.get('batch_id'):
                    batch = Batch.objects.get(id=item['batch_id'])
                
                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    batch=batch,
                    quantity=item['quantity'],
                    price=Decimal(item['price']),
                    discount_amount=Decimal(item.get('discount_amount', 0)),
                    discount_percent=Decimal(item.get('discount_percent', 0)),
                    total=Decimal(item['total'])
                )
                
                # Update product quantity
                product.quantity -= item['quantity']
                product.save()
                
                # Update batch quantity if batch was specified
                if batch:
                    batch.quantity -= item['quantity']
                    batch.save()
            
            # Update customer balance if credit sale
            if sale.is_credit and sale.customer:
                sale.customer.balance += sale.balance
                sale.customer.save()
            
            return JsonResponse({'success': True})
    
    # GET request - prepare data for editing
    products = Product.objects.filter(is_active=True).order_by('name')
    categories = Category.objects.all()
    customers = Customer.objects.all().order_by('name')
    
    # Get currently valid discounts
    today = timezone.now().date()
    discounts = Discount.objects.filter(
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    )
    
    context = {
        'sale': sale,
        'products': products,
        'categories': categories,
        'customers': customers,
        'discounts': discounts,
        'company': Company.objects.first()
    }
    return render(request, 'pos/edit_sale.html', context)

# ============== Product & Inventory Views ==============
@login_required
def product_list(request):
    products = Product.objects.all().order_by('name')
    
    # Search functionality - removed description from the filter
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(barcode__icontains=search_query)
        )
    # Rest of your view remains the same...
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    # Stock filter
    stock_filter = request.GET.get('stock')
    if stock_filter == 'low':
        products = products.filter(quantity__lte=F('reorder_level'), quantity__gt=0)
    elif stock_filter == 'out':
        products = products.filter(quantity__lte=0)
    elif stock_filter == 'active':
        products = products.filter(is_active=True)
    elif stock_filter == 'inactive':
        products = products.filter(is_active=False)
    
    # Get all categories for filter dropdown
    categories = Category.objects.all()
    
    # Calculate total stock value
    total_value = products.aggregate(
        total=Sum(F('quantity') * F('selling_price'))
    )['total'] or 0
    
    # Pagination
    paginator = Paginator(products, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    export_format = request.GET.get('export')
    if export_format:
        return generate_product_list_export(export_format, products)
    
    context = {
        'products': page_obj,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'stock_filter': stock_filter,
        'total_value': total_value
    }
    return render(request, 'pos/products.html', context)

def generate_product_list_export(format, queryset):
    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="product_list.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Name', 'Barcode', 'Category', 'Supplier', 
            'Purchase Price', 'Selling Price', 'Wholesale Price',
            'Current Stock', 'Reorder Level', 'Stock Value', 'Status'
        ])
        
        for product in queryset:
            stock_value = product.quantity * product.purchase_price
            writer.writerow([
                product.name,
                product.barcode or '',
                product.category.name if product.category else '',
                product.supplier.name if product.supplier else '',
                float(product.purchase_price),
                float(product.selling_price),
                float(product.wholesale_price),
                product.quantity,
                product.reorder_level,
                float(stock_value),
                'Active' if product.is_active else 'Inactive'
            ])
        
        return response

@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            
            # Generate barcode if not provided
            if not product.barcode:
                last_product = Product.objects.order_by('-id').first()
                next_id = last_product.id + 1 if last_product else 1
                product.barcode = f"PRD{next_id:08d}"
            
            product.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    
    suppliers = Supplier.objects.all()
    categories = Category.objects.all()
    
    context = {
        'form': form,
        'suppliers': suppliers,
        'categories': categories
    }
    return render(request, 'pos/add_product.html', context)

@login_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    
    suppliers = Supplier.objects.all()
    categories = Category.objects.all()
    
    context = {
        'form': form,
        'product': product,
        'suppliers': suppliers,
        'categories': categories
    }
    return render(request, 'pos/edit_product.html', context)

@login_required
def toggle_product_status(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save()
    return redirect('product_list')

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    batches = product.batches.filter(quantity__gt=0).order_by('expiry_date')
    return render(request, 'pos/product_detail.html', {'product': product, 'batches': batches})

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum, Q, DecimalField
from django.db.models.expressions import ExpressionWrapper
from django.http import HttpResponse
from django.core.paginator import Paginator
from decimal import Decimal
import csv
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font
from .models import Product, Category, Supplier

@login_required
def inventory_report(request):
    # Debug: print received parameters
    print(f"GET parameters: {dict(request.GET)}")
    
    # Get all products with calculated stock value using PURCHASE PRICE (cost)
    products = Product.objects.annotate(
        stock_value=ExpressionWrapper(
            F('quantity') * F('purchase_price'),
            output_field=DecimalField()
        )
    ).order_by('name')
    
    print(f"Initial products count: {products.count()}")
    
    # Apply filters with validation
    category_id = request.GET.get('category')
    if category_id and category_id.isdigit():
        products = products.filter(category_id=int(category_id))
        print(f"After category filter ({category_id}): {products.count()}")
    
    supplier_id = request.GET.get('supplier')
    if supplier_id and supplier_id.isdigit():
        products = products.filter(supplier_id=int(supplier_id))
        print(f"After supplier filter ({supplier_id}): {products.count()}")
    
    # Stock status filter
    stock_filter = request.GET.get('stock')
    if stock_filter == 'low':
        products = products.filter(quantity__lte=F('reorder_level'), quantity__gt=0)
        print(f"After low stock filter: {products.count()}")
    elif stock_filter == 'out':
        products = products.filter(quantity__lte=0)
        print(f"After out of stock filter: {products.count()}")
    elif stock_filter == 'active':
        products = products.filter(is_active=True)
        print(f"After active filter: {products.count()}")
    elif stock_filter == 'inactive':
        products = products.filter(is_active=False)
        print(f"After inactive filter: {products.count()}")
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(barcode__icontains=search_query)
        )
        print(f"After search filter ({search_query}): {products.count()}")
    
    print(f"Final products count: {products.count()}")
    
    # Calculate summary statistics
    total_products = products.count()
    total_stock_value = products.aggregate(total=Sum('stock_value'))['total'] or Decimal('0.00')
    
    in_stock_count = products.filter(quantity__gt=0).count()
    low_stock_count = products.filter(quantity__gt=0, quantity__lte=F('reorder_level')).count()
    out_of_stock_count = products.filter(quantity__lte=0).count()
    
    # Get filter options
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()
    
    # Export functionality
    export_format = request.GET.get('export')
    if export_format:
        return generate_inventory_export(export_format, products)
    
    # Pagination
    paginator = Paginator(products, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Convert to string for template comparison
    context = {
        'products': page_obj,
        'categories': categories,
        'suppliers': suppliers,
        'total_products': total_products,
        'total_stock_value': total_stock_value,
        'in_stock_count': in_stock_count,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'selected_category': str(category_id) if category_id else '',
        'selected_supplier': str(supplier_id) if supplier_id else '',
        'stock_filter': stock_filter,
        'search_query': search_query,
    }
    return render(request, 'pos/inventory_report.html', context)



def generate_inventory_export(format, queryset):
    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="inventory_report_{}.csv"'.format(
            datetime.now().strftime('%Y%m%d_%H%M%S')
        )
        
        writer = csv.writer(response)
        writer.writerow([
            'Product Name', 'Barcode', 'Category', 'Supplier', 
            'Quantity', 'Reorder Level', 'Purchase Price (KES)', 
            'Selling Price (KES)', 'Stock Value (KES)', 'Status'
        ])
        
        for product in queryset:
            stock_value = product.quantity * product.purchase_price
            writer.writerow([
                product.name,
                product.barcode or '',
                product.category.name if product.category else '',
                product.supplier.name if product.supplier else '',
                product.quantity,
                product.reorder_level,
                float(product.purchase_price),
                float(product.selling_price),
                float(stock_value),
                'Active' if product.is_active else 'Inactive'
            ])
        
        return response
    
    elif format == 'excel':
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="inventory_report_{}.xlsx"'.format(
            datetime.now().strftime('%Y%m%d_%H%M%S')
        )
        
        # Create Excel workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Inventory Report"
        
        # Add headers (REMOVED SKU)
        headers = [
            'Product Name', 'Barcode', 'Category', 'Supplier', 
            'Quantity', 'Reorder Level', 'Purchase Price (KES)', 
            'Selling Price (KES)', 'Stock Value (KES)', 'Status'
        ]
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.font = Font(bold=True)
        
        # Add data (FIXED column mapping)
        for row_num, product in enumerate(queryset, 2):
            stock_value = product.quantity * product.purchase_price
            ws.cell(row=row_num, column=1, value=product.name)
            ws.cell(row=row_num, column=2, value=product.barcode or '')
            ws.cell(row=row_num, column=3, value=product.category.name if product.category else '')
            ws.cell(row=row_num, column=4, value=product.supplier.name if product.supplier else '')
            ws.cell(row=row_num, column=5, value=product.quantity)
            ws.cell(row=row_num, column=6, value=product.reorder_level)
            ws.cell(row=row_num, column=7, value=float(product.purchase_price))
            ws.cell(row=row_num, column=8, value=float(product.selling_price))
            ws.cell(row=row_num, column=9, value=float(stock_value))
            ws.cell(row=row_num, column=10, value='Active' if product.is_active else 'Inactive')
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        wb.save(response)
        return response
    
    return HttpResponse('Invalid export format', status=400)

@login_required
def profit_margin_report(request):
    # Date filtering
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date') or timezone.now().date()
    
    if not start_date:
        # Default to beginning of current month
        start_date = timezone.now().date().replace(day=1)
    
    # Get sales in date range
    sales = Sale.objects.filter(
        date__date__range=[start_date, end_date],
        is_completed=True
    )
    
    # Calculate profit margins
    sale_items = SaleItem.objects.filter(sale__in=sales).select_related('product')
    
    profit_data = []
    for item in sale_items:
        try:
            # Handle cases where product might be deleted
            if not item.product:
                continue
                
            cost = item.product.purchase_price * item.quantity
            revenue = item.total
            profit = revenue - cost
            margin = (profit / revenue * 100) if revenue > 0 else 0
            
            profit_data.append({
                'product_name': item.product.name,
                'quantity_sold': item.quantity,
                'total_cost': cost,
                'total_revenue': revenue,
                'total_profit': profit,
                'profit_margin': margin,
                'sale_date': item.sale.date
            })
        except (AttributeError, ObjectDoesNotExist):
            continue
    
    # Aggregate by product
    product_stats = {}
    for item in profit_data:
        if item['product_name'] not in product_stats:
            product_stats[item['product_name']] = {
                'quantity_sold': 0,
                'total_cost': 0,
                'total_revenue': 0,
                'total_profit': 0
            }
        
        product_stats[item['product_name']]['quantity_sold'] += item['quantity_sold']
        product_stats[item['product_name']]['total_cost'] += item['total_cost']
        product_stats[item['product_name']]['total_revenue'] += item['total_revenue']
        product_stats[item['product_name']]['total_profit'] += item['total_profit']
    
    # Calculate final margins
    final_data = []
    total_quantity = 0
    total_cost = 0
    total_revenue = 0
    total_profit = 0
    
    for product, stats in product_stats.items():
        margin = (stats['total_profit'] / stats['total_revenue'] * 100) if stats['total_revenue'] > 0 else 0
        final_data.append({
            'product_name': product,
            'quantity_sold': stats['quantity_sold'],
            'total_cost': stats['total_cost'],
            'total_revenue': stats['total_revenue'],
            'total_profit': stats['total_profit'],
            'profit_margin': margin
        })
        
        total_quantity += stats['quantity_sold']
        total_cost += stats['total_cost']
        total_revenue += stats['total_revenue']
        total_profit += stats['total_profit']
    
    # Calculate average margin
    avg_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Sort by profit margin
    final_data.sort(key=lambda x: x['profit_margin'], reverse=True)
    
    context = {
        'profit_data': final_data,
        'start_date': start_date,
        'end_date': end_date,
        'total_quantity': total_quantity,
        'total_cost': total_cost,
        'total_revenue': total_revenue,
        'total_profit': total_profit,
        'avg_margin': avg_margin
    }
    return render(request, 'pos/profit_margin_report.html', context)



# ============== Batch Management Views ==============
@login_required
def batch_list(request):
    batches = Batch.objects.filter(quantity__gt=0).order_by('-expiry_date')
    
    # Filter by product
    product_id = request.GET.get('product')
    if product_id:
        batches = batches.filter(product_id=product_id)
    
    # Filter by expiry status
    expiry_filter = request.GET.get('expiry')
    if expiry_filter == 'expired':
        batches = batches.filter(expiry_date__lt=timezone.now().date())
    elif expiry_filter == 'expiring':
        batches = batches.filter(
            expiry_date__gte=timezone.now().date(),
            expiry_date__lte=timezone.now().date() + timedelta(days=30)
        )
    
    products = Product.objects.filter(is_active=True).order_by('name')
    
    context = {
        'batches': batches,
        'products': products,
        'selected_product': product_id,
        'expiry_filter': expiry_filter
    }
    return render(request, 'pos/batch_list.html', context)

@login_required
def add_batch(request):
    if request.method == 'POST':
        form = BatchForm(request.POST)
        if form.is_valid():
            batch = form.save()
            
            # Update product quantity
            product = batch.product
            product.quantity += batch.quantity
            product.save()
            
            return redirect('batch_list')
    else:
        form = BatchForm()
    
    products = Product.objects.filter(is_active=True).order_by('name')
    
    context = {
        'form': form,
        'products': products
    }
    return render(request, 'pos/add_batch.html', context)

@login_required
def edit_batch(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    
    if request.method == 'POST':
        original_quantity = batch.quantity
        form = BatchForm(request.POST, instance=batch)
        
        if form.is_valid():
            batch = form.save()
            
            # Update product quantity with the difference
            product = batch.product
            product.quantity += (batch.quantity - original_quantity)
            product.save()
            
            return redirect('batch_list')
    else:
        form = BatchForm(instance=batch)
    
    context = {
        'form': form,
        'batch': batch
    }
    return render(request, 'pos/edit_batch.html', context)

# ============== Customer Views ==============
@login_required
def customer_list(request):
    customers = Customer.objects.all().order_by('name')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query))
    
    # Filter by balance status
    balance_filter = request.GET.get('balance')
    if balance_filter == 'credit':
        customers = customers.filter(balance__gt=0)
    elif balance_filter == 'zero':
        customers = customers.filter(balance=0)
    
    # Export functionality
    export_format = request.GET.get('export')
    if export_format:
        return generate_customer_export(export_format, customers)
    
    # Pagination
    paginator = Paginator(customers, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    customer_purchases = Sale.objects.filter(
        is_completed=True
    ).values(
        'customer__name'
    ).annotate(
        total_spent=Sum('total'),
        visit_count=Count('id'),
        last_visit=Max('date')
    ).order_by('-total_spent')
    
    context = {
        'customers': page_obj,
        'search_query': search_query,
        'balance_filter': balance_filter,
        'customer_purchases': customer_purchases
    }
    return render(request, 'pos/customer_list.html', context)

@login_required
def add_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        form = CustomerForm()
    
    context = {
        'form': form
    }
    return render(request, 'pos/add_customer.html', context)

@login_required
def edit_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=customer)
    
    context = {
        'form': form,
        'customer': customer
    }
    return render(request, 'pos/edit_customer.html', context)

@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    sales = Sale.objects.filter(customer=customer).order_by('-date')
    
    # Pagination for sales
    paginator = Paginator(sales, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'customer': customer,
        'sales': page_obj
    }
    return render(request, 'pos/customer_detail.html', context)

@login_required
def customer_payment(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))
        payment_method = request.POST.get('payment_method')
        reference = request.POST.get('reference', '')
        
        if amount > 0:
            with transaction.atomic():
                # Create a negative sale to record the payment
                payment_sale = Sale.objects.create(
                    customer=customer,
                    user=request.user,
                    subtotal=0,
                    total=amount,
                    payment_method=payment_method,
                    amount_paid=amount,
                    balance=-amount,
                    is_completed=True,
                    is_payment=True,
                    reference=reference
                )
                
                # Update customer balance
                customer.balance -= amount
                customer.save()
                
                return redirect('customer_detail', pk=pk)
    
    context = {
        'customer': customer
    }
    return render(request, 'pos/customer_payment.html', context)

def generate_customer_export(format, queryset):
    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="customers.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Name', 'Phone', 'Email', 'Address', 
            'Credit Limit', 'Balance'
        ])
        
        for customer in queryset:
            writer.writerow([
                customer.name,
                customer.phone,
                customer.email,
                customer.address,
                customer.credit_limit,
                customer.balance
            ])
    
        return response
    
    return HttpResponse('Invalid export format', status=400)

# ============== Sales Reports Views ==============
@login_required
def sales_report(request):
    sales = Sale.objects.filter(is_completed=True).order_by('-date')
    
    # Date filtering
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        sales = sales.filter(date__date__gte=start_date)
    if end_date:
        sales = sales.filter(date__date__lte=end_date)
    
    # Payment method filter
    payment_method = request.GET.get('payment_method')
    if payment_method:
        sales = sales.filter(payment_method=payment_method)
    
    # Sale type filter
    sale_type = request.GET.get('sale_type')
    if sale_type:
        sales = sales.filter(sale_type=sale_type)
    
    # Credit status filter
    credit_filter = request.GET.get('credit')
    if credit_filter == 'credit':
        sales = sales.filter(is_credit=True)
    elif credit_filter == 'paid':
        sales = sales.filter(is_credit=False)
    
    # Customer filter
    customer_id = request.GET.get('customer')
    if customer_id:
        sales = sales.filter(customer_id=customer_id)
    
    # Calculate summary stats
    total_sales = sales.aggregate(total=Sum('total'))['total'] or 0
    total_items = sales.aggregate(total=Sum('items__quantity'))['total'] or 0
    
    payment_methods = Sale.PAYMENT_METHODS
    payment_totals = []
    
    for method in payment_methods:
        total = sales.filter(payment_method=method[0]).aggregate(
            total=Sum('total'))['total'] or 0
        payment_totals.append({
            'method': method[1],
            'total': total
        })
    
    # Get all customers for filter dropdown
    customers = Customer.objects.all()

    sales_by_hour = sales.annotate(
        hour=ExtractHour('date')
    ).values('hour').annotate(
        total=Sum('total'),
        count=Count('id')
    ).order_by('hour')
    
    top_products = SaleItem.objects.filter(sale__in=sales).values(
        'product__name'
    ).annotate(
        quantity=Sum('quantity'),
        revenue=Sum('total')
    ).order_by('-revenue')[:10]
    
    

    # Export functionality
    export_format = request.GET.get('export')
    if export_format:
        return generate_sales_export(export_format, sales)
    
    # Pagination
    paginator = Paginator(sales, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'sales': page_obj,
        'customers': customers,
        'total_sales': total_sales,
        'total_items': total_items,
        'payment_totals': payment_totals,
        'start_date': start_date,
        'end_date': end_date,
        'payment_method': payment_method,
        'sale_type': sale_type,
        'credit_filter': credit_filter,
        'selected_customer': customer_id,
        'sales_by_hour': sales_by_hour,
        'top_products': top_products
    }
    return render(request, 'pos/sales_report.html', context)

@login_required
def daily_sales_summary(request):
    today = timezone.now().date()
    
    # Get sales totals by payment method with proper aggregation
    sales = Sale.objects.filter(
        date__date=today,
        is_completed=True
    ).annotate(
        payment_total=Case(
            When(payment_method='cash', then=F('total')),
            When(payment_method='mpesa', then=F('total')),
            When(payment_method='card', then=F('total')),
            When(payment_method='cheque', then=F('total')),
            default=Value(0),
            output_field=DecimalField()
        )
    )
    
    # Calculate totals using proper aggregation
    totals = sales.aggregate(
        cash_sales=Sum('cash_amount'),
        mpesa_sales=Sum('mpesa_amount'),
        card_sales=Sum('card_amount'),
        cheque_sales=Sum('cheque_amount'),
        credit_sales=Sum('total', filter=Q(is_credit=True)),
        all_sales=Sum('total')
    )
    
    # Handle None values from aggregation
    cash_sales = totals['cash_sales'] or 0
    mpesa_sales = totals['mpesa_sales'] or 0
    card_sales = totals['card_sales'] or 0
    cheque_sales = totals['cheque_sales'] or 0
    credit_sales = totals['credit_sales'] or 0
    total_sales = totals['all_sales'] or 0
    
    # Get expenses and purchases for the day
    expenses = Expense.objects.filter(date__date=today)
    purchases = Purchase.objects.filter(date__date=today)
    
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    total_purchases = purchases.aggregate(total=Sum('total'))['total'] or 0
    
    # Calculate net cash (excluding credit sales)
    net_cash = (cash_sales + mpesa_sales + card_sales + cheque_sales) - total_expenses - total_purchases
    
    context = {
        'date': today,
        'cash_sales': cash_sales,
        'mpesa_sales': mpesa_sales,
        'card_sales': card_sales,
        'cheque_sales': cheque_sales,
        'credit_sales': credit_sales,
        'total_sales': total_sales,
        'total_expenses': total_expenses,
        'total_purchases': total_purchases,
        'net_cash': net_cash
    }
    return render(request, 'pos/daily_sales_summary.html', context)

def generate_sales_export(format, queryset):
    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Sale Number', 'Date', 'Customer', 'Items', 
            'Subtotal', 'Discount', 'Total', 
            'Payment Method', 'Amount Paid', 'Balance',
            'Cash Amount', 'Mpesa Amount', 'Card Amount', 'Cheque Amount'
        ])
        
        for sale in queryset:
            writer.writerow([
                sale.sale_number,
                sale.date.strftime('%Y-%m-%d %H:%M'),
                sale.customer.name if sale.customer else 'Walk-in',
                sale.items.aggregate(total=Sum('quantity'))['total'] or 0,
                sale.subtotal,
                sale.discount_amount,
                sale.total,
                sale.get_payment_method_display(),
                sale.amount_paid,
                sale.balance,
                sale.cash_amount,
                sale.mpesa_amount,
                sale.card_amount,
                sale.cheque_amount
            ])
        
        return response
    
    return HttpResponse('Invalid export format', status=400)

# ============== Purchase Views ==============



@login_required
@login_required
@login_required
def purchase_list(request):
    # Use the existing item_count field instead of annotating
    purchases = Purchase.objects.all().order_by('-date')
    
    # Filter parameters
    filters = {
        'start_date': request.GET.get('start_date'),
        'end_date': request.GET.get('end_date'),
        'supplier_id': request.GET.get('supplier'),
        'payment': request.GET.get('payment'),
        'is_return': request.GET.get('is_return'),
        'return_status': request.GET.get('return_status'),
        'search': request.GET.get('search')
    }
    
    # Apply filters
    if filters['start_date']:
        purchases = purchases.filter(date__date__gte=filters['start_date'])
    if filters['end_date']:
        purchases = purchases.filter(date__date__lte=filters['end_date'])
    if filters['supplier_id']:
        purchases = purchases.filter(supplier_id=filters['supplier_id'])
    
    # Payment status filter
    if filters['payment'] == 'paid':
        purchases = purchases.filter(is_paid=True)
    elif filters['payment'] == 'unpaid':
        purchases = purchases.filter(is_paid=False)
    
    # Return status filter
    if filters['is_return'] == 'true':
        purchases = purchases.filter(is_return=True)
        if filters['return_status']:
            purchases = purchases.filter(return_status=filters['return_status'])
    elif filters['is_return'] == 'false':
        purchases = purchases.filter(is_return=False)
    
    # Search functionality
    if filters['search']:
        purchases = purchases.filter(
            Q(invoice_number__icontains=filters['search']) |
            Q(supplier__name__icontains=filters['search']) |
            Q(return_reason__icontains=filters['search'])
        )
    
    # Get all suppliers for filter dropdown
    suppliers = Supplier.objects.all().order_by('name')
    
    # Calculate summary stats using conditional aggregation
    stats = purchases.aggregate(
        total_purchases=Sum('total', filter=Q(is_return=False)),
        total_returns=Sum('total', filter=Q(is_return=True)),
        total_items=Sum('items__quantity')
    )
    stats = {k: v or 0 for k, v in stats.items()}
    
    # Export functionality
    export_format = request.GET.get('export')
    if export_format:
        return generate_purchases_export(export_format, purchases)
    
    # Pagination
    paginator = Paginator(purchases, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    

    purchases_by_supplier = purchases.values(
        'supplier__name'
    ).annotate(
        total=Sum('total'),
        count=Count('id')
    ).order_by('-total')
    
    

    context = {
        'purchases': page_obj,
        'suppliers': suppliers,
        'total_purchases': stats['total_purchases'],
        'total_returns': stats['total_returns'],
        'total_items': stats['total_items'],
        'start_date': filters['start_date'],
        'end_date': filters['end_date'],
        'selected_supplier': filters['supplier_id'],
        'payment_filter': filters['payment'],
        'return_filter': filters['is_return'],
        'return_status_filter': filters['return_status'],
        'search_query': filters['search'],
        'purchases_by_supplier': purchases_by_supplier
    }
    
    return render(request, 'pos/purchase_list.html', context)



from django.db.models import Q
from django.http import JsonResponse
import json
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from .models import Supplier, Product, Purchase, PurchaseItem
from .forms import PurchaseForm

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.views.decorators.http import require_GET, require_POST
import json
from .models import Product, Supplier, Purchase, PurchaseItem
from .forms import PurchaseForm

@login_required
@login_required
def add_purchase(request):
    # Generate invoice number
    today = timezone.now().date()
    purchases_today = Purchase.objects.filter(date__date=today).count()
    next_invoice_number = purchases_today + 1
    invoice_number = f"INV-{today.strftime('%Y%m%d')}-{next_invoice_number:04d}"

    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        
        try:
            if form.is_valid():
                with transaction.atomic():
                    # Create and save the purchase first
                    purchase = form.save(commit=False)
                    purchase.user = request.user
                    purchase.invoice_number = invoice_number
                    purchase.save()  # Save the purchase first to get an ID
                    
                    # Calculate totals from items
                    items = []
                    item_count = 0
                    subtotal = Decimal('0.00')
                    
                    # Process items from POST data
                    i = 0
                    while f'items[{i}][product_id]' in request.POST:
                        product_id = request.POST.get(f'items[{i}][product_id]')
                        quantity = Decimal(request.POST.get(f'items[{i}][quantity]', '0'))
                        
                        try:
                            product = Product.objects.get(id=product_id)
                            
                            # Get the price - use purchase_price as default if not provided
                            price_str = request.POST.get(f'items[{i}][price]')
                            price = Decimal(price_str) if price_str else product.purchase_price
                            
                            batch_number = request.POST.get(f'items[{i}][batch_number]', '')
                            expiry_date = request.POST.get(f'items[{i}][expiry_date]')
                            
                            # Create batch if batch number provided
                            batch = None
                            if batch_number:
                                batch = Batch.objects.create(
                                    product=product,
                                    batch_number=batch_number,
                                    quantity=quantity,
                                    purchase_price=price,  # Use the entered price
                                    expiry_date=expiry_date if expiry_date else None
                                )
                            
                            # Create purchase item with the saved purchase
                            PurchaseItem.objects.create(
                                purchase=purchase,
                                product=product,
                                batch=batch,
                                quantity=quantity,
                                price=price,
                                total=quantity * price
                            )
                            
                            # Update product stock and purchase price
                            product.quantity += quantity
                            product.purchase_price = price  # Update with latest purchase price
                            product.save()
                            
                            subtotal += quantity * price
                            item_count += 1
                            
                        except Product.DoesNotExist:
                            raise ValidationError(f"Product with ID {product_id} does not exist")
                        
                        i += 1
                    
                    if item_count == 0:
                        raise ValidationError("Please add at least one item to the purchase")
                    
                    # Update purchase totals
                    purchase.subtotal = subtotal
                    purchase.total = subtotal  # No tax
                    purchase.item_count = item_count
                    purchase.save()
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'redirect_url': reverse('view_purchase', args=[purchase.id])
                        })
                    return redirect('purchase_list')
        
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': str(e),
                    'errors': form.errors
                }, status=400)
            messages.error(request, f'Error saving purchase: {str(e)}')
    else:
        form = PurchaseForm(initial={
            'invoice_number': invoice_number
        })
    
    products = Product.objects.filter(is_active=True).order_by('name')
    suppliers = Supplier.objects.all().order_by('name')
    
    context = {
        'form': form,
        'products': products,
        'suppliers': suppliers,
        'today': today,
        'next_invoice_number': next_invoice_number
    }
    return render(request, 'pos/add_purchase.html', context)


@login_required
def edit_purchase(request, pk):
    try:
        purchase = get_object_or_404(Purchase, pk=pk)
        
        if request.method == 'POST':
            form = PurchaseForm(request.POST, instance=purchase)
            
            try:
                if form.is_valid():
                    with transaction.atomic():
                        # First, restore original quantities
                        for item in purchase.items.all():
                            product = item.product
                            product.quantity -= item.quantity
                            product.save()
                            
                            if item.batch:
                                batch = item.batch
                                batch.quantity -= item.quantity
                                # Only delete batch if it's not used elsewhere
                                if batch.quantity <= 0:
                                    batch.delete()
                                else:
                                    batch.save()
                        
                        # Delete old items
                        purchase.items.all().delete()
                        
                        # Process new items from POST data
                        items = []
                        item_count = 0
                        subtotal = Decimal('0.00')
                        
                        i = 0
                        while f'items[{i}][product_id]' in request.POST:
                            product_id = request.POST.get(f'items[{i}][product_id]')
                            quantity = Decimal(request.POST.get(f'items[{i}][quantity]', '0'))
                            
                            try:
                                product = Product.objects.get(id=product_id)
                                price_str = request.POST.get(f'items[{i}][price]')
                                price = Decimal(price_str) if price_str else product.purchase_price
                                
                                batch_number = request.POST.get(f'items[{i}][batch_number]', '').strip()
                                expiry_date = request.POST.get(f'items[{i}][expiry_date]')
                                
                                # Create batch if batch number provided
                                batch = None
                                if batch_number:
                                    # Check if batch already exists for this product
                                    existing_batch = Batch.objects.filter(
                                        product=product, 
                                        batch_number=batch_number
                                    ).first()
                                    
                                    if existing_batch:
                                        batch = existing_batch
                                        batch.quantity += quantity
                                        batch.purchase_price = price
                                        if expiry_date:
                                            batch.expiry_date = expiry_date
                                        batch.save()
                                    else:
                                        batch = Batch.objects.create(
                                            product=product,
                                            batch_number=batch_number,
                                            quantity=quantity,
                                            purchase_price=price,
                                            expiry_date=expiry_date if expiry_date else None
                                        )
                                
                                # Create purchase item
                                PurchaseItem.objects.create(
                                    purchase=purchase,
                                    product=product,
                                    batch=batch,
                                    quantity=quantity,
                                    price=price,
                                    total=quantity * price
                                )
                                
                                # Update product stock and purchase price
                                product.quantity += quantity
                                product.purchase_price = price
                                product.save()
                                
                                subtotal += quantity * price
                                item_count += 1
                                
                            except Product.DoesNotExist:
                                raise ValidationError(f"Product with ID {product_id} does not exist")
                            
                            i += 1
                        
                        if item_count == 0:
                            raise ValidationError("Please add at least one item to the purchase")
                        
                        # Update purchase totals
                        purchase.subtotal = subtotal
                        purchase.total = subtotal  # No tax
                        purchase.item_count = item_count
                        purchase.save()
                        
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({
                                'success': True,
                                'redirect_url': reverse('view_purchase', args=[purchase.id])
                            })
                        messages.success(request, 'Purchase updated successfully!')
                        return redirect('purchase_list')
            
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': str(e),
                        'errors': form.errors
                    }, status=400)
                messages.error(request, f'Error saving purchase: {str(e)}')
        else:
            form = PurchaseForm(instance=purchase)
        
        products = Product.objects.filter(is_active=True).order_by('name')
        suppliers = Supplier.objects.all().order_by('name')
        
        context = {
            'form': form,
            'purchase': purchase,
            'products': products,
            'suppliers': suppliers,
            'today': timezone.now().date(),
        }
        return render(request, 'pos/edit_purchase.html', context)
    
    except Http404:
        messages.error(request, 'The purchase you\'re trying to edit does not exist or has been deleted.')
        return redirect('purchase_list')


from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse, Http404  # Added Http404 import
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from django.core.exceptions import ValidationError
from .models import Purchase, Product, Supplier, PurchaseItem, Batch
from .forms import PurchaseForm  # Make sure to import your form


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Purchase, PendingPurchase

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.views.decorators.http import require_POST

from .models import Purchase, PendingPurchase, PurchaseItem, Batch
import json

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
import json

@login_required
@csrf_exempt  # Temporarily for testing, remove in production
@require_POST
@login_required
@require_POST
def save_purchase_as_pending(request):
    try:
        # Parse JSON data from request
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            }, status=400)

        with transaction.atomic():
            # Validate required fields - check both supplier_id and supplier
            supplier_id = data.get('supplier_id') or data.get('supplier')
            
            if not supplier_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Supplier is required'
                }, status=400)
                
            try:
                supplier = Supplier.objects.get(id=supplier_id)
            except (Supplier.DoesNotExist, ValueError):
                return JsonResponse({
                    'success': False,
                    'message': 'Supplier not found'
                }, status=404)
            
            # Validate items
            if 'items' not in data or not data['items']:
                return JsonResponse({
                    'success': False,
                    'message': 'At least one item is required'
                }, status=400)
            
            # Prepare items data
            items_data = []
            subtotal = 0
            
            for item in data['items']:
                try:
                    product = Product.objects.get(id=item['product_id'])
                    quantity = float(item['quantity'])
                    price = float(item['price'])
                    total = quantity * price
                    
                    items_data.append({
                        'product_id': product.id,
                        'product_name': product.name,
                        'quantity': quantity,
                        'price': price,
                        'batch_number': item.get('batch_number', ''),
                        'expiry_date': item.get('expiry_date', ''),
                        'total': total
                    })
                    
                    subtotal += total
                except Product.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': f'Product with ID {item["product_id"]} not found'
                    }, status=404)
                except (KeyError, ValueError) as e:
                    return JsonResponse({
                        'success': False,
                        'message': f'Invalid item data: {str(e)}'
                    }, status=400)
            
            # Create pending purchase data
            pending_data = {
                'supplier_id': supplier.id,
                'invoice_number': data.get('invoice_number', ''),
                'items': items_data,
                'subtotal': subtotal,
                'total': subtotal,  # No tax for now
                'is_paid': data.get('is_paid', False),
                'payment_method': data.get('payment_method', ''),
                'notes': data.get('notes', '')
            }
            
            # Create pending purchase
            pending_purchase = PendingPurchase.objects.create(
                user=request.user,
                supplier=supplier,
                data=pending_data
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Purchase saved as pending successfully',
                'pending_purchase_id': pending_purchase.id,
                'redirect_url': reverse('pending_purchases')
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Server error: {str(e)}'
        }, status=500)
    

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.views.decorators.http import require_POST, require_GET
from django.core.paginator import Paginator
import json
from decimal import Decimal

from .models import PendingPurchase, Product, Supplier, Purchase, PurchaseItem, Batch
from .forms import PurchaseForm

@login_required
def pending_purchases_list(request):
    """List all pending purchases"""
    pending_purchases = PendingPurchase.objects.filter(
        user=request.user, 
        status='pending'
    ).select_related('supplier').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(pending_purchases, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'pending_purchases': page_obj,
    }
    return render(request, 'pos/pending_purchases_list.html', context)


# views.py
@login_required
def edit_pending_purchase(request, pk):
    """Edit a pending purchase with the same interface as add purchase"""
    pending_purchase = get_object_or_404(PendingPurchase, pk=pk, user=request.user, status='pending')
    
    if request.method == 'POST':
        try:
            # Parse JSON data
            data = json.loads(request.body)
            
            with transaction.atomic():
                # Validate supplier
                supplier_id = data.get('supplier')
                if not supplier_id:
                    return JsonResponse({
                        'success': False,
                        'message': 'Supplier is required'
                    }, status=400)
                
                try:
                    supplier = Supplier.objects.get(id=supplier_id)
                except Supplier.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Supplier not found'
                    }, status=404)
                
                # Validate items
                if 'items' not in data or not data['items']:
                    return JsonResponse({
                        'success': False,
                        'message': 'At least one item is required'
                    }, status=400)
                
                # Process items
                items_data = []
                subtotal = Decimal('0.00')
                
                for item in data['items']:
                    try:
                        product = Product.objects.get(id=item['product_id'])
                        quantity = Decimal(str(item['quantity']))
                        price = Decimal(str(item['price']))
                        total = quantity * price
                        
                        items_data.append({
                            'product_id': product.id,
                            'product_name': product.name,
                            'quantity': float(quantity),
                            'price': float(price),
                            'batch_number': item.get('batch_number', ''),
                            'expiry_date': item.get('expiry_date', ''),
                            'total': float(total)
                        })
                        
                        subtotal += total
                    except Product.DoesNotExist:
                        return JsonResponse({
                            'success': False,
                            'message': f'Product with ID {item["product_id"]} not found'
                        }, status=404)
                    except (KeyError, ValueError) as e:
                        return JsonResponse({
                            'success': False,
                            'message': f'Invalid item data: {str(e)}'
                        }, status=400)
                
                # Update pending purchase
                pending_purchase.supplier = supplier
                pending_purchase.invoice_number = data.get('invoice_number', '')
                pending_purchase.data = {
                    'supplier_id': supplier.id,
                    'invoice_number': data.get('invoice_number', ''),
                    'items': items_data,
                    'subtotal': float(subtotal),
                    'total': float(subtotal),
                    'is_paid': data.get('is_paid', False),
                    'payment_method': data.get('payment_method', ''),
                    'notes': data.get('notes', '')
                }
                pending_purchase.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Pending purchase updated successfully',
                    'redirect_url': reverse('view_pending_purchase', args=[pending_purchase.id])
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error updating pending purchase: {str(e)}'
            }, status=500)
    
    # GET request - prepare data for the form
    suppliers = Supplier.objects.all().order_by('name')
    products = Product.objects.filter(is_active=True).order_by('name')
    
    # Prepare items data for the form
    items = pending_purchase.data.get('items', [])
    
    context = {
        'pending_purchase': pending_purchase,
        'suppliers': suppliers,
        'products': products,
        'items_json': json.dumps(items),
        'selected_supplier': pending_purchase.supplier,
        'invoice_number': pending_purchase.data.get('invoice_number', ''),
        'is_paid': pending_purchase.data.get('is_paid', False),
        'payment_method': pending_purchase.data.get('payment_method', ''),
        'notes': pending_purchase.data.get('notes', ''),
    }
    
    return render(request, 'pos/edit_pending_purchase.html', context)


@login_required
@require_POST
def complete_pending_purchase(request, pk):
    """Convert a pending purchase to a completed purchase"""
    pending_purchase = get_object_or_404(PendingPurchase, pk=pk, user=request.user, status='pending')
    
    try:
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        with transaction.atomic():
            # Get data from pending purchase
            pending_data = pending_purchase.data
            
            # Create the purchase
            purchase = Purchase.objects.create(
                supplier=pending_purchase.supplier,
                invoice_number=pending_data.get('invoice_number', ''),
                subtotal=Decimal(pending_data.get('subtotal', '0.00')),
                total=Decimal(pending_data.get('total', '0.00')),
                item_count=len(pending_data.get('items', [])),
                is_paid=pending_data.get('is_paid', False),
                payment_method=pending_data.get('payment_method', ''),
                notes=pending_data.get('notes', ''),
                user=request.user,
                is_return=False
            )
            
            # Add items to the purchase and update inventory
            for item_data in pending_data.get('items', []):
                try:
                    product = Product.objects.get(id=item_data['product_id'])
                    quantity = Decimal(str(item_data['quantity']))
                    price = Decimal(str(item_data['price']))
                    
                    # Create batch if batch number provided
                    batch = None
                    if item_data.get('batch_number'):
                        batch = Batch.objects.create(
                            product=product,
                            batch_number=item_data['batch_number'],
                            quantity=quantity,
                            purchase_price=price,
                            expiry_date=item_data.get('expiry_date')
                        )
                    
                    # Create purchase item
                    PurchaseItem.objects.create(
                        purchase=purchase,
                        product=product,
                        batch=batch,
                        quantity=quantity,
                        price=price,
                        total=quantity * price
                    )
                    
                    # Update product stock
                    product.quantity += quantity
                    product.purchase_price = price  # Update with latest purchase price
                    product.save()
                    
                except Product.DoesNotExist:
                    # If product doesn't exist, skip it but continue with others
                    continue
            
            # Mark pending purchase as completed
            pending_purchase.status = 'completed'
            pending_purchase.save()
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Purchase completed successfully!',
                    'purchase_id': purchase.id
                })
            else:
                messages.success(request, 'Purchase completed successfully!')
                return redirect('view_purchase', pk=purchase.id)
    
    except Exception as e:
        error_message = f'Error completing purchase: {str(e)}'
        if is_ajax:
            return JsonResponse({
                'success': False,
                'message': error_message
            }, status=500)
        else:
            messages.error(request, error_message)
            return redirect('pending_purchases_list')


            
@login_required
@require_POST
def delete_pending_purchase(request, pk):
    """Delete a pending purchase"""
    pending_purchase = get_object_or_404(PendingPurchase, pk=pk, user=request.user, status='pending')
    
    try:
        pending_purchase.delete()
        messages.success(request, 'Pending purchase deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting pending purchase: {str(e)}')
    
    return redirect('pending_purchases_list')


@login_required
def pending_purchases(request):
    pending_purchases = PendingPurchase.objects.filter(status='pending').order_by('-created_at')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(pending_purchases, 25)
    
    try:
        pending_purchases = paginator.page(page)
    except PageNotAnInteger:
        pending_purchases = paginator.page(1)
    except EmptyPage:
        pending_purchases = paginator.page(paginator.num_pages)
    
    context = {
        'pending_purchases': pending_purchases,
    }
    return render(request, 'pos/pending_purchases.html', context)

@login_required
def view_pending_purchase(request, pk):
    """View details of a specific pending purchase"""
    pending_purchase = get_object_or_404(PendingPurchase, pk=pk, user=request.user)
    
    # Get product details for display
    product_ids = [item.get('product_id') for item in pending_purchase.data.get('items', [])]
    products = Product.objects.filter(id__in=product_ids).in_bulk()
    
    # Enhance items with product details
    items = []
    for item in pending_purchase.data.get('items', []):
        product = products.get(int(item.get('product_id'))) if item.get('product_id') else None
        if product:
            items.append({
                'product': product,
                'quantity': item.get('quantity', 0),
                'price': item.get('price', 0),
                'batch_number': item.get('batch_number', ''),
                'expiry_date': item.get('expiry_date', ''),
                'total': Decimal(item.get('quantity', 0)) * Decimal(item.get('price', 0))
            })
    
    context = {
        'pending_purchase': pending_purchase,
        'items': items,
        'subtotal': pending_purchase.data.get('subtotal', 0),
        'total': pending_purchase.data.get('total', 0),
    }
    return render(request, 'pos/view_pending_purchase.html', context)




@login_required
def get_purchase_items_api(request, purchase_id):
    # API endpoint to get purchase items in JSON format
    purchase = get_object_or_404(Purchase, id=purchase_id)
    items = purchase.items.all().values(
        'id', 'product__id', 'product__name', 'quantity', 
        'price', 'total', 'batch__batch_number', 'batch__expiry_date'
    )
    return JsonResponse(list(items), safe=False)

@login_required
def export_purchases(request):
    # Export purchases to CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="purchases_{}.csv"'.format(
        datetime.now().strftime('%Y%m%d_%H%M%S')
    )
    
    writer = csv.writer(response)
    writer.writerow([
        'Invoice Number', 'Date', 'Supplier', 'Items Count', 
        'Total Amount', 'Payment Status', 'Created By'
    ])
    
    purchases = Purchase.objects.filter(is_return=False).select_related('supplier', 'created_by')
    for purchase in purchases:
        writer.writerow([
            purchase.invoice_number,
            purchase.date.strftime('%Y-%m-%d %H:%M'),
            purchase.supplier.name,
            purchase.item_count,
            purchase.total,
            'Paid' if purchase.is_paid else 'Unpaid',
            purchase.created_by.get_full_name() or purchase.created_by.username
        ])
    
    return response

@login_required
def export_pending_purchases(request):
    # Export pending purchases to CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="pending_purchases_{}.csv"'.format(
        datetime.now().strftime('%Y%m%d_%H%M%S')
    )
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Supplier', 'Invoice Number', 'Items Count', 
        'Total Amount', 'Created At', 'Status', 'Created By'
    ])
    
    pending_purchases = PendingPurchase.objects.select_related('supplier', 'user')
    for pp in pending_purchases:
        writer.writerow([
            pp.id,
            pp.supplier.name,
            pp.data.get('invoice_number', ''),
            len(pp.data.get('items', [])),
            pp.data.get('total', '0.00'),
            pp.created_at.strftime('%Y-%m-%d %H:%M'),
            pp.get_status_display(),
            pp.user.get_full_name() or pp.user.username
        ])
    
    return response

@login_required
def export_supplier_returns(request):
    # Export supplier returns to CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="supplier_returns_{}.csv"'.format(
        datetime.now().strftime('%Y%m%d_%H%M%S')
    )
    
    writer = csv.writer(response)
    writer.writerow([
        'Return Number', 'Date', 'Original Invoice', 'Supplier', 
        'Items Count', 'Total Amount', 'Status', 'Processed By'
    ])
    
    returns = Purchase.objects.filter(is_return=True).select_related('supplier', 'processed_by')
    for ret in returns:
        writer.writerow([
            ret.invoice_number,
            ret.date.strftime('%Y-%m-%d %H:%M'),
            ret.original_invoice,
            ret.supplier.name,
            ret.item_count,
            ret.total,
            ret.get_return_status_display(),
            ret.processed_by.get_full_name() if ret.processed_by else ''
        ])
    
    return response

@login_required
def cancel_pending_purchase(request, pk):
    pending_purchase = get_object_or_404(PendingPurchase, pk=pk, status='pending')
    
    try:
        pending_purchase.status = 'canceled'
        pending_purchase.save()
        messages.success(request, 'Pending purchase canceled successfully')
    except Exception as e:
        messages.error(request, f'Error canceling pending purchase: {str(e)}')
    
    return redirect('pending_purchases')


@login_required
def search_suppliers(request):
    search_term = request.GET.get('search', '').strip()
    
    if len(search_term) < 2:
        return JsonResponse([], safe=False)
    
    suppliers = Supplier.objects.filter(
        Q(name__icontains=search_term) |
        Q(contact_person__icontains=search_term) |
        Q(phone__icontains=search_term) |
        Q(email__icontains=search_term)
    ).distinct()[:10]
    
    results = [{
        'id': s.id,
        'text': f"{s.name} - {s.contact_person or ''} ({s.phone or ''})"
    } for s in suppliers]
    
    return JsonResponse(results, safe=False)


from django.views.decorators.http import require_GET
import json

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Q
import json

@login_required


@login_required
def view_purchase(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    return render(request, 'pos/view_purchase.html', {'purchase': purchase})

@login_required
def record_payment(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    
    # Calculate total payments already made for this purchase
    total_paid = SupplierPayment.objects.filter(purchase=purchase).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    balance_due = purchase.total - total_paid
    
    if request.method == 'POST':
        try:
            amount = float(request.POST.get('amount', 0))
            payment_method = request.POST.get('payment_method')
            reference = request.POST.get('reference', '')
            payment_date = request.POST.get('date') or timezone.now().date()
            
            # Validate amount
            if amount <= 0:
                messages.error(request, 'Amount must be greater than 0')
            elif amount > balance_due:
                messages.error(request, f'Payment amount cannot exceed the balance due of KSh {balance_due:.2f}')
            else:
                # Create the payment record
                SupplierPayment.objects.create(
                    purchase=purchase,
                    supplier=purchase.supplier,
                    amount=amount,
                    date=payment_date,
                    payment_method=payment_method,
                    reference=reference,
                    user=request.user
                )
                
                # Update purchase payment status
                new_total_paid = total_paid + amount
                purchase.is_paid = new_total_paid >= purchase.total
                purchase.save()
                
                messages.success(request, f'Payment of KSh {amount:.2f} recorded successfully')
                return redirect('view_purchase', pk=purchase.id)
                
        except ValueError:
            messages.error(request, 'Invalid amount entered')
    
    context = {
        'purchase': purchase,
        'balance_due': balance_due,
    }
    return render(request, 'pos/record_payment.html', context)

def generate_purchases_export(format, queryset):
    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="purchases_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Invoice', 'Date', 'Supplier', 'Items', 
            'Subtotal', 'Tax', 'Discount', 'Total',
            'Payment Status', 'Is Return'
        ])
        
        for purchase in queryset:
            writer.writerow([
                purchase.invoice_number,
                purchase.date.strftime('%Y-%m-%d %H:%M'),
                purchase.supplier.name,
                purchase.items.aggregate(total=Sum('quantity'))['total'] or 0,
                purchase.subtotal,
                purchase.tax,
                purchase.discount,
                purchase.total,
                'Paid' if purchase.is_paid else 'Unpaid',
                'Yes' if purchase.is_return else 'No'
            ])
        
        return response
    
    return HttpResponse('Invalid export format', status=400)

@login_required
def create_purchase_return(request):
    if request.method == 'POST':
        form = PurchaseReturnForm(request.POST)
        if form.is_valid():
            return_purchase = form.save(commit=False)
            return_purchase.is_return = True
            return_purchase.user = request.user
            return_purchase.save()
            return redirect('purchase_list')
    else:
        form = PurchaseReturnForm()
    
    # Get all purchases that can be returned (not already returns)
    purchases = Purchase.objects.filter(is_return=False).order_by('-date')
    
    return render(request, 'pos/create_purchase_return.html', {
        'form': form,
        'purchases': purchases
    })


# ============== Supplier Views ==============
@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all().order_by('name')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        suppliers = suppliers.filter(
            Q(name__icontains=search_query) |
            Q(contact_person__icontains=search_query) |
            Q(phone__icontains=search_query))
    
    # Filter by balance status
    balance_filter = request.GET.get('balance')
    if balance_filter == 'credit':
        suppliers = suppliers.filter(balance__gt=0)
    elif balance_filter == 'zero':
        suppliers = suppliers.filter(balance=0)
    
    # Export functionality
    export_format = request.GET.get('export')
    if export_format:
        return generate_suppliers_export(export_format, suppliers)
    
    context = {
        'suppliers': suppliers,
        'search_query': search_query,
        'balance_filter': balance_filter
    }
    

    supplier_purchases = Purchase.objects.filter(
        is_return=False
    ).values(
        'supplier__name'
    ).annotate(
        total_spent=Sum('total'),
        order_count=Count('id'),
        last_order=Max('date')
    ).order_by('-total_spent')
    
    context.update({
        'supplier_purchases': supplier_purchases
    })
    return render(request, 'pos/supplier_list.html', context)

@login_required
def add_supplier(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f'Supplier "{supplier.name}" added successfully!')
            return redirect('supplier_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SupplierForm()
    
    context = {
        'form': form,
        'title': 'Add New Supplier'
    }
    return render(request, 'pos/add_supplier.html', context)
@login_required
def edit_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            return redirect('supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    
    context = {
        'form': form,
        'supplier': supplier
    }
    return render(request, 'pos/edit_supplier.html', context)

@login_required
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    purchases = Purchase.objects.filter(supplier=supplier).order_by('-date')
    payments = SupplierPayment.objects.filter(supplier=supplier).order_by('-date')
    returns = Return.objects.filter(supplier=supplier).order_by('-date')
    
    # Pagination for purchases and payments
    purchase_paginator = Paginator(purchases, 10)
    purchase_page = request.GET.get('purchase_page')
    purchase_page_obj = purchase_paginator.get_page(purchase_page)
    
    payment_paginator = Paginator(payments, 10)
    payment_page = request.GET.get('payment_page')
    payment_page_obj = payment_paginator.get_page(payment_page)
    
    return_paginator = Paginator(returns, 10)
    return_page = request.GET.get('return_page')
    return_page_obj = return_paginator.get_page(return_page)
    
    context = {
        'supplier': supplier,
        'purchases': purchase_page_obj,
        'payments': payment_page_obj,
        'returns': return_page_obj
    }
    return render(request, 'pos/supplier_detail.html', context)

def generate_suppliers_export(format, queryset):
    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="suppliers.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Name', 'Contact Person', 'Phone', 'Email', 
            'Address', 'Balance'
        ])
        
        for supplier in queryset:
            writer.writerow([
                supplier.name,
                supplier.contact_person,
                supplier.phone,
                supplier.email,
                supplier.address,
                supplier.balance
            ])
        
        return response
    
    return HttpResponse('Invalid export format', status=400)

@login_required
def customer_payment_report(request):
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search_query = request.GET.get('search', '')
    
    # Start with all payments
    payments = CustomerPayment.objects.all().select_related('customer', 'sale')
    
    # Apply date filters only if dates are provided
    if start_date:
        payments = payments.filter(date__gte=start_date)
    if end_date:
        payments = payments.filter(date__lte=end_date)
    
    # Apply search filter if provided
    if search_query:
        payments = payments.filter(
            Q(customer__name__icontains=search_query) |
            Q(sale__sale_number__icontains=search_query) |
            Q(reference__icontains=search_query)
        )
    
    # Group by payment method
    by_method = payments.values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    # Group by customer
    by_customer = payments.values('customer__name').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Calculate total amount and average payment
    total_amount = payments.aggregate(total=Sum('amount'))['total'] or 0
    average_payment = total_amount / len(payments) if payments.exists() else 0
    
    context = {
        'payments': payments,
        'by_method': by_method,
        'by_customer': by_customer,
        'start_date': start_date,
        'end_date': end_date,
        'search_query': search_query,
        'total_amount': total_amount,
        'average_payment': average_payment,
    }
    return render(request, 'pos/customer_payment_report.html', context)


@login_required
def supplier_payment_report(request):
    # Date filtering
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date') or timezone.now().date()
    
    if not start_date:
        # Default to beginning of current month
        start_date = timezone.now().date().replace(day=1)
    
    payments = SupplierPayment.objects.filter(
        date__range=[start_date, end_date]
    ).select_related('supplier', 'purchase')
    
    # Group by payment method
    by_method = payments.values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    # Group by supplier
    by_supplier = payments.values('supplier__name').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    context = {
        'payments': payments,
        'by_method': by_method,
        'by_supplier': by_supplier,
        'start_date': start_date,
        'end_date': end_date,
        'total_amount': payments.aggregate(total=Sum('amount'))['total'] or 0
    }
    return render(request, 'pos/supplier_payment_report.html', context)


@login_required
def reports_dashboard(request):
    # Quick stats for dashboard
    today = timezone.now().date()
    
    # Today's sales
    today_sales = Sale.objects.filter(
        date__date=today,
        is_completed=True
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Today's expenses
    today_expenses = Expense.objects.filter(
        date__date=today
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Low stock items
    low_stock_count = Product.objects.filter(
        quantity__lte=F('reorder_level'),
        is_active=True
    ).count()
    
    # Outstanding credit
    outstanding_credit = Sale.objects.filter(
        is_credit=True,
        balance__gt=0
    ).aggregate(total=Sum('balance'))['total'] or 0
    
    context = {
        'today_sales': today_sales,
        'today_expenses': today_expenses,
        'low_stock_count': low_stock_count,
        'outstanding_credit': outstanding_credit,
    }
    return render(request, 'pos/reports_dashboard.html', context)

from .models import SupplierReturn
from .forms import SupplierReturnForm

def supplier_returns(request):
    if request.method == 'POST':
        form = SupplierReturnForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('supplier_returns_list')
    else:
        form = SupplierReturnForm()
    
    returns = SupplierReturn.objects.all().order_by('-return_date')
    return render(request, 'pos/supplier_returns.html', {
        'form': form,
        'returns': returns
    })

def process_return(request, return_id):
    supplier_return = get_object_or_404(SupplierReturn, id=return_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        supplier_return.status = new_status
        supplier_return.save()
        
        # If approved, update inventory
        if new_status == 'approved':
            product = supplier_return.product
            product.quantity += supplier_return.quantity
            product.save()
            
        return redirect('supplier_returns_list')
    
    return render(request, 'pos/process_return.html', {
        'return': supplier_return
    })


# ============== Expense Views ==============
@login_required
def expense_list(request):
    expenses = Expense.objects.all().order_by('-date')
    
    # Date filtering
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        expenses = expenses.filter(date__gte=start_date)
    if end_date:
        expenses = expenses.filter(date__lte=end_date)
    
    # Category filter
    category = request.GET.get('category')
    if category:
        expenses = expenses.filter(category=category)
    
    # Calculate total expenses
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    # Export functionality
    export_format = request.GET.get('export')
    if export_format:
        return generate_expenses_export(export_format, expenses)
    
    # Pagination
    paginator = Paginator(expenses, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    expenses_by_category = expenses.values(
        'category'
    ).annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    monthly_expenses = expenses.annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')
    
    
    
    context = {
        'expenses': page_obj,
        'total_expenses': total_expenses,
        'start_date': start_date,
        'end_date': end_date,
        'selected_category': category,
        'expenses_by_category': expenses_by_category,
        'monthly_expenses': monthly_expenses
    }
    return render(request, 'pos/expense_list.html', context)

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            return redirect('expense_list')
    else:
        form = ExpenseForm()
    
    context = {
        'form': form
    }
    return render(request, 'pos/add_expense.html', context)

@login_required
def edit_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)
    
    context = {
        'form': form,
        'expense': expense
    }
    return render(request, 'pos/edit_expense.html', context)

def generate_expenses_export(format, queryset):
    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="expenses.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Date', 'Category', 'Description', 'Amount', 'User'
        ])
        
        for expense in queryset:
            writer.writerow([
                expense.date.strftime('%Y-%m-%d'),
                expense.get_category_display(),
                expense.description,
                expense.amount,
                expense.user.username
            ])
        
        return response
    
    return HttpResponse('Invalid export format', status=400)

# ============== Discount Views ==============
@login_required
def discount_list(request):
    today = timezone.now().date()
    discounts = Discount.objects.all().order_by('-start_date')
    
    # Filter by active status
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        discounts = discounts.filter(
            is_active=True, 
            start_date__lte=today, 
            end_date__gte=today
        )
    elif status_filter == 'upcoming':
        discounts = discounts.filter(start_date__gt=today)
    elif status_filter == 'expired':
        discounts = discounts.filter(end_date__lt=today)
    
    context = {
        'discounts': discounts,
        'status_filter': status_filter
    }
    return render(request, 'pos/discount_list.html', context)

@login_required
def add_discount(request):
    if request.method == 'POST':
        form = DiscountForm(request.POST)
        if form.is_valid():
            discount = form.save()
            
            # Apply discount to selected products/categories
            if discount.discount_type == 'percentage':
                amount = discount.amount / 100
                update_func = lambda p: p.selling_price * (1 - amount)
            else:
                update_func = lambda p: max(p.selling_price - discount.amount, Decimal('0.01'))
            
            if discount.products.exists():
                for product in discount.products.all():
                    product.selling_price = update_func(product)
                    product.save()
            
            if discount.categories.exists():
                for category in discount.categories.all():
                    for product in category.product_set.all():
                        product.selling_price = update_func(product)
                        product.save()
            
            return redirect('discount_list')
    else:
        form = DiscountForm()
    
    products = Product.objects.filter(is_active=True).order_by('name')
    categories = Category.objects.all()
    
    context = {
        'form': form,
        'products': products,
        'categories': categories
    }
    return render(request, 'pos/add_discount.html', context)

@login_required
def toggle_discount_status(request, pk):
    discount = get_object_or_404(Discount, pk=pk)
    discount.is_active = not discount.is_active
    discount.save()
    return redirect('discount_list')

# ============== Company & Pricing Views ==============
@login_required
def company_settings(request):
    company = Company.objects.first()
    
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            return redirect('company_settings')
    else:
        form = CompanyForm(instance=company)
    
    context = {
        'form': form,
        'company': company
    }
    return render(request, 'pos/company_settings.html', context)

@login_required
def company_pricing(request):
    company_prices = CompanyPrice.objects.all().order_by('company__name', 'product__name')
    
    # Filter by company
    company_id = request.GET.get('company')
    if company_id:
        company_prices = company_prices.filter(company_id=company_id)
    
    companies = Company.objects.all()
    products = Product.objects.filter(is_active=True).order_by('name')
    
    context = {
        'company_prices': company_prices,
        'companies': companies,
        'products': products,
        'selected_company': company_id
    }
    return render(request, 'pos/company_pricing.html', context)

@login_required
def add_company_price(request):
    if request.method == 'POST':
        form = CompanyPriceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('company_pricing')
    else:
        form = CompanyPriceForm()
    
    companies = Company.objects.all()
    products = Product.objects.filter(is_active=True).order_by('name')
    
    context = {
        'form': form,
        'companies': companies,
        'products': products
    }
    return render(request, 'pos/add_company_price.html', context)

@login_required
def edit_company_price(request, pk):
    company_price = get_object_or_404(CompanyPrice, pk=pk)
    
    if request.method == 'POST':
        form = CompanyPriceForm(request.POST, instance=company_price)
        if form.is_valid():
            form.save()
            return redirect('company_pricing')
    else:
        form = CompanyPriceForm(instance=company_price)
    
    context = {
        'form': form,
        'company_price': company_price
    }
    return render(request, 'pos/edit_company_price.html', context)

# ============== Reports Views ==============
@login_required
def profit_loss_report(request):
    # Date filtering
    start_date = request.GET.get('start_date', (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', timezone.now().strftime('%Y-%m-%d'))
    
    # Get sales in date range
    sales = Sale.objects.filter(
        date__date__range=[start_date, end_date],
        is_completed=True
    )
    total_sales = sales.aggregate(total=Sum('total'))['total'] or 0
    
    # Calculate cost of goods sold
    sale_items = SaleItem.objects.filter(sale__in=sales)
    cogs = sale_items.annotate(
        cost=ExpressionWrapper(
            F('product__purchase_price') * F('quantity'),
            output_field=DecimalField()
        )
    ).aggregate(total=Sum('cost'))['total'] or 0
    
    # Calculate gross profit
    gross_profit = total_sales - cogs
    
    # Get expenses in date range
    expenses = Expense.objects.filter(date__range=[start_date, end_date])
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    # Group expenses by category
    expenses_by_category = expenses.values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Calculate net profit
    net_profit = gross_profit - total_expenses
    
    # Profit trend data (last 12 months)
    profit_trend = []
    for i in range(12):
        month = timezone.now().date() - timedelta(days=30*i)
        month_start = month.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_sales = Sale.objects.filter(
            date__date__range=[month_start, month_end],
            is_completed=True
        ).aggregate(total=Sum('total'))['total'] or 0
        
        month_cogs = SaleItem.objects.filter(
            sale__date__date__range=[month_start, month_end]
        ).annotate(
            cost=ExpressionWrapper(
                F('product__purchase_price') * F('quantity'),
                output_field=DecimalField()
            )
        ).aggregate(total=Sum('cost'))['total'] or 0
        
        month_expenses = Expense.objects.filter(
            date__range=[month_start, month_end]
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        month_profit = (month_sales - month_cogs) - month_expenses
        
        profit_trend.append({
            'month': month_start.strftime('%b %Y'),
            'sales': float(month_sales),
            'cogs': float(month_cogs),
            'expenses': float(month_expenses),
            'profit': float(month_profit)
        })
    
    profit_trend.reverse()  # Show oldest first
    
    context = {
        'total_sales': total_sales,
        'cogs': cogs,
        'gross_profit': gross_profit,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'expenses_by_category': expenses_by_category,
        'profit_trend': profit_trend,
        'start_date': start_date,
        'end_date': end_date
    }
    return render(request, 'pos/profit_loss_report.html', context)

@login_required
def stock_value_report(request):
    products = Product.objects.annotate(
        stock_value=ExpressionWrapper(
            F('quantity') * F('selling_price'),
            output_field=DecimalField()
        )
    ).order_by('-stock_value')
    
    # Category filter
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Calculate total stock value
    total_value = products.aggregate(total=Sum('stock_value'))['total'] or 0
    
    # Get all categories for filter dropdown
    categories = Category.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'total_value': total_value,
        'selected_category': category_id
    }
    return render(request, 'pos/stock_value_report.html', context)

# ============== Receipt Printing ==============
# views.py
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.conf import settings
from .models import Receipt, Sale

@login_required
def view_receipt(request, receipt_id):
    """View a receipt in HTML format"""
    receipt = get_object_or_404(Receipt, id=receipt_id)
    company = Company.objects.first()  # Assuming you have a Company model
    
    context = {
        'receipt': receipt,
        'company': company,
        'sale': receipt.sale,
        'items': receipt.content.get('items', []),
        'payment_details': receipt.content.get('payment_details', {}),
    }
    
    return render(request, 'pos/receipt.html', context)

@login_required
def print_receipt(request, receipt_id):
    """View optimized for printing"""
    receipt = get_object_or_404(Receipt, id=receipt_id)
    company = Company.objects.first()
    
    context = {
        'receipt': receipt,
        'company': company,
        'sale': receipt.sale,
        'items': receipt.content.get('items', []),
        'payment_details': receipt.content.get('payment_details', {}),
        'print_directly': True,  # Flag for template to optimize for printing
    }
    
    return render(request, 'pos/receipt_print.html', context)

@login_required
def generate_receipt(request, sale_id):
    """Generate a receipt for a sale"""
    sale = get_object_or_404(Sale, id=sale_id)
    
    # Generate receipt number (you might want a better system)
    today = timezone.now().date()
    last_receipt = Receipt.objects.filter(
        created_at__date=today
    ).order_by('-id').first()
    
    next_num = 1
    if last_receipt:
        try:
            last_num = int(last_receipt.receipt_number.split('-')[-1])
            next_num = last_num + 1
        except:
            pass
    
    receipt_number = f"RCP-{today.strftime('%Y%m%d')}-{next_num:04d}"
    
    # Prepare receipt content
    receipt_content = {
        'sale_number': sale.sale_number,
        'date': sale.date.strftime('%Y-%m-%d %H:%M:%S'),
        'customer': sale.customer.name if sale.customer else 'Walk-in Customer',
        'items': [{
            'name': item.product.name,
            'quantity': item.quantity,
            'price': str(item.price),
            'total': str(item.total),
            'batch': item.batch.batch_number if item.batch else '',
        } for item in sale.items.all()],
        'subtotal': str(sale.subtotal),
        'discount': str(sale.discount_amount),
        'total': str(sale.total),
        'payment_method': sale.get_payment_method_display(),
        'payment_details': {
            'cash': str(sale.cash_amount),
            'mpesa': str(sale.mpesa_amount),
            'card': str(sale.card_amount),
            'cheque': str(sale.cheque_amount),
        },
        'amount_paid': str(sale.amount_paid),
        'change': str(max(sale.amount_paid - sale.total, Decimal(0))),
        'balance': str(sale.balance),
    }
    
    # Create receipt record
    receipt = Receipt.objects.create(
        receipt_number=receipt_number,
        receipt_type='sale',
        sale=sale,
        content=receipt_content,
        created_by=request.user
    )
    
    return JsonResponse({
        'success': True,
        'receipt_id': receipt.id,
        'receipt_number': receipt.receipt_number,
        'print_url': reverse('print_receipt', args=[receipt.id]),
    })

@login_required
def receipt_history(request):
    """View receipt history"""
    receipts = Receipt.objects.all().order_by('-created_at')
    
    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        receipts = receipts.filter(created_at__date__gte=start_date)
    if end_date:
        receipts = receipts.filter(created_at__date__lte=end_date)
    
    # Filter by receipt type
    receipt_type = request.GET.get('type')
    if receipt_type:
        receipts = receipts.filter(receipt_type=receipt_type)
    
    # Filter by printed status
    printed = request.GET.get('printed')
    if printed == 'yes':
        receipts = receipts.filter(is_printed=True)
    elif printed == 'no':
        receipts = receipts.filter(is_printed=False)
    
    # Pagination
    paginator = Paginator(receipts, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'receipts': page_obj,
        'start_date': start_date,
        'end_date': end_date,
        'selected_type': receipt_type,
        'selected_printed': printed,
    }
    
    return render(request, 'pos/receipt_history.html', context)


    
# ============== AJAX & Utility Views ==============
@login_required
@login_required
@require_GET
def search_products(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(
        Q(name__icontains=query) | Q(barcode__icontains=query),
        is_active=True,
        quantity__gt=0
    ).order_by('name')[:10]
    
    results = [{
        'id': p.id,
        'name': p.name,
        'price': str(p.selling_price),
        'purchase_price': str(p.purchase_price),  # Added purchase_price
        'wholesale_price': str(p.wholesale_price) if hasattr(p, 'wholesale_price') else '',
        'wholesale_min_quantity': p.wholesale_min_quantity if hasattr(p, 'wholesale_min_quantity') else 0,
        'quantity': p.quantity,
        'barcode': p.barcode or ''
    } for p in products]
    
    return JsonResponse(results, safe=False)

@login_required
@require_POST
def search_customers(request):
    query = request.POST.get('q', '')
    
    if query:
        customers = Customer.objects.filter(
            Q(name__icontains=query) |
            Q(phone__icontains=query)
        ).order_by('name')[:10]
    else:
        customers = Customer.objects.none()
    
    results = [{
        'id': c.id,
        'name': c.name,
        'phone': c.phone or '',
        'balance': str(c.balance)
    } for c in customers]
    
    return JsonResponse(results, safe=False)

@login_required
@require_GET
def get_product_details(request, pk):
    product = get_object_or_404(Product, pk=pk)
    sale_type = request.GET.get('sale_type', 'retail')
    
    price = product.selling_price
    if sale_type == 'wholesale' and hasattr(product, 'wholesale_price'):
        price = product.wholesale_price
    
    data = {
        'id': product.id,
        'name': product.name,
        'price': str(price),
        'quantity': product.quantity,
        'batches': [{
            'id': b.id,
            'batch_number': b.batch_number,
            'quantity': b.quantity,
            'expiry_date': b.expiry_date.strftime('%Y-%m-%d') if b.expiry_date else ''
        } for b in product.batches.filter(quantity__gt=0)]
    }
    
    return JsonResponse(data)

@login_required
@require_GET
def get_customer_details(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    
    data = {
        'id': customer.id,
        'name': customer.name,
        'phone': customer.phone or '',
        'credit_limit': str(customer.credit_limit),
        'balance': str(customer.balance)
    }
    
    return JsonResponse(data)

@login_required
@require_GET
def get_purchase_items(request, purchase_id):
    purchase = get_object_or_404(Purchase, pk=purchase_id)
    items = purchase.items.all()
    
    results = [{
        'id': item.id,
        'product_id': item.product.id,
        'product_name': item.product.name,
        'batch_id': item.batch.id if item.batch else None,
        'batch_number': item.batch.batch_number if item.batch else '',
        'quantity': item.quantity,
        'price': str(item.price),
        'max_returnable': item.quantity - (item.returned_quantity if hasattr(item, 'returned_quantity') else 0)
    } for item in items]
    
    return JsonResponse(results, safe=False)

# ============== Bulk Upload Views ==============
import pandas as pd
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Product, Category, Supplier, Customer
import re
from datetime import datetime

@login_required
def bulk_upload(request):
    if request.method == 'POST':
        form = BulkUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                file = request.FILES['file']
                model_type = form.cleaned_data['model_type']
                
                # Read the Excel file
                try:
                    df = pd.read_excel(file)
                    # Convert all columns to string to handle mixed types
                    df = df.astype(str)
                except Exception as e:
                    messages.error(request, f'Error reading Excel file: {str(e)}')
                    return redirect('bulk_upload')
                
                records_created = 0
                errors = []
                
                def clean_numeric(value, default=0):
                    """Extract numeric value from strings like '38 pcs'"""
                    if pd.isna(value) or value == 'nan' or value == 'None':
                        return default
                    try:
                        # Extract first numeric part
                        match = re.search(r'(\d+\.?\d*)', str(value))
                        if match:
                            return Decimal(match.group(1))
                        return Decimal(value)
                    except:
                        return default
                
                def clean_text(value):
                    """Clean text fields"""
                    if pd.isna(value) or value == 'nan' or value == 'None':
                        return ''
                    return str(value).strip()
                
                # PRODUCT IMPORT
                if model_type == 'product':
                    required_fields = ['Name', 'Purchase Price', 'Selling Price']
                    for field in required_fields:
                        if field not in df.columns:
                            messages.error(request, f'Missing required column: {field}')
                            return redirect('bulk_upload')
                    
                    for index, row in df.iterrows():
                        try:
                            # Required fields
                            name = clean_text(row.get('Name'))
                            if not name:
                                errors.append(f"Row {index+1}: Missing product name")
                                continue
                                
                            purchase_price = clean_numeric(row.get('Purchase Price'))
                            selling_price = clean_numeric(row.get('Selling Price'))
                            
                            # Optional fields with defaults
                            wholesale_price = clean_numeric(row.get('Wholesale Price', selling_price))
                            quantity = int(clean_numeric(row.get('Qty', 0)))
                            reorder_level = int(clean_numeric(row.get('Reorder Level', 5)))
                            barcode = clean_text(row.get('Barcode', ''))
                            category_name = clean_text(row.get('Category', 'Uncategorized'))
                            
                            # Get or create category
                            category = None
                            if category_name:
                                category, _ = Category.objects.get_or_create(name=category_name)
                            
                            # Handle supplier if provided
                            supplier = None
                            supplier_name = clean_text(row.get('Supplier'))
                            if supplier_name:
                                supplier, _ = Supplier.objects.get_or_create(name=supplier_name)
                            
                            # Create product
                            Product.objects.create(
                                name=name,
                                barcode=barcode,
                                category=category,
                                purchase_price=purchase_price,
                                selling_price=selling_price,
                                wholesale_price=wholesale_price,
                                quantity=quantity,
                                reorder_level=reorder_level,
                                supplier=supplier,
                                is_active=True
                            )
                            records_created += 1
                            
                        except Exception as e:
                            errors.append(f"Row {index+1}: {str(e)}")
                
                # CUSTOMER IMPORT
                elif model_type == 'customer':
                    required_fields = ['Name']
                    for field in required_fields:
                        if field not in df.columns:
                            messages.error(request, f'Missing required column: {field}')
                            return redirect('bulk_upload')
                    
                    for index, row in df.iterrows():
                        try:
                            name = clean_text(row.get('Name'))
                            if not name:
                                errors.append(f"Row {index+1}: Missing customer name")
                                continue
                                
                            Customer.objects.create(
                                name=name,
                                phone=clean_text(row.get('Phone', '')),
                                email=clean_text(row.get('Email', '')),
                                address=clean_text(row.get('Address', '')),
                                credit_limit=clean_numeric(row.get('Credit Limit', 0))
                            )
                            records_created += 1
                            
                        except Exception as e:
                            errors.append(f"Row {index+1}: {str(e)}")
                
                # SUPPLIER IMPORT
                elif model_type == 'supplier':
                    required_fields = ['Name']
                    for field in required_fields:
                        if field not in df.columns:
                            messages.error(request, f'Missing required column: {field}')
                            return redirect('bulk_upload')
                    
                    for index, row in df.iterrows():
                        try:
                            name = clean_text(row.get('Name'))
                            if not name:
                                errors.append(f"Row {index+1}: Missing supplier name")
                                continue
                                
                            Supplier.objects.create(
                                name=name,
                                contact_person=clean_text(row.get('Contact Person', '')),
                                phone=clean_text(row.get('Phone', '')),
                                email=clean_text(row.get('Email', '')),
                                address=clean_text(row.get('Address', '')),
                                balance=0
                            )
                            records_created += 1
                            
                        except Exception as e:
                            errors.append(f"Row {index+1}: {str(e)}")
                
                # Results handling
                if errors:
                    messages.warning(request, f"Completed with {len(errors)} errors. {records_created} records imported successfully.")
                    request.session['bulk_upload_errors'] = errors[:50]  # Limit to 50 errors
                else:
                    messages.success(request, f'Successfully imported {records_created} {model_type} records!')
                
                return redirect('bulk_upload')
            
            except Exception as e:
                messages.error(request, f'System error during import: {str(e)}')
                return redirect('bulk_upload')
        else:
            messages.error(request, 'Invalid form submission')
            return redirect('bulk_upload')
    
    else:
        form = BulkUploadForm()
    
    # Get errors from session if they exist
    errors = request.session.pop('bulk_upload_errors', [])
    
    return render(request, 'pos/bulk_upload.html', {
        'form': form,
        'errors': errors
    })
    
# ============== Authentication Views ==============
from django.contrib.auth import logout
from django.shortcuts import redirect

def custom_logout(request):
    logout(request)
    return redirect('login')

# ============== Reports Dashboard ==============
@login_required
def reports_dashboard(request):
    """Main reports dashboard that links to all report types"""
    return render(request, 'pos/reports_dashboard.html')

from django.db.models import Sum, Count, F, Q
from django.db.models.functions import TruncDate
from datetime import timedelta
from decimal import Decimal

@login_required
def dashboard(request):
    # Date range handling
    date_range = request.GET.get('range', '30d')
    
    if date_range == '7d':
        days = 7
        start_date = timezone.now() - timedelta(days=days)
    elif date_range == '90d':
        days = 90
        start_date = timezone.now() - timedelta(days=days)
    elif date_range == 'ytd':
        start_date = timezone.now().replace(month=1, day=1)
    else:
        days = 30
        start_date = timezone.now() - timedelta(days=days)
    
    end_date = timezone.now()
    
    # Today's sales data
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    today_sales = Sale.objects.filter(
        date__date=today,
        is_completed=True
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    yesterday_sales = Sale.objects.filter(
        date__date=yesterday,
        is_completed=True
    ).aggregate(total=Sum('total'))['total'] or Decimal('0.01')
    
    today_vs_yesterday = float(((today_sales - yesterday_sales) / yesterday_sales) * 100) if yesterday_sales != 0 else 0
    
    # Monthly sales data
    this_month = timezone.now().date().replace(day=1)
    last_month = (this_month - timedelta(days=1)).replace(day=1)
    
    monthly_sales = Sale.objects.filter(
        date__date__gte=this_month,
        is_completed=True
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    last_month_sales = Sale.objects.filter(
        date__date__gte=last_month,
        date__date__lt=this_month,
        is_completed=True
    ).aggregate(total=Sum('total'))['total'] or Decimal('0.01')
    
    monthly_vs_last = float(((monthly_sales - last_month_sales) / last_month_sales) * 100) if last_month_sales != 0 else 0
    
    # Low stock items
    low_stock_count = Product.objects.filter(
        quantity__lte=F('reorder_level'),
        is_active=True
    ).count()
    
    # Outstanding credit
    outstanding_credit = Sale.objects.filter(
        is_credit=True,
        balance__gt=0
    ).aggregate(total=Sum('balance'))['total'] or Decimal('0')
    
    # Recent sales
    recent_sales = Sale.objects.filter(
        is_completed=True
    ).order_by('-date')[:10]
    
    # Sales trend data
    sales_trend = Sale.objects.filter(
        date__date__gte=start_date,
        is_completed=True
    ).annotate(
        day=TruncDate('date')
    ).values('day').annotate(
        total=Sum('total')
    ).order_by('day')
    
    sales_trend_labels = [sale['day'].strftime('%b %d') for sale in sales_trend]
    sales_trend_data = [float(sale['total'] or 0) for sale in sales_trend]
    
    # Payment methods breakdown
    payment_methods = Sale.objects.filter(
        date__date__gte=start_date,
        is_completed=True
    ).values('payment_method').annotate(
        total=Sum('total'),
        count=Count('id')
    ).order_by('-total')
    
    payment_method_labels = []
    payment_method_data = []
    payment_method_colors = []
    payment_method_colors_hover = []
    
    colors = {
        'cash': ['#4e73df', '#2e59d9'],
        'mpesa': ['#1cc88a', '#17a673'],
        'card': ['#36b9cc', '#2c9faf'],
        'cheque': ['#f6c23e', '#dda20a'],
        'credit': ['#e74a3b', '#be2617']
    }
    
    for method in payment_methods:
        payment_method_labels.append(method['payment_method'].capitalize())
        payment_method_data.append(float(method['total'] or 0))
        payment_method_colors.append(colors.get(method['payment_method'], ['#858796'])[0])
        payment_method_colors_hover.append(colors.get(method['payment_method'], ['#707384'])[0])
    
    # SIMPLIFIED: Fast moving products (just get top 5 by quantity sold)
    fast_moving_products = Product.objects.filter(
        saleitem__sale__date__date__gte=start_date,
        saleitem__sale__is_completed=True
    ).annotate(
        total_sold=Sum('saleitem__quantity')
    ).order_by('-total_sold')[:5]
    
    # SIMPLIFIED: Slow moving products (products not sold in last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    slow_moving_products = Product.objects.filter(
        is_active=True,
        quantity__gt=0
    ).exclude(
        saleitem__sale__date__gte=thirty_days_ago,
        saleitem__sale__is_completed=True
    ).order_by('?')[:5]  # Random 5 products
    
    context = {
        'today_sales': today_sales,
        'today_vs_yesterday': today_vs_yesterday,
        'today_vs_yesterday_abs': abs(today_vs_yesterday),
        'monthly_sales': monthly_sales,
        'monthly_vs_last': monthly_vs_last,
        'monthly_vs_last_abs': abs(monthly_vs_last),
        'low_stock_count': low_stock_count,
        'outstanding_credit': outstanding_credit,
        'recent_sales': recent_sales,
        'sales_trend_labels': sales_trend_labels,
        'sales_trend_data': sales_trend_data,
        'payment_method_labels': payment_method_labels,
        'payment_method_data': payment_method_data,
        'payment_method_colors': payment_method_colors,
        'payment_method_colors_hover': payment_method_colors_hover,
        'payment_methods': [
            {'name': m['payment_method'].capitalize(), 'color': colors.get(m['payment_method'], ['#858796'])[0]}
            for m in payment_methods
        ],
        'fast_moving_products': fast_moving_products,
        'slow_moving_products': slow_moving_products,
    }
    return render(request, 'pos/dashboard.html', context)

from django.http import JsonResponse
from .models import Product, CompanyPrice

def get_product_pricing(request, pk):
    try:
        product = Product.objects.get(pk=pk)
        company_id = request.GET.get('company_id')
        
        if company_id:
            try:
                company_price = CompanyPrice.objects.get(
                    product=product, 
                    company_id=company_id
                )
                price = company_price.price
            except CompanyPrice.DoesNotExist:
                price = product.selling_price
        else:
            price = product.selling_price
        
        response_data = {
            'product_id': product.id,
            'selling_price': str(product.selling_price),
            'wholesale_price': str(product.wholesale_price),
            'wholesale_min_quantity': product.wholesale_min_quantity,
            'final_price': str(price),
            'quantity': product.quantity
        }
        
        return JsonResponse(response_data)
    
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    



from django.shortcuts import render
from django.utils import timezone
from .models import Sale, Purchase, Expense
from datetime import timedelta

def reports(request):
    # Default to last 30 days
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Get filter parameters from request
    report_type = request.GET.get('type', 'sales')
    date_range = request.GET.get('range', '30d')
    
    # Adjust date range based on selection
    if date_range == '7d':
        start_date = end_date - timedelta(days=7)
    elif date_range == '90d':
        start_date = end_date - timedelta(days=90)
    elif date_range == 'ytd':
        start_date = end_date.replace(month=1, day=1)
    
    # Generate report data based on type
    if report_type == 'sales':
        data = Sale.objects.filter(
            date__range=[start_date, end_date]
        ).order_by('-date')
        title = "Sales Report"
    elif report_type == 'purchases':
        data = Purchase.objects.filter(
            date__range=[start_date, end_date]
        ).order_by('-date')
        title = "Purchases Report"
    elif report_type == 'expenses':
        data = Expense.objects.filter(
            date__range=[start_date, end_date]
        ).order_by('-date')
        title = "Expenses Report"
    else:
        data = []
        title = "Report"
    
    context = {
        'report_type': report_type,
        'date_range': date_range,
        'start_date': start_date,
        'end_date': end_date,
        'data': data,
        'title': title
    }
    
    return render(request, 'pos/reports.html', context)


from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, Count, Q
from .models import Sale, Expense, Purchase, Customer
from datetime import datetime, timedelta
import csv
from django.http import HttpResponse

# views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum, Count, Q
from .models import Sale, Customer
from datetime import datetime, timedelta
import csv
from django.http import HttpResponse
from django.core.paginator import Paginator

def daily_sales_report(request):
    # Date filter - default to last 7 days
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    try:
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date() if date_from else None
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else None
    except:
        date_from = date_to = None
    
    if not date_from and not date_to:
        date_to = datetime.now().date()
        date_from = date_to - timedelta(days=7)
    
    # Base queryset with date filter
    sales = Sale.objects.filter(
        date__date__gte=date_from,
        date__date__lte=date_to,
        is_completed=True
    ).select_related('customer', 'user').prefetch_related('items')
    
    # Apply additional filters
    payment_method = request.GET.get('payment_method')
    if payment_method:
        if payment_method == 'credit':
            sales = sales.filter(is_credit=True)
        else:
            sales = sales.filter(payment_method=payment_method)
    
    customer_id = request.GET.get('customer')
    if customer_id:
        sales = sales.filter(customer_id=customer_id)
    
    min_amount = request.GET.get('min_amount')
    if min_amount:
        sales = sales.filter(total__gte=float(min_amount))
    
    # Calculate totals
    totals = sales.aggregate(
        total_sales=Sum('total'),
        total_items=Sum('items__quantity'),
        transaction_count=Count('id')
    )
    
    # Calculate average sale
    if totals['transaction_count'] and totals['total_sales']:
        average_sale = totals['total_sales'] / totals['transaction_count']
    else:
        average_sale = 0
    
    # Get top customer
    top_customer = sales.values('customer__name').annotate(
        total=Sum('total')
    ).order_by('-total').first()
    
    # Pagination
    paginator = Paginator(sales.order_by('-date'), 25)  # Show 25 sales per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all customers for filter dropdown
    customers = Customer.objects.all().order_by('name')
    
    context = {
        'sales': page_obj,
        'customers': customers,
        'date_from': date_from.strftime('%Y-%m-%d') if date_from else '',
        'date_to': date_to.strftime('%Y-%m-%d') if date_to else '',
        'totals': totals,
        'average_sale': average_sale,
        'top_customer': top_customer,
        'payment_methods': [
            ('cash', 'Cash'),
            ('mpesa', 'M-Pesa'),
            ('card', 'Card'),
            ('credit', 'Credit')
        ],
        'selected_payment_method': payment_method,
        'selected_customer': customer_id,
        'selected_min_amount': min_amount
    }
    return render(request, 'pos/daily_sales_report.html', context)

def export_daily_sales(request):
    # Get filter parameters from request
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    payment_method = request.GET.get('payment_method')
    customer_id = request.GET.get('customer')
    min_amount = request.GET.get('min_amount')

    # Initialize base queryset
    sales = Sale.objects.filter(is_completed=True)
    
    # Apply date filters only if dates are provided
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            sales = sales.filter(date__date__gte=date_from)
        except ValueError:
            pass  # Invalid date format, skip this filter

    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            sales = sales.filter(date__date__lte=date_to)
        except ValueError:
            pass  # Invalid date format, skip this filter

    # Apply payment method filter
    if payment_method:
        if payment_method == 'credit':
            sales = sales.filter(is_credit=True)
        else:
            sales = sales.filter(payment_method=payment_method)

    # Apply customer filter
    if customer_id:
        sales = sales.filter(customer_id=customer_id)

    # Apply minimum amount filter
    if min_amount:
        try:
            sales = sales.filter(total__gte=float(min_amount))
        except (ValueError, TypeError):
            pass  # Invalid amount, skip this filter

    # Order the results
    sales = sales.order_by('-date').select_related('customer', 'user').prefetch_related('items')

    # Generate filename with date range if available
    filename = "sales_export"
    if date_from and date_to:
        filename += f"_{date_from}_to_{date_to}"
    elif date_from:
        filename += f"_from_{date_from}"
    elif date_to:
        filename += f"_to_{date_to}"
    filename += ".csv"

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Write headers - removed discount and tax_amount since they don't exist
    writer.writerow([
        'Receipt Number', 'Date', 'Time', 'Customer', 'Customer Phone', 
        'Items Count', 'Total Amount', 'Payment Method', 'Is Credit', 
        'Cashier'  # Removed: 'Discount', 'Tax Amount'
    ])
    
    # Write data rows
    for sale in sales:
        writer.writerow([
            sale.sale_number,
            sale.date.date(),
            sale.date.time(),
            sale.customer.name if sale.customer else 'Walk-in',
            sale.customer.phone if sale.customer else '',
            sale.items.count(),
            sale.total,
            sale.get_payment_method_display(),
            'Yes' if sale.is_credit else 'No',
            sale.user.get_full_name() or sale.user.username,
            # Removed: sale.discount if hasattr(sale, 'discount') else 0,
            # Removed: sale.tax_amount if hasattr(sale, 'tax_amount') else 0
        ])
    
    return response

from .forms import StockJournalForm
from .models import StockJournal

@login_required
def stock_journal_list(request):
    journals = StockJournal.objects.all().select_related('product', 'batch', 'user').order_by('-date')
    
    # Filtering
    product_id = request.GET.get('product')
    movement_type = request.GET.get('movement_type')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if product_id:
        journals = journals.filter(product_id=product_id)
    if movement_type:
        journals = journals.filter(movement_type=movement_type)
    if start_date:
        journals = journals.filter(date__date__gte=start_date)
    if end_date:
        journals = journals.filter(date__date__lte=end_date)
    
    # Export functionality
    export_format = request.GET.get('export')
    if export_format == 'csv':
        return generate_stock_journal_export(journals)
    
    # Pagination
    paginator = Paginator(journals, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    products = Product.objects.filter(is_active=True).order_by('name')
    
    context = {
        'journals': page_obj,
        'products': products,
        'movement_types': StockJournal.MOVEMENT_TYPES,
        'selected_product': product_id,
        'selected_movement_type': movement_type,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'pos/stock_journal_list.html', context)

@login_required
def add_stock_journal(request):
    if request.method == 'POST':
        form = StockJournalForm(request.POST)
        if form.is_valid():
            journal = form.save(commit=False)
            journal.user = request.user
            
            # Update product quantity based on movement type
            product = journal.product
            if journal.movement_type == 'in':
                product.quantity += journal.quantity
            elif journal.movement_type == 'out':
                product.quantity -= journal.quantity
            product.save()
            
            # Update batch quantity if batch is specified
            if journal.batch:
                batch = journal.batch
                if journal.movement_type == 'in':
                    batch.quantity += journal.quantity
                elif journal.movement_type == 'out':
                    batch.quantity -= journal.quantity
                batch.save()
            
            journal.save()
            messages.success(request, 'Stock movement recorded successfully!')
            return redirect('stock_journal_list')
    else:
        form = StockJournalForm()
    
    context = {
        'form': form,
        'title': 'Record Stock Movement'
    }
    return render(request, 'pos/add_stock_journal.html', context)

def generate_stock_journal_export(queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="stock_journal.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Date', 'Product', 'Batch', 'Movement Type', 
        'Quantity', 'Reference', 'Notes', 'User'
    ])
    
    for journal in queryset:
        writer.writerow([
            journal.date.strftime('%Y-%m-%d %H:%M'),
            journal.product.name,
            journal.batch.batch_number if journal.batch else '',
            journal.get_movement_type_display(),
            journal.quantity,
            journal.reference,
            journal.notes,
            journal.user.username
        ])
    
    return response


from django.http import JsonResponse
from django.template.loader import render_to_string

@login_required
def get_batches_for_product(request):
    product_id = request.GET.get('product_id')
    batches = Batch.objects.filter(product_id=product_id).order_by('-expiry_date')
    
    options = '<option value="">---------</option>'
    for batch in batches:
        options += f'<option value="{batch.id}">{batch.batch_number} (Exp: {batch.expiry_date}) - Qty: {batch.quantity}</option>'
    
    return JsonResponse({'options': options})




import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
from .forms import ProductImportForm

@login_required
def import_products(request):
    if request.method == 'POST':
        form = ProductImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                df = pd.read_excel(request.FILES['file'])
                # Replace NaN values with None
                df = df.where(pd.notnull(df), None)
                
                update_existing = form.cleaned_data['update_existing']
                records_created = 0
                records_updated = 0
                errors = []
                
                with transaction.atomic():
                    for index, row in df.iterrows():
                        try:
                            # Required fields
                            name = row.get('Name')
                            if not name:
                                errors.append(f"Row {index+1}: Missing product name")
                                continue
                                
                            # Get or create category
                            category_name = row.get('Category')
                            category = None
                            if category_name:
                                category, _ = Category.objects.get_or_create(name=category_name)
                            
                            # Get or create supplier
                            supplier_name = row.get('Supplier')
                            supplier = None
                            if supplier_name:
                                supplier, _ = Supplier.objects.get_or_create(name=supplier_name)
                            
                            # Convert prices to Decimal
                            purchase_price = Decimal(str(row.get('Purchase Price', 0))) if row.get('Purchase Price') is not None else Decimal(0)
                            selling_price = Decimal(str(row.get('Selling Price', 0))) if row.get('Selling Price') is not None else Decimal(0)
                            wholesale_price = Decimal(str(row.get('Wholesale Price', selling_price))) if row.get('Wholesale Price') is not None else selling_price
                            
                            # Default values
                            defaults = {
                                'category': category,
                                'supplier': supplier,
                                'purchase_price': purchase_price,
                                'selling_price': selling_price,
                                'wholesale_price': wholesale_price,
                                'wholesale_min_quantity': int(row.get('Wholesale Min Quantity', 0)),
                                'quantity': int(row.get('Quantity', 0)),
                                'reorder_level': int(row.get('Reorder Level', 5)),
                                'barcode': row.get('Barcode', ''),
                                'is_active': bool(row.get('Is Active', True))
                            }
                            
                            if update_existing:
                                product, created = Product.objects.update_or_create(
                                    name=name,
                                    defaults=defaults
                                )
                                if created:
                                    records_created += 1
                                else:
                                    records_updated += 1
                            else:
                                # Only create new products
                                if Product.objects.filter(name=name).exists():
                                    errors.append(f"Row {index+1}: Product '{name}' already exists")
                                    continue
                                    
                                Product.objects.create(name=name, **defaults)
                                records_created += 1
                                
                        except Exception as e:
                            errors.append(f"Row {index+1}: {str(e)}")
                
                if errors:
                    messages.warning(request, f"Import completed with {len(errors)} errors")
                    # You might want to save these errors to display to the user
                else:
                    messages.success(request, f'Successfully imported {records_created} products! {records_updated} updated.' if update_existing else f'Successfully imported {records_created} products!')
                return redirect('product_list')
            
            except Exception as e:
                messages.error(request, f'Error during import: {str(e)}')
    else:
        form = ProductImportForm()
    
    return render(request, 'pos/import_products.html', {'form': form})  



@login_required
def opening_closing_stock_report(request):
    # Date filtering
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date') or timezone.now().date()
    
    if not start_date:
        # Default to beginning of current month
        start_date = timezone.now().date().replace(day=1)
    
    # Get products
    products = Product.objects.filter(is_active=True).order_by('name')
    
    # Calculate stock movements during period
    stock_movements = StockJournal.objects.filter(
        date__date__range=[start_date, end_date]
    ).values('product').annotate(
        stock_in=Sum('quantity', filter=Q(movement_type='in')),
        stock_out=Sum('quantity', filter=Q(movement_type='out'))
    )
    
    movement_dict = {movement['product']: movement for movement in stock_movements}
    
    report_data = []
    total_opening_stock = 0
    total_stock_in = 0
    total_stock_out = 0
    total_closing_stock = 0
    total_opening_value = 0
    total_closing_value = 0
    
    for product in products:
        movements = movement_dict.get(product.id, {})
        opening_stock = product.quantity - (movements.get('stock_in', 0) or 0) + (movements.get('stock_out', 0) or 0)
        closing_stock = product.quantity
        stock_in = movements.get('stock_in', 0) or 0
        stock_out = movements.get('stock_out', 0) or 0
        value_change = (closing_stock - opening_stock) * product.purchase_price
        
        report_data.append({
            'product': product,
            'opening_stock': max(opening_stock, 0),
            'closing_stock': closing_stock,
            'stock_in': stock_in,
            'stock_out': stock_out,
            'value_change': value_change
        })
        
        # Update totals
        total_opening_stock += max(opening_stock, 0)
        total_stock_in += stock_in
        total_stock_out += stock_out
        total_closing_stock += closing_stock
        total_opening_value += max(opening_stock, 0) * product.purchase_price
        total_closing_value += closing_stock * product.purchase_price
    
    context = {
        'report_data': report_data,
        'start_date': start_date,
        'end_date': end_date,
        'total_opening_stock': total_opening_stock,
        'total_stock_in': total_stock_in,
        'total_stock_out': total_stock_out,
        'total_closing_stock': total_closing_stock,
        'total_opening_value': total_opening_value,
        'total_closing_value': total_closing_value,
        'total_value_change': total_closing_value - total_opening_value
    }
    return render(request, 'pos/opening_closing_stock.html', context)