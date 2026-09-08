# reports.py - Create this new file in your app directory
from django.db.models import (
    Sum, Count, Avg, Max, Min, F, Q, ExpressionWrapper, 
    DecimalField, Value, Case, When, CharField, IntegerField
)
from django.db.models.functions import TruncDate, TruncMonth, TruncYear, Coalesce
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
import json

from .models import (
    Sale, SaleItem, Purchase, PurchaseItem, Product, 
    Customer, Supplier, Expense, StockJournal,
    CustomerPayment, SupplierPayment
)

class ReportGenerator:
    """Base class for report generation"""
    
    def __init__(self, request):
        self.request = request
        self.filters = {}
        self.parse_filters()
    
    def parse_filters(self):
        """Parse common filters from request"""
        self.filters = {
            'start_date': self.request.GET.get('start_date'),
            'end_date': self.request.GET.get('end_date'),
            'category': self.request.GET.get('category'),
            'supplier': self.request.GET.get('supplier'),
            'customer': self.request.GET.get('customer'),
            'payment_method': self.request.GET.get('payment_method'),
            'product': self.request.GET.get('product'),
        }
        
        # Set default date range if not provided
        if not self.filters['start_date']:
            self.filters['start_date'] = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not self.filters['end_date']:
            self.filters['end_date'] = timezone.now().strftime('%Y-%m-%d')
    
    def apply_date_filter(self, queryset, date_field='date'):
        """Apply date filter to queryset"""
        if self.filters['start_date']:
            queryset = queryset.filter(**{f'{date_field}__date__gte': self.filters['start_date']})
        if self.filters['end_date']:
            queryset = queryset.filter(**{f'{date_field}__date__lte': self.filters['end_date']})
        return queryset