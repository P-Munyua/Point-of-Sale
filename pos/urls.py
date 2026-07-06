from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
# At the top of your urls.py, add batch_profit_report to the imports
from pos.views import (
    # ... your existing imports ...
    batch_profit_report,  # Add this line
)

urlpatterns = [

    path('login/', views.custom_login, name='custom_login'),
    path('logout/', views.custom_logout, name='custom_logout'),
    path('password-change/', views.password_change, name='password_change'),
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    
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
    path('sale/<int:sale_id>/print-direct/', views.print_receipt_direct, name='print_receipt_direct'),
    path('sale/delete/<int:pk>/', views.delete_sale, name='delete_sale'),
    path('load-pending-sale/<int:pk>/', views.load_pending_sale, name='load_pending_sale'),
    path('get-sale-id/<str:sale_number>/', views.get_sale_id, name='get_sale_id'),
    path('get-edit-sale-data/<int:pk>/', views.get_edit_sale_data, name='get_edit_sale_data'),
    path('get-product-batches/<int:product_id>/', views.get_product_batches_with_prices, name='get_product_batches'),
    path('check-batch-availability/<int:batch_id>/<str:quantity>/', views.check_batch_availability, name='check_batch_availability'),


    # Credit Payments
    path('credit-payments/', views.credit_payments, name='credit_payments'),
    path('credit-payments/<int:pk>/process/', views.process_credit_payment, name='process_credit_payment'),
    path('sale/<int:pk>/load-to-pos/', views.load_sale_to_pos, name='load_sale_to_pos'),
    path('clear-edit-session/', views.clear_edit_session, name='clear_edit_session'),



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
    path('batches/<int:pk>/', views.batch_detail, name='batch_detail'),
    path('batches/<int:pk>/delete/', views.delete_batch, name='delete_batch'),
    
    
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
path('purchases/delete/<int:pk>/', views.delete_purchase, name='delete_purchase'),

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
    path('expenses/delete/<int:pk>/', views.delete_expense, name='delete_expense'),
    
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
    path('stock-journal/<int:pk>/', views.stock_journal_detail, name='stock_journal_detail'),



    path('stock-journal/', views.stock_journal_list, name='stock_journal_list'),
    path('stock-journal/add/', views.add_stock_journal, name='add_stock_journal'),
    path('ajax/get-batches/', views.get_batches_for_product, name='get_batches_for_product'),
    path('get-product-batches/<int:product_id>/', views.get_product_batches, name='get_product_batches'),
    path('reports/', views.reports_dashboard, name='reports_dashboard'),
    path('reports/sales-by-product/', views.sales_by_product_report, name='sales_by_product_report'),
    path('reports/purchase-by-product/', views.purchase_by_product_report, name='purchase_by_product_report'),
    path('reports/customer-payments/', views.customer_payment_report, name='customer_payment_report'),
    path('reports/supplier-payments/', views.supplier_payment_report, name='supplier_payment_report'),
    path('reports/profit-by-product/', views.profit_by_product_report, name='profit_by_product_report'),
    path('reports/daily-opening-stock/', views.daily_opening_stock_report, name='daily_opening_stock_report'), 
    path('reports/top-selling-products/', views.top_selling_products_report, name='top_selling_products_report'),
    path('reports/slow-moving-products/', views.slow_moving_products_report, name='slow_moving_products_report'),
    path('reports/customer-sales-analysis/', views.customer_sales_analysis, name='customer_sales_analysis'),
    path('reports/supplier-purchase-analysis/', views.supplier_purchase_analysis, name='supplier_purchase_analysis'),
    path('reports/product-performance/', views.product_performance_report, name='product_performance_report'),
    path('reports/weekly-sales-profit/', views.weekly_sales_profit_report, name='weekly_sales_profit_report'),

    
    # Export URLs
    path('reports/export/<str:report_type>/', views.export_report, name='export_report'),
    path('ajax/search-products/', views.search_products, name='search_products'),
    path('reports/daily-opening-stock/export/', views.export_opening_stock, name='export_opening_stock'),
    path('supplier-payments/', views.supplier_payment_summary, name='supplier_payment_summary'),
    path('supplier-payments/<int:supplier_id>/', views.supplier_payment_summary, name='supplier_payment_summary'),
    path('admin/users/dashboard/', views.user_management_dashboard, name='user_management_dashboard'),
    path('admin/users/', views.user_list, name='user_list'),
    path('admin/users/create/', views.create_user, name='create_user'),
    path('admin/users/<int:pk>/', views.user_detail, name='user_detail'),
    path('admin/users/<int:pk>/edit/', views.edit_user, name='edit_user'),
    path('admin/users/<int:pk>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    path('admin/users/<int:pk>/reset-password/', views.reset_user_password, name='reset_user_password'),
    path('admin/users/bulk-import/', views.bulk_import_users, name='bulk_import_users'),
    
    # Role Management URLs
    path('admin/roles/', views.role_list, name='role_list'),
    path('admin/roles/create/', views.create_role, name='create_role'),
    path('admin/roles/<int:pk>/', views.role_detail, name='role_detail'),
    path('admin/roles/<int:pk>/edit/', views.edit_role, name='edit_role'),
    path('admin/roles/<int:pk>/toggle-status/', views.toggle_role_status, name='toggle_role_status'),
    path('admin/roles/<int:pk>/duplicate/', views.duplicate_role, name='duplicate_role'),
    
    # Activity Logs
    path('admin/activity-logs/', views.activity_logs, name='activity_logs'),
    
    # Permissions
    path('admin/permissions/summary/', views.user_permissions_summary, name='user_permissions_summary'),
    path('admin/users/<int:pk>/permissions/', views.get_user_permissions, name='get_user_permissions'),
    path('credit/payments/', views.credit_payments, name='credit_payments'),
    path('credit/payment/<int:pk>/product-level/', views.product_level_credit_payment, name='product_level_credit_payment'),
    path('credit/payment/history/<int:pk>/', views.credit_payment_history, name='credit_payment_history'),
    path('credit/payment/detail/<int:payment_id>/', views.credit_payment_detail, name='credit_payment_detail'),
    path('credit/payment/process/<int:pk>/', views.process_credit_payment, name='process_credit_payment'),
    path('stock-management/', views.stock_management, name='stock_management'),
    path('batch-profit/', views.batch_profit_report, name='batch_profit_report'),
    path('reports/expiry-tracking/', views.expiry_tracking, name='expiry_tracking'),
    
    # Expected Profits
    path('reports/expected-profits/', views.expected_profits_report, name='expected_profits_report'),
    path('purchases/<int:pk>/invoice/', views.purchase_invoice, name='purchase_invoice'),
    path('purchases/<int:pk>/print/', views.print_purchase_invoice, name='print_purchase_invoice'),
    path('pos/initialize-paystack-payment/', views.initialize_paystack_payment, name='initialize_paystack_payment'),
    path('pos/initialize-mpesa-payment/', views.initialize_mpesa_payment, name='initialize_mpesa_payment'),
    path('pos/generate-qr-payment/<int:sale_id>/', views.generate_qr_payment, name='generate_qr_payment'),
    path('pos/paystack-webhook/', views.paystack_webhook, name='paystack_webhook'),
    path('pos/verify-payment/', views.verify_payment, name='verify_payment'),
    path('pos/payment-callback/', views.payment_callback, name='payment_callback'),
    path('sale/<int:sale_id>/thermal-print/', views.thermal_print_receipt, name='thermal_print_receipt'),
    # In your urls.py, make sure you have:

]
