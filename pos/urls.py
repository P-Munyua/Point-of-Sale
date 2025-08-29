from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # POS & Sales
    path('pos/', views.pos, name='pos'),
    path('process-sale/', views.process_sale, name='process_sale'),
    path('save-pending-sale/', views.save_pending_sale, name='save_pending_sale'),
    path('pending-sales/', views.pending_sales_list, name='pending_sales_list'),
    path('pending-sales/<int:pk>/', views.view_pending_sale, name='view_pending_sale'),
    path('pending-sales/<int:pk>/complete/', views.complete_pending_sale, name='complete_pending_sale'),
    path('pending-sales/<int:pk>/delete/', views.delete_pending_sale, name='delete_pending_sale'),
    path('edit-sale/<int:pk>/', views.edit_sale, name='edit_sale'),
    path('sale/<int:pk>/', views.sale_detail, name='sale_detail'),
    path('sales/<int:pk>/', views.view_sale, name='view_sale'),
    path('receipt/<int:receipt_id>/', views.view_receipt, name='view_receipt'),
    path('receipt/<int:receipt_id>/print/', views.print_receipt, name='print_receipt'),
    path('sale/<int:sale_id>/generate-receipt/', views.generate_receipt, name='generate_receipt'),
    path('receipts/', views.receipt_history, name='receipt_history'),
    path('load-pending-sale/<int:pk>/', views.load_pending_sale, name='load_pending_sale'),
    
    # Credit Payments
    path('credit-payments/', views.credit_payments, name='credit_payments'),
    path('credit-payments/<int:pk>/process/', views.process_credit_payment, name='process_credit_payment'),
    

    # Products & Inventory
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/edit/<int:pk>/', views.edit_product, name='edit_product'),
    path('products/toggle/<int:pk>/', views.toggle_product_status, name='toggle_product_status'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('inventory/', views.inventory_report, name='inventory_report'),
    path('bulk-upload/', views.bulk_upload, name='bulk_upload'),
    path('products/import/', views.import_products, name='import_products'),

    # Batch Management
    path('batches/', views.batch_list, name='batch_list'),
    path('batches/add/', views.add_batch, name='add_batch'),
    path('batches/edit/<int:pk>/', views.edit_batch, name='edit_batch'),
    
    # Customers
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.add_customer, name='add_customer'),
    path('customers/edit/<int:pk>/', views.edit_customer, name='edit_customer'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/payment/', views.customer_payment, name='customer_payment'),
    
    # Sales Reports
    path('sales/', views.sales_report, name='sales_report'),
    path('sales/daily/', views.daily_sales_summary, name='daily_sales_summary'),
    path('sales/daily/', views.daily_sales_report, name='daily_sales_report'),
    path('reports/', views.reports_dashboard, name='reports_dashboard'),
    path('reports/opening-closing-stock/', views.opening_closing_stock_report, name='opening_closing_stock_report'),
    path('reports/profit-margin/', views.profit_margin_report, name='profit_margin_report'),
    path('reports/customer-payments/', views.customer_payment_report, name='customer_payment_report'),
    path('reports/supplier-payments/', views.supplier_payment_report, name='supplier_payment_report'),


    # Purchases & Returns
    # Purchases & Returns
path('purchases/', views.purchase_list, name='purchase_list'),
path('purchases/add/', views.add_purchase, name='add_purchase'),
path("purchases/edit/<int:pk>/", views.edit_purchase, name="edit_purchase"),
path('purchases/<int:pk>/', views.view_purchase, name='view_purchase'),
path('purchases/<int:pk>/payment/', views.record_payment, name='record_payment'),
path('purchases/save-pending/', views.save_purchase_as_pending, name='save_purchase_as_pending'),
path('purchases/<int:purchase_id>/items/', views.get_purchase_items, name='get_purchase_items'),
path('purchases/save-pending/', views.save_purchase_as_pending, name='save_purchase_as_pending'),
# Pending Purchases
path('pending-purchases/', views.pending_purchases, name='pending_purchases'),
path('pending-purchases/<int:pk>/cancel/', views.cancel_pending_purchase, name='cancel_pending_purchase'),

path('pending-purchases/', views.pending_purchases_list, name='pending_purchases_list'),
path('pending-purchases/<int:pk>/', views.view_pending_purchase, name='view_pending_purchase'),
path('pending-purchases/<int:pk>/edit/', views.edit_pending_purchase, name='edit_pending_purchase'),
path('pending-purchases/<int:pk>/complete/', views.complete_pending_purchase, name='complete_pending_purchase'),
path('pending-purchases/<int:pk>/delete/', views.delete_pending_purchase, name='delete_pending_purchase'),
# Returns
path('supplier-returns/', views.supplier_returns, name='supplier_returns'),
path('purchases/returns/create/', views.create_purchase_return, name='create_purchase_return'),
path('purchases/returns/<int:pk>/process/', views.process_return, name='process_return'),

# API Endpoints
path('api/suppliers/search/', views.search_suppliers, name='search_suppliers'),
path('api/products/search/', views.search_products, name='search_products'),
path('api/purchases/<int:purchase_id>/items/', views.get_purchase_items_api, name='get_purchase_items_api'),

# Export Endpoints
path('purchases/export/', views.export_purchases, name='export_purchases'),
path('pending-purchases/export/', views.export_pending_purchases, name='export_pending_purchases'),
path('supplier-returns/export/', views.export_supplier_returns, name='export_supplier_returns'),
    # Suppliers
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.add_supplier, name='add_supplier'),
    path('suppliers/edit/<int:pk>/', views.edit_supplier, name='edit_supplier'),
    path('suppliers/<int:pk>/', views.supplier_detail, name='supplier_detail'),
    path('supplier-returns/', views.supplier_returns, name='supplier_returns'),
    path('process-return/<int:return_id>/', views.process_return, name='process_return'),

    #  Expenses
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.add_expense, name='add_expense'),
    path('expenses/edit/<int:pk>/', views.edit_expense, name='edit_expense'),
    
    # Discounts
    path('discounts/', views.discount_list, name='discount_list'),
    path('discounts/add/', views.add_discount, name='add_discount'),
    path('discounts/toggle/<int:pk>/', views.toggle_discount_status, name='toggle_discount_status'),
    
    # Company & Pricing
    path('company/settings/', views.company_settings, name='company_settings'),
    path('company/pricing/', views.company_pricing, name='company_pricing'),
    path('company/pricing/add/', views.add_company_price, name='add_company_price'),
    path('company/pricing/edit/<int:pk>/', views.edit_company_price, name='edit_company_price'),

    # Reports
    path('reports/', views.reports_dashboard, name='reports_dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('reports/', views.reports, name='reports'),
    path('reports/profit-loss/', views.profit_loss_report, name='profit_loss_report'),
    path('reports/stock-value/', views.stock_value_report, name='stock_value_report'),
    path('daily_sales_report', views.daily_sales_report, name='daily_sales_report'),
    path('reports/daily-sales/export/', views.export_daily_sales, name='export_daily_sales'),

    # AJAX & Utilities
    path('search-products/', views.search_products, name='search_products'),
    path('search-customers/', views.search_customers, name='search_customers'),
    path('product/<int:pk>/details/', views.get_product_details, name='get_product_details'),
    path('customer/<int:pk>/details/', views.get_customer_details, name='get_customer_details'),
    path('product/<int:pk>/pricing/', views.get_product_pricing, name='get_product_pricing'),


    path('stock-journal/', views.stock_journal_list, name='stock_journal_list'),
    path('stock-journal/add/', views.add_stock_journal, name='add_stock_journal'),
    path('ajax/get-batches/', views.get_batches_for_product, name='get_batches_for_product'),
    


    # Authentication
    path('logout/', views.custom_logout, name='logout'),
    path('logout/', LogoutView.as_view(), name='logout'),
]