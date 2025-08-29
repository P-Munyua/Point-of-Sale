from django import forms
from .models import *
from django.core.exceptions import ValidationError

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'wholesale_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'wholesale_min_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


from django import forms
from django.core.validators import FileExtensionValidator

class ProductImportForm(forms.Form):
    file = forms.FileField(
        label='Excel File',
        validators=[FileExtensionValidator(allowed_extensions=['xlsx', 'xls'])]
    )
    update_existing = forms.BooleanField(
        required=False,
        initial=False,
        label='Update existing products'
    ) 

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone', 'email', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            raise forms.ValidationError("Phone number is required")
        return phone

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['customer', 'sale_type', 'payment_method', 'amount_paid', 'mpesa_code', 'cheque_number', 'is_credit']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'sale_type': forms.Select(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control'}),
            'mpesa_code': forms.TextInput(attrs={'class': 'form-control'}),
            'cheque_number': forms.TextInput(attrs={'class': 'form-control'}),
            'is_credit': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

from django import forms
from .models import Purchase, Supplier

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['supplier', 'invoice_number']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supplier'].required = True
        self.fields['invoice_number'].required = False
        self.fields['supplier'].queryset = Supplier.objects.all().order_by('name')

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['date', 'category', 'description', 'amount']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['product', 'batch_number', 'quantity', 'expiry_date', 'purchase_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class DiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'discount_type': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'products': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'categories': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class SupplierPaymentForm(forms.ModelForm):
    class Meta:
        model = SupplierPayment
        fields = ['supplier', 'purchase', 'amount', 'date', 'payment_method', 'reference']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'purchase': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CompanyPriceForm(forms.ModelForm):
    class Meta:
        model = CompanyPrice
        fields = ['company', 'product', 'price']
        widgets = {
            'company': forms.Select(attrs={'class': 'form-control'}),
            'product': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class PendingSaleForm(forms.ModelForm):
    class Meta:
        model = PendingSale
        fields = ['customer']  # Standard Django convention is lowercase
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'})
        }

class BulkUploadForm(forms.Form):
    model_choices = (
        ('product', 'Products'),
        ('customer', 'Customers'),
        ('supplier', 'Suppliers'),
    )
    
    model_type = forms.ChoiceField(choices=model_choices, widget=forms.Select(attrs={'class': 'form-control'}))
    file = forms.FileField(label='Excel File', widget=forms.FileInput(attrs={'class': 'form-control'}))



class ImportForm(forms.Form):
    model_choices = (
        ('product', 'Products'),
        ('customer', 'Customers'),
        ('supplier', 'Suppliers'),
    )
    
    model_type = forms.ChoiceField(choices=model_choices, widget=forms.Select(attrs={'class': 'form-control'}))
    csv_file = forms.FileField(label='CSV File', widget=forms.FileInput(attrs={'class': 'form-control'}))
    overwrite = forms.BooleanField(required=False, initial=False, 
                                 widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))




from django import forms
from .models import Product, Customer, Supplier

class BulkUploadForm(forms.Form):
    file = forms.FileField(label='Excel File')
    model_type = forms.ChoiceField(
        choices=[
            ('product', 'Products'),
            ('customer', 'Customers'),
            ('supplier', 'Suppliers')
        ],
        widget=forms.RadioSelect
    )


class PurchaseReturnForm(forms.ModelForm):
    original_purchase = forms.ModelChoiceField(
        queryset=Purchase.objects.filter(is_return=False),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}))
    
    class Meta:
        model = Purchase
        fields = ['original_purchase', 'invoice_number', 'return_reason']
        widgets = {
            'invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'RET-001'
            }),
            'return_reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Reason for return...'
            }),
        }


class SupplierReturnForm(forms.ModelForm):
    class Meta:
        model = SupplierReturn
        fields = ['supplier', 'product', 'batch', 'quantity', 'reason', 'refund_amount', 'notes']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'product': forms.Select(attrs={'class': 'form-control'}),
            'batch': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'refund_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class PurchaseReturnForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['supplier', 'invoice_number', 'return_reason']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. RET-001'
            }),
            'return_reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Reason for return...'
            }),
        }




class StockJournalForm(forms.ModelForm):
    class Meta:
        model = StockJournal
        fields = ['product', 'batch', 'movement_type', 'quantity', 'reference', 'notes']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['batch'].queryset = Batch.objects.none()
        
        if 'product' in self.data:
            try:
                product_id = int(self.data.get('product'))
                self.fields['batch'].queryset = Batch.objects.filter(product_id=product_id).order_by('-expiry_date')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['batch'].queryset = self.instance.product.batches.order_by('-expiry_date')


from django import forms
from .models import Company

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'address', 'phone', 'email', 'vat_number', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'vat_number': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }