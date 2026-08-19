import os
from django.shortcuts import render, redirect, get_object_or_404
from .models import Account
from .forms import AccountForm

ALLOWED_EXTENSIONS = {'.xlsx', '.xls', '.csv'}


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


def account_detail(request, pk):
    account = get_object_or_404(Account, pk=pk)
    files = []
    folder_error = None
    if account.folder_path:
        if os.path.isdir(account.folder_path):
            files = sorted([
                f for f in os.listdir(account.folder_path)
                if os.path.splitext(f)[1].lower() in ALLOWED_EXTENSIONS
            ])
        else:
            folder_error = f"Folder not found: {account.folder_path}"
    return render(request, 'accounts/detail.html', {
        'account': account, 'files': files, 'folder_error': folder_error,
    })


def account_edit(request, pk):
    account = get_object_or_404(Account, pk=pk)
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            return redirect('account_detail', pk=pk)
    else:
        form = AccountForm(instance=account)
    return render(request, 'accounts/edit.html', {'form': form, 'account': account})


def account_upload(request, pk):
    account = get_object_or_404(Account, pk=pk)
    if request.method == 'POST' and account.folder_path:
        uploaded = request.FILES.get('file')
        if uploaded:
            filename = os.path.basename(uploaded.name)
            ext = os.path.splitext(filename)[1].lower()
            if ext in ALLOWED_EXTENSIONS:
                dest = os.path.join(account.folder_path, filename)
                with open(dest, 'wb+') as f:
                    for chunk in uploaded.chunks():
                        f.write(chunk)
    return redirect('account_detail', pk=pk)
