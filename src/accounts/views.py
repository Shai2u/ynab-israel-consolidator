import csv
import hashlib
import io
import os
import pandas as pd
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Account, FileReview
from .forms import AccountForm
from etl_pipeline.consolidate import SOURCE_REGISTRY

ALLOWED_EXTENSIONS = {'.xlsx', '.xls', '.csv'}

_SOURCE_BY_ACCOUNT_NAME = {source.name: source for source in SOURCE_REGISTRY}

YNAB_CSV_HEADER = ['Date', 'Payee', 'Category', 'Memo', 'Outflow', 'Inflow']


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


def _sha256_of_file(path, chunk_size=65536):
    digest = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _date_range_of(normalized_df):
    if normalized_df.empty:
        return None
    dates = pd.to_datetime(normalized_df['Date'], dayfirst=True, errors='coerce').dropna()
    if dates.empty:
        return None
    return f"{dates.min().strftime('%d/%m/%Y')} – {dates.max().strftime('%d/%m/%Y')}"


def account_detail(request, pk):
    account = get_object_or_404(Account, pk=pk)
    files = []
    folder_error = None
    if account.folder_path:
        if os.path.isdir(account.folder_path):
            names = sorted([
                f for f in os.listdir(account.folder_path)
                if os.path.splitext(f)[1].lower() in ALLOWED_EXTENSIONS
            ])
            hash_counts = {}
            for name in names:
                path = os.path.join(account.folder_path, name)
                file_hash = _sha256_of_file(path)
                files.append({
                    'name': name,
                    'size': os.path.getsize(path),
                    'hash': file_hash,
                })
                hash_counts[file_hash] = hash_counts.get(file_hash, 0) + 1
            for file_info in files:
                file_info['is_duplicate'] = hash_counts[file_info['hash']] > 1

            reviews_by_name = {r.filename: r for r in account.file_reviews.all()}
            for file_info in files:
                review = reviews_by_name.get(file_info['name'])
                if review is None:
                    file_info['reviewed_at'] = None
                    file_info['review_stale'] = False
                elif review.file_hash == file_info['hash']:
                    file_info['reviewed_at'] = review.reviewed_at
                    file_info['review_stale'] = False
                else:
                    file_info['reviewed_at'] = None
                    file_info['review_stale'] = True

            source = _SOURCE_BY_ACCOUNT_NAME.get(account.name)
            if source is not None:
                try:
                    loaded_tables = source.loader(folder=account.folder_path, recursive=False)
                except Exception:
                    loaded_tables = []
                tables_by_name = {table.path.name: table for table in loaded_tables}
                for file_info in files:
                    table = tables_by_name.get(file_info['name'])
                    if table is None:
                        file_info['date_range'] = None
                        continue
                    try:
                        normalized_df = source.normalizer(table.dataframe, dates_range=None)
                        file_info['date_range'] = _date_range_of(normalized_df)
                    except Exception as exc:
                        file_info['date_range'] = f"⚠ parse error: {exc}"
            else:
                for file_info in files:
                    file_info['date_range'] = None
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


def _safe_file_path(account, filename):
    """Resolve ``filename`` inside ``account.folder_path``, guarding against traversal."""
    safe_name = os.path.basename(filename)
    full_path = os.path.join(account.folder_path, safe_name)
    if os.path.dirname(os.path.abspath(full_path)) != os.path.abspath(account.folder_path):
        raise Http404("Invalid file path.")
    return safe_name, full_path


def account_toggle_review(request, pk, filename):
    account = get_object_or_404(Account, pk=pk)
    if not account.folder_path:
        raise Http404("Account has no folder configured.")
    if request.method != 'POST':
        raise Http404("Invalid request method.")

    safe_name, full_path = _safe_file_path(account, filename)
    if not os.path.isfile(full_path):
        raise Http404("File not found.")

    current_hash = _sha256_of_file(full_path)
    review = FileReview.objects.filter(account=account, filename=safe_name).first()
    if review is not None:
        review.delete()
    if review is None or review.file_hash != current_hash:
        # No prior review, or the file changed since it was last reviewed:
        # (re-)mark reviewed against the current content, with a fresh timestamp.
        FileReview.objects.create(account=account, filename=safe_name, file_hash=current_hash)
    return redirect('account_detail', pk=pk)


def account_convert(request, pk, filename):
    account = get_object_or_404(Account, pk=pk)
    if not account.folder_path:
        raise Http404("Account has no folder configured.")

    safe_name, full_path = _safe_file_path(account, filename)
    if not os.path.isfile(full_path):
        raise Http404("File not found.")

    source = _SOURCE_BY_ACCOUNT_NAME.get(account.name)
    if source is None:
        raise Http404(f"No source reader registered for account '{account.name}'.")

    if request.method == 'POST':
        dates = request.POST.getlist('date')
        payees = request.POST.getlist('payee')
        memos = request.POST.getlist('memo')
        outflows = request.POST.getlist('outflow')
        inflows = request.POST.getlist('inflow')
        categories = request.POST.getlist('category')

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(YNAB_CSV_HEADER)
        for date, payee, category, memo, outflow, inflow in zip(
            dates, payees, categories, memos, outflows, inflows
        ):
            writer.writerow([date, payee, category, memo, outflow, inflow])

        response = HttpResponse(
            buffer.getvalue().encode('utf-8-sig'),
            content_type='text/csv; charset=utf-8-sig',
        )
        response['Content-Disposition'] = (
            f'attachment; filename="{os.path.splitext(safe_name)[0]}_ynab.csv"'
        )
        return response

    loaded_tables = source.loader(folder=account.folder_path, recursive=False)
    table = next((t for t in loaded_tables if t.path.name == safe_name), None)
    if table is None:
        raise Http404("File could not be loaded by the source reader.")

    normalized_df = source.normalizer(table.dataframe, dates_range=None)
    rows = [
        {
            'date': row['Date'],
            'payee': row['Payee'],
            'memo': row['Memo'],
            'outflow': row['Outflow'],
            'inflow': row['Inflow'],
            'category': '',
        }
        for _, row in normalized_df.iterrows()
    ]

    return render(request, 'accounts/convert.html', {
        'account': account,
        'filename': safe_name,
        'rows': rows,
    })


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
