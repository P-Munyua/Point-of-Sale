# pos/management/commands/initialize_roles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pos.models import Role, UserProfile

class Command(BaseCommand):
    help = 'Initialize default roles and permissions'

    def handle(self, *args, **options):
        # Define roles with permissions
        roles_config = {
            'admin': {
                'description': 'Full system access',
                'permissions': {
                    # Dashboard & POS
                    'can_access_dashboard': True,
                    'can_access_pos': True,
                    'can_process_sales': True,
                    'can_edit_sales': True,
                    'can_delete_sales': True,
                    'can_view_all_sales': True,
                    'can_view_own_sales': True,
                    # Products
                    'can_view_products': True,
                    'can_add_products': True,
                    'can_edit_products': True,
                    'can_delete_products': True,
                    'can_import_products': True,
                    # Inventory
                    'can_view_inventory': True,
                    'can_manage_stock': True,
                    'can_view_reports': True,
                    # Purchases
                    'can_view_purchases': True,
                    'can_add_purchases': True,
                    'can_edit_purchases': True,
                    'can_delete_purchases': True,
                    # Customers
                    'can_view_customers': True,
                    'can_add_customers': True,
                    'can_edit_customers': True,
                    'can_delete_customers': True,
                    # Suppliers
                    'can_view_suppliers': True,
                    'can_add_suppliers': True,
                    'can_edit_suppliers': True,
                    'can_delete_suppliers': True,
                    # Reports
                    'can_view_sales_reports': True,
                    'can_view_inventory_reports': True,
                    'can_view_profit_reports': True,
                    'can_view_customer_reports': True,
                    'can_export_reports': True,
                    # Settings
                    'can_manage_settings': True,
                    'can_manage_users': True,
                    'can_manage_roles': True,
                    # Financial
                    'can_view_financials': True,
                    'can_process_refunds': True,
                    'can_view_credit_sales': True,
                    'can_process_credit_payments': True,
                }
            },
            'manager': {
                'description': 'Store manager with most permissions',
                'permissions': {
                    'can_access_dashboard': True,
                    'can_access_pos': True,
                    'can_process_sales': True,
                    'can_edit_sales': True,
                    'can_delete_sales': False,
                    'can_view_all_sales': True,
                    'can_view_own_sales': True,
                    'can_view_products': True,
                    'can_add_products': True,
                    'can_edit_products': True,
                    'can_delete_products': False,
                    'can_import_products': True,
                    'can_view_inventory': True,
                    'can_manage_stock': True,
                    'can_view_reports': True,
                    'can_view_purchases': True,
                    'can_add_purchases': True,
                    'can_edit_purchases': True,
                    'can_delete_purchases': False,
                    'can_view_customers': True,
                    'can_add_customers': True,
                    'can_edit_customers': True,
                    'can_delete_customers': False,
                    'can_view_suppliers': True,
                    'can_add_suppliers': True,
                    'can_edit_suppliers': True,
                    'can_delete_suppliers': False,
                    'can_view_sales_reports': True,
                    'can_view_inventory_reports': True,
                    'can_view_profit_reports': True,
                    'can_view_customer_reports': True,
                    'can_export_reports': True,
                    'can_manage_settings': False,
                    'can_manage_users': False,
                    'can_manage_roles': False,
                    'can_view_financials': True,
                    'can_process_refunds': True,
                    'can_view_credit_sales': True,
                    'can_process_credit_payments': True,
                }
            },
            'cashier': {
                'description': 'Cashier - POS operations only',
                'permissions': {
                    'can_access_dashboard': True,
                    'can_access_pos': True,
                    'can_process_sales': True,
                    'can_edit_sales': False,
                    'can_delete_sales': False,
                    'can_view_all_sales': False,
                    'can_view_own_sales': True,
                    'can_view_products': True,
                    'can_add_products': False,
                    'can_edit_products': False,
                    'can_delete_products': False,
                    'can_import_products': False,
                    'can_view_inventory': True,
                    'can_manage_stock': False,
                    'can_view_reports': False,
                    'can_view_purchases': False,
                    'can_add_purchases': False,
                    'can_edit_purchases': False,
                    'can_delete_purchases': False,
                    'can_view_customers': True,
                    'can_add_customers': True,
                    'can_edit_customers': False,
                    'can_delete_customers': False,
                    'can_view_suppliers': False,
                    'can_add_suppliers': False,
                    'can_edit_suppliers': False,
                    'can_delete_suppliers': False,
                    'can_view_sales_reports': False,
                    'can_view_inventory_reports': False,
                    'can_view_profit_reports': False,
                    'can_view_customer_reports': False,
                    'can_export_reports': False,
                    'can_manage_settings': False,
                    'can_manage_users': False,
                    'can_manage_roles': False,
                    'can_view_financials': False,
                    'can_process_refunds': False,
                    'can_view_credit_sales': False,
                    'can_process_credit_payments': False,
                }
            },
            'inventory': {
                'description': 'Inventory manager',
                'permissions': {
                    'can_access_dashboard': True,
                    'can_access_pos': False,
                    'can_process_sales': False,
                    'can_edit_sales': False,
                    'can_delete_sales': False,
                    'can_view_all_sales': False,
                    'can_view_own_sales': False,
                    'can_view_products': True,
                    'can_add_products': True,
                    'can_edit_products': True,
                    'can_delete_products': False,
                    'can_import_products': True,
                    'can_view_inventory': True,
                    'can_manage_stock': True,
                    'can_view_reports': True,
                    'can_view_purchases': True,
                    'can_add_purchases': True,
                    'can_edit_purchases': True,
                    'can_delete_purchases': False,
                    'can_view_customers': False,
                    'can_add_customers': False,
                    'can_edit_customers': False,
                    'can_delete_customers': False,
                    'can_view_suppliers': True,
                    'can_add_suppliers': True,
                    'can_edit_suppliers': True,
                    'can_delete_suppliers': False,
                    'can_view_sales_reports': False,
                    'can_view_inventory_reports': True,
                    'can_view_profit_reports': False,
                    'can_view_customer_reports': False,
                    'can_export_reports': True,
                    'can_manage_settings': False,
                    'can_manage_users': False,
                    'can_manage_roles': False,
                    'can_view_financials': False,
                    'can_process_refunds': False,
                    'can_view_credit_sales': False,
                    'can_process_credit_payments': False,
                }
            },
            'accountant': {
                'description': 'Accountant - financial reports only',
                'permissions': {
                    'can_access_dashboard': True,
                    'can_access_pos': False,
                    'can_process_sales': False,
                    'can_edit_sales': False,
                    'can_delete_sales': False,
                    'can_view_all_sales': True,
                    'can_view_own_sales': False,
                    'can_view_products': False,
                    'can_add_products': False,
                    'can_edit_products': False,
                    'can_delete_products': False,
                    'can_import_products': False,
                    'can_view_inventory': True,
                    'can_manage_stock': False,
                    'can_view_reports': True,
                    'can_view_purchases': True,
                    'can_add_purchases': False,
                    'can_edit_purchases': False,
                    'can_delete_purchases': False,
                    'can_view_customers': True,
                    'can_add_customers': False,
                    'can_edit_customers': False,
                    'can_delete_customers': False,
                    'can_view_suppliers': True,
                    'can_add_suppliers': False,
                    'can_edit_suppliers': False,
                    'can_delete_suppliers': False,
                    'can_view_sales_reports': True,
                    'can_view_inventory_reports': True,
                    'can_view_profit_reports': True,
                    'can_view_customer_reports': True,
                    'can_export_reports': True,
                    'can_manage_settings': False,
                    'can_manage_users': False,
                    'can_manage_roles': False,
                    'can_view_financials': True,
                    'can_process_refunds': False,
                    'can_view_credit_sales': True,
                    'can_process_credit_payments': False,
                }
            }
        }

        # Create roles
        for role_name, config in roles_config.items():
            role, created = Role.objects.get_or_create(
                name=role_name,
                defaults={
                    'description': config['description'],
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(f'Created role: {role_name}')
            else:
                self.stdout.write(f'Updated role: {role_name}')
            
            # Update permissions
            for perm_name, value in config['permissions'].items():
                setattr(role, perm_name, value)
            role.save()
        
        # Create admin user if doesn't exist
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@company.com',
                'first_name': 'System',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if created:
            admin_user.set_password('Admin@123')
            admin_user.save()
            self.stdout.write('Created admin user: admin (password: Admin@123)')
        
        # Assign admin role to admin user
        admin_role = Role.objects.get(name='admin')
        profile, created = UserProfile.objects.get_or_create(
            user=admin_user,
            defaults={
                'role': admin_role,
                'is_active': True
            }
        )
        if not created:
            profile.role = admin_role
            profile.save()
        
        self.stdout.write(self.style.SUCCESS('Roles initialized successfully!'))