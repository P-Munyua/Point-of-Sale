# utils.py or at the bottom of views.py
def get_credit_sale_summary(sale_id):
    """Get detailed credit sale summary"""
    sale = Sale.objects.get(id=sale_id)
    credit_items = CreditSaleItem.objects.filter(sale_item__sale=sale)
    
    summary = {
        'sale': sale,
        'total_credited': Decimal('0.00'),
        'total_paid': Decimal('0.00'),
        'total_balance': Decimal('0.00'),
        'products': [],
        'fully_paid_count': 0,
        'partially_paid_count': 0,
        'unpaid_count': 0,
    }
    
    for item in credit_items:
        product_summary = {
            'product': item.sale_item.product,
            'credited': item.quantity_credited,
            'paid': item.quantity_paid,
            'remaining': item.remaining_quantity,
            'amount_credited': item.total_amount,
            'amount_paid': item.amount_paid,
            'amount_balance': item.balance_amount,
            'is_fully_paid': item.is_fully_paid,
            'progress_percentage': (item.quantity_paid / item.quantity_credited * 100) if item.quantity_credited > 0 else 0,
        }
        
        summary['products'].append(product_summary)
        summary['total_credited'] += item.total_amount
        summary['total_paid'] += item.amount_paid
        summary['total_balance'] += item.balance_amount
        
        if item.is_fully_paid:
            summary['fully_paid_count'] += 1
        elif item.quantity_paid > 0:
            summary['partially_paid_count'] += 1
        else:
            summary['unpaid_count'] += 1
    
    return summary

def generate_credit_payment_report(start_date, end_date):
    """Generate credit payment report"""
    payments = CreditPayment.objects.filter(
        payment_date__range=[start_date, end_date]
    ).select_related('sale', 'sale__customer')
    
    report_data = []
    total_amount = Decimal('0.00')
    
    for payment in payments:
        payment_details = payment.details.all()
        for detail in payment_details:
            report_data.append({
                'payment_date': payment.payment_date,
                'sale_number': payment.sale.sale_number,
                'customer': payment.sale.customer.name if payment.sale.customer else 'Walk-in',
                'product': detail.credit_sale_item.sale_item.product.name,
                'quantity_paid': detail.quantity_paid,
                'amount_paid': detail.amount_paid,
                'payment_method': payment.get_payment_method_display(),
                'reference': payment.reference,
            })
            total_amount += detail.amount_paid
    
    return {
        'payments': report_data,
        'total_amount': total_amount,
        'payment_count': len(payments),
        'start_date': start_date,
        'end_date': end_date,
    }