from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from django.views.generic.edit import DeleteView
from .models import Transaction, Category, Budget
from .forms import TransactionForm, CategoryForm, BudgetForm, UserRegisterForm

from django.db.models import Sum, Q
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Transaction
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum

@login_required
def dashboard(request):

    today = timezone.now()
    current_month = today.strftime('%B %Y') 
    

    first_day = today.replace(day=1)
    last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    

    transactions = Transaction.objects.filter(
        user=request.user,
        date__range=[first_day, last_day]
    )
    

    total_income = transactions.filter(category__type='IN').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    total_expenses = transactions.filter(category__type='EX').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    balance = total_income - total_expenses
    

    recent_transactions = transactions.order_by('-date')[:5]
    

    expense_categories = Category.objects.filter(
        user=request.user,
        type='EX',
        transaction__in=transactions
    ).annotate(
        total=Sum('transaction__amount')
    ).order_by('-total')
    

    income_categories = Category.objects.filter(
        user=request.user,
        type='IN',
        transaction__in=transactions
    ).annotate(
        total=Sum('transaction__amount')
    ).order_by('-total')
    

    for category in expense_categories:
        category.percentage = (category.total / total_expenses * 100) if total_expenses > 0 else 0
    
    for category in income_categories:
        category.percentage = (category.total / total_income * 100) if total_income > 0 else 0
    
    context = {
        'balance': balance,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'current_month': current_month,
     'recent_transactions': recent_transactions,
     'expense_categories': expense_categories,
        'income_categories': income_categories,
    }
    return render(request, 'finances/dashboard.html', context)

@login_required
def transaction_list(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    
    # Filtering
    category_id = request.GET.get('category')
    transaction_type = request.GET.get('type')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if category_id:
        transactions = transactions.filter(category_id=category_id)
    
    if transaction_type:
        transactions = transactions.filter(category__type=transaction_type)
    
    if start_date:
        transactions = transactions.filter(date__gte=start_date)
    
    if end_date:
        transactions = transactions.filter(date__lte=end_date)
    
    # Pagination
    paginator = Paginator(transactions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.filter(user=request.user)
    
    context = {
        'transactions': page_obj,
        'categories': categories,
        'selected_category': category_id,
        'selected_type': transaction_type,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'finances/transaction_list.html', context)

@login_required
def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, 'Transacción creada exitosamente.')
            return redirect('transaction_list')
    else:
        form = TransactionForm(user=request.user)
    
    return render(request, 'finances/transaction_form.html', {'form': form})

@login_required
def transaction_edit(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transacción actualizada exitosamente.')
            return redirect('transaction_list')
    else:
        form = TransactionForm(instance=transaction, user=request.user)
    
    return render(request, 'finances/transaction_form.html', {'form': form})

@login_required
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transacción eliminada exitosamente.')
        return redirect('transaction_list')
    
    return render(request, 'finances/transaction_confirm_delete.html', {'transaction': transaction})

# Add user registration view
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'¡Cuenta creada para {username}! Ahora puedes iniciar sesión.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'finances/register.html', {'form': form})

@login_required
def category_list(request):
    categories = Category.objects.filter(user=request.user)
    context = {
        'categories': categories,
    }
    return render(request, 'finances/category_list.html', context)

@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, user=request.user)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, 'Categoría creada exitosamente.')
            return redirect('category_list')
    else:
        form = CategoryForm(user=request.user)
    
    return render(request, 'finances/category_form.html', {'form': form, 'title': 'Nueva Categoría'})

@login_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada exitosamente.')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category, user=request.user)
    
    return render(request, 'finances/category_form.html', {'form': form, 'title': 'Editar Categoría'})

class CategoryDelete(DeleteView):
    model = Category
    template_name = 'finances/category_confirm_delete.html'
    success_url = reverse_lazy('category_list')
    
    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Categoría eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)