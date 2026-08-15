import io
import csv
from django.shortcuts import render
from .forms import ConsolidationForm
from etl_pipeline.consolidate import build_master_df
from django.http import HttpResponse

def consolidation_run(request):
    result = None
    error = None

    if request.method == 'POST':
        form = ConsolidationForm(request.POST)
        if form.is_valid():
            start = form.cleaned_data['start_date'].strftime('%d/%m/%Y')
            end = form.cleaned_data['end_date'].strftime('%d/%m/%Y')
            try:
                status_rows = []
                master_df = build_master_df(
                    dates_range=(start, end),
                    status_rows=status_rows,
                    fail_on_error=False,
                )
                result = {
                    'total_rows': len(master_df),
                    'status_rows': status_rows,
                }
            except Exception as e:
                error = str(e)
    else:
        form = ConsolidationForm()

    return render(request, 'consolidation/run.html', {
        'form': form,
        'result': result,
        'error': error,
    })

def consolidation_export(request):
    if request.method == 'POST':
        form = ConsolidationForm(request.POST)
        if form.is_valid():
            start_str = form.cleaned_data['start_date'].strftime('%d_%m_%Y')
            end_str = form.cleaned_data['end_date'].strftime('%d_%m_%Y')

            start = form.cleaned_data['start_date'].strftime('%d/%m/%Y')
            end = form.cleaned_data['end_date'].strftime('%d/%m/%Y')
            master_df = build_master_df(
                dates_range=(start, end),
                fail_on_error=False,
            )
            response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
            response['Content-Disposition'] = f'attachment; filename="master_{start_str}-{end_str}.csv"'
            master_df.to_csv(path_or_buf=response, index=False, encoding='utf-8-sig')
            return response
    return HttpResponse(status=400)