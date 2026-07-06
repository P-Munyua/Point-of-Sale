# your_app/management/commands/generate_batches_for_existing_products.py

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from pos.models import Product, Batch, Supplier, Category
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate batches for all existing products that don\'t have batches'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually creating batches'
        )
        parser.add_argument(
            '--product-id',
            type=int,
            help='Generate batch for specific product ID only'
        )
        parser.add_argument(
            '--batch-prefix',
            type=str,
            default='INITIAL',
            help='Prefix for batch numbers (default: INITIAL)'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        product_id = options['product_id']
        batch_prefix = options['batch_prefix']
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Starting batch generation for existing products'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get products
        if product_id:
            products = Product.objects.filter(id=product_id, is_active=True)
            if not products.exists():
                self.stdout.write(self.style.ERROR(f'Product with ID {product_id} not found'))
                return
        else:
            products = Product.objects.filter(is_active=True)
        
        # Get default supplier (create if doesn't exist)
        default_supplier, created = Supplier.objects.get_or_create(
            name='Initial Stock',
            defaults={
                'contact_person': 'System',
                'phone': '0000000000',
                'email': 'system@localhost',
                'address': 'Initial Stock Import',
                'balance': 0
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created default supplier: {default_supplier.name}'))
        
        stats = {
            'total_products': 0,
            'products_with_batches': 0,
            'products_without_batches': 0,
            'batches_created': 0,
            'errors': 0
        }
        
        for product in products:
            stats['total_products'] += 1
            
            # Check if product already has batches
            existing_batches = Batch.objects.filter(product=product)
            if existing_batches.exists():
                stats['products_with_batches'] += 1
                self.stdout.write(f"✓ Product '{product.name}' already has {existing_batches.count()} batch(es)")
                continue
            
            stats['products_without_batches'] += 1
            
            # Check if product has quantity
            if product.quantity <= 0:
                self.stdout.write(self.style.WARNING(f"⚠ Product '{product.name}' has zero quantity, skipping batch creation"))
                continue
            
            self.stdout.write(f"→ Processing product: {product.name}")
            self.stdout.write(f"  - Quantity: {product.quantity}")
            self.stdout.write(f"  - Purchase Price: KSh {product.purchase_price}")
            self.stdout.write(f"  - Selling Price: KSh {product.selling_price}")
            self.stdout.write(f"  - Wholesale Price: KSh {product.wholesale_price}")
            
            if dry_run:
                self.stdout.write(self.style.WARNING(f"  [DRY RUN] Would create batch for {product.name}"))
                stats['batches_created'] += 1
                continue
            
            try:
                with transaction.atomic():
                    # Generate batch number
                    batch_number = f"{batch_prefix}-{timezone.now().strftime('%Y%m%d')}-{product.id:06d}"
                    
                    # Ensure batch number is unique
                    counter = 1
                    original_batch_number = batch_number
                    while Batch.objects.filter(batch_number=batch_number).exists():
                        batch_number = f"{original_batch_number}-{counter}"
                        counter += 1
                    
                    # Create batch
                    batch = Batch.objects.create(
                        product=product,
                        batch_number=batch_number,
                        quantity=product.quantity,
                        expiry_date=None,  # No expiry date for initial stock
                        purchase_price=product.purchase_price,
                        selling_price=product.selling_price,
                        wholesale_price=product.wholesale_price,
                        purchase=None,
                        purchase_item=None,
                        date_received=timezone.now().date(),
                        is_active=True
                    )
                    
                    stats['batches_created'] += 1
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Created batch: {batch.batch_number} (ID: {batch.id})"))
                    
            except Exception as e:
                stats['errors'] += 1
                self.stdout.write(self.style.ERROR(f"  ✗ Error creating batch for {product.name}: {str(e)}"))
                logger.error(f"Error creating batch for product {product.name}: {e}")
        
        # Print summary
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('BATCH GENERATION SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f"Total products processed: {stats['total_products']}")
        self.stdout.write(f"Products with existing batches: {stats['products_with_batches']}")
        self.stdout.write(f"Products without batches: {stats['products_without_batches']}")
        self.stdout.write(f"Batches created: {stats['batches_created']}")
        self.stdout.write(f"Errors: {stats['errors']}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠ This was a DRY RUN. No changes were made.'))
            self.stdout.write(self.style.WARNING('Run without --dry-run to actually create batches.'))
        
        if stats['errors'] > 0:
            self.stdout.write(self.style.ERROR(f'\n⚠ {stats["errors"]} errors occurred. Check logs for details.'))

class CreateMissingBatchesCommand(BaseCommand):
    """Alternative command name for convenience"""
    help = 'Create batches for products that don\'t have any batches'

    def handle(self, *args, **options):
        command = Command()
        return command.handle(*args, **options)