# management/commands/fix_stock.py

from django.core.management.base import BaseCommand
from django.db import transaction
from pos.models import Product, Batch, Purchase, PurchaseItem, Sale, SaleItem
from decimal import Decimal

class Command(BaseCommand):
    help = 'Fix stock inconsistencies and ensure batches are properly linked'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show what would be done without actually doing it')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.WARNING('Starting stock fix...'))
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Fix 1: Ensure all products with stock have at least one batch
        self.fix_products_without_batches(dry_run)
        
        # Fix 2: Ensure batch quantities match product total quantities
        self.fix_batch_quantities(dry_run)
        
        # Fix 3: Ensure sale items have purchase_price set
        self.fix_sale_items(dry_run)
        
        self.stdout.write(self.style.SUCCESS('Stock fix completed!'))
    
    def fix_products_without_batches(self, dry_run):
        """Create default batches for products that have stock but no batches"""
        products_without_batches = Product.objects.filter(
            quantity__gt=0,
            batches__isnull=True
        )
        
        count = products_without_batches.count()
        self.stdout.write(f"Found {count} products with stock but no batches")
        
        if count == 0:
            return
        
        for product in products_without_batches:
            self.stdout.write(f"  - {product.name}: has {product.quantity} units")
            
            if not dry_run:
                # Create a default batch
                Batch.objects.create(
                    product=product,
                    batch_number=f"DEFAULT-{product.id}",
                    quantity=product.quantity,
                    purchase_price=product.purchase_price,
                    selling_price=product.selling_price,
                    wholesale_price=product.wholesale_price,
                    date_received=product.created_at.date() if hasattr(product, 'created_at') else None,
                    is_active=True
                )
                self.stdout.write(self.style.SUCCESS(f"    Created batch for {product.name}"))
    
    def fix_batch_quantities(self, dry_run):
        """Ensure batch quantities sum to product total quantity"""
        products = Product.objects.filter(batches__isnull=False).distinct()
        
        for product in products:
            batch_total = product.batches.aggregate(total=models.Sum('quantity'))['total'] or Decimal('0')
            
            if batch_total != product.quantity:
                self.stdout.write(
                    f"  - {product.name}: Product has {product.quantity}, "
                    f"Batches sum to {batch_total} (difference: {product.quantity - batch_total})"
                )
                
                if not dry_run:
                    # Find the most recent batch and adjust it
                    latest_batch = product.batches.order_by('-date_received', '-id').first()
                    if latest_batch:
                        difference = product.quantity - batch_total
                        latest_batch.quantity += difference
                        latest_batch.save()
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"    Adjusted batch {latest_batch.batch_number} by {difference}"
                            )
                        )
    
    def fix_sale_items(self, dry_run):
        """Ensure sale items have purchase_price set from their batches"""
        sale_items = SaleItem.objects.filter(
            purchase_price=0,
            batch__isnull=False
        )
        
        count = sale_items.count()
        self.stdout.write(f"Found {count} sale items without purchase_price")
        
        for item in sale_items:
            if item.batch:
                self.stdout.write(
                    f"  - Sale #{item.sale.id}: {item.product.name} x {item.quantity} "
                    f"should have purchase_price {item.batch.purchase_price}"
                )
                
                if not dry_run:
                    item.purchase_price = item.batch.purchase_price
                    item.save()