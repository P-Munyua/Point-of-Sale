from django import forms
from .models import *
from django.core.exceptions import ValidationError
from django import forms
from .models import Product
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.forms import inlineformset_factory
from .models import StockJournal, StockJournalItem
from decimal import Decimal, InvalidOperation

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'least_selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'wholesale_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'wholesale_min_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        purchase_price = cleaned_data.get('purchase_price')
        selling_price = cleaned_data.get('selling_price')
        least_selling_price = cleaned_data.get('least_selling_price')
        wholesale_price = cleaned_data.get('wholesale_price')
        quantity = cleaned_data.get('quantity')
        reorder_level = cleaned_data.get('reorder_level')
        wholesale_min_quantity = cleaned_data.get('wholesale_min_quantity')
        
        # Validation rules
        errors = {}
        
        if purchase_price and selling_price:
            if selling_price < purchase_price:
                errors['selling_price'] = "Selling price cannot be less than purchase price."
            
            if least_selling_price:
                if least_selling_price > selling_price:
                    errors['least_selling_price'] = "Least selling price cannot be higher than retail price."
                if least_selling_price < purchase_price:
                    errors['least_selling_price'] = "Least selling price cannot be less than purchase price."
            
            if wholesale_price:
                if wholesale_price < purchase_price:
                    errors['wholesale_price'] = "Wholesale price cannot be less than purchase price."
                if wholesale_price > selling_price:
                    errors['wholesale_price'] = "Wholesale price cannot be higher than retail price."
        
        # Validate quantities can accept 6 decimal places
        if quantity is not None:
            try:
                # Convert to Decimal with 6 decimal places
                quantity = Decimal(str(quantity))
                cleaned_data['quantity'] = quantity
            except (ValueError, InvalidOperation):
                errors['quantity'] = "Invalid quantity value."
        
        if reorder_level is not None:
            try:
                reorder_level = Decimal(str(reorder_level))
                cleaned_data['reorder_level'] = reorder_level
            except (ValueError, InvalidOperation):
                errors['reorder_level'] = "Invalid reorder level value."
        
        if wholesale_min_quantity is not None:
            try:
                wholesale_min_quantity = Decimal(str(wholesale_min_quantity))
                cleaned_data['wholesale_min_quantity'] = wholesale_min_quantity
            except (ValueError, InvalidOperation):
                errors['wholesale_min_quantity'] = "Invalid wholesale minimum quantity value."
        
        if errors:
            raise ValidationError(errors)
        
        return cleaned_data


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

# forms.py - PurchaseForm
from django import forms
from .models import Purchase, Supplier, Product

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['supplier', 'invoice_number', 'payment_method', 'is_paid', 'notes']
        widgets = {
            'invoice_number': forms.TextInput(attrs={
                'readonly': 'readonly',
                'class': 'bg-gray-50'
            }),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supplier'].queryset = Supplier.objects.all().order_by('name')
        self.fields['is_paid'].required = False

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

# Add this to your existing forms.py
from django.forms import formset_factory, modelformset_factory

# In forms.py - Update the ExpenseItemForm and ExpenseFormSet

class ExpenseItemForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['date', 'category', 'description', 'amount']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date',
                'required': False  # Allow empty for row template
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
                'required': False  # Allow empty for row template
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2, 
                'placeholder': 'Description',
                'required': False
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control amount-input', 
                'placeholder': '0.00', 
                'step': '0.01',
                'required': False
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set today's date as default if not provided
        if not self.initial.get('date'):
            self.fields['date'].initial = timezone.now().date()
        
        # Ensure category choices match the model
        self.fields['category'].choices = [('', 'Select Category')] + list(Expense.CATEGORIES)

# Use a regular formset with extra=0 and handle validation manually
ExpenseFormSet = forms.formset_factory(
    ExpenseItemForm,
    extra=0,  # Start with no rows, we'll add them dynamically
    can_delete=True
)

# Create formset factory
ExpenseFormSet = modelformset_factory(
    Expense, 
    form=ExpenseItemForm,
    extra=3,  # Number of empty forms to show
    can_delete=True
)

class BulkExpenseForm(forms.Form):
    expense_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        initial=timezone.now().date
    )
    total_amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': True})
    )

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




# In forms.py - Update StockJournalForm
class StockJournalForm(forms.ModelForm):
    class Meta:
        model = StockJournal
        fields = ['reference', 'notes']  # Removed movement_type
        widgets = {
            'reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Reference (optional)'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes (optional)'}),
        }
        labels = {
            'reference': 'Reference',
            'notes': 'Notes',
        }

class StockJournalItemForm(forms.ModelForm):
    class Meta:
        model = StockJournalItem
        fields = ['product', 'batch', 'movement_type', 'quantity', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control product-select'}),
            'batch': forms.Select(attrs={'class': 'form-control batch-select'}),
            'movement_type': forms.Select(attrs={'class': 'form-control movement-type-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control quantity-input', 'step': '0.01', 'min': '0.01'}),
            'notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Notes (optional)'}),
        }
        labels = {
            'product': 'Product *',
            'batch': 'Batch',
            'movement_type': 'Movement Type *',
            'quantity': 'Quantity *',
            'notes': 'Notes',
        }

# Update the formset factory
StockJournalItemFormSet = inlineformset_factory(
    StockJournal,
    StockJournalItem,
    form=StockJournalItemForm,
    extra=1,
    can_delete=True,
    fields=['product', 'batch', 'movement_type', 'quantity', 'notes']
)


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


# Add these forms to your forms.py

from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import UserProfile, Role, PermissionGroup

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'is_active')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
        return user


class CustomUserEditForm(UserChangeForm):
    password = None  # Remove password field
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['role', 'phone', 'address', 'id_number', 'profile_picture', 
                 'is_active', 'can_override_role', 'custom_permissions']
        widgets = {
            'custom_permissions': forms.HiddenInput(),  # Will handle via JS
        }


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Group fields by category
        self.fields = forms.models.modelform_factory(Role, fields='__all__')().fields


class RoleFilterForm(forms.Form):
    """Form for filtering roles"""
    is_active = forms.ChoiceField(
        choices=[('', 'All'), ('true', 'Active'), ('false', 'Inactive')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search roles...'
        })
    )


class UserFilterForm(forms.Form):
    """Form for filtering users"""
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=False,
        empty_label="All Roles",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    is_active = forms.ChoiceField(
        choices=[('', 'All'), ('true', 'Active'), ('false', 'Inactive')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search users...'
        })
    )


class BulkUserImportForm(forms.Form):
    """Form for bulk user import"""
    file = forms.FileField(
        label='Excel File',
        help_text='Upload Excel file with columns: username, email, first_name, last_name, role, phone'
    )
    send_email = forms.BooleanField(
        required=False,
        initial=True,
        label='Send welcome email to users'
    )
    generate_passwords = forms.BooleanField(
        required=False,
        initial=True,
        label='Generate random passwords'
    )


class PasswordResetAdminForm(forms.Form):
    """Form for admin to reset user password"""
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label='Select User',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='New Password'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Confirm Password'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        
        return cleaned_data