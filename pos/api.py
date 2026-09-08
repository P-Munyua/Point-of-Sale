from django.http import JsonResponse
from .models import Supplier, Product

def supplier_search(request):
    query = request.GET.get('search', '')
    suppliers = Supplier.objects.filter(name__icontains=query)[:10]
    data = [{'id': s.id, 'name': s.name} for s in suppliers]
    return JsonResponse(data, safe=False)

def product_search(request):
    query = request.GET.get('search', '')
    products = Product.objects.filter(
        Q(name__icontains=query) | Q(barcode__icontains=query),
        is_active=True
    )[:10]
    data = [{
        'id': p.id,
        'name': p.name,
        'barcode': p.barcode or '',
        'purchase_price': str(p.purchase_price)
    } for p in products]
    return JsonResponse(data, safe=False)