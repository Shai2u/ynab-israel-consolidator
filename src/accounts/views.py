from django.shortcuts import render, redirect
from .models import Account
from .forms import AccountForm


def account_list(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('account_list')
    else:
        form = AccountForm()

    accounts = Account.objects.all()
    return render(request, 'accounts/list.html', {'form': form, 'accounts': accounts})
