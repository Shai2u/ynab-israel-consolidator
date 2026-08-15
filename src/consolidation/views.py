import io
import csv
from django.shortcuts import render
from .forms import ConsolidationForm
from etl_pipeline.consolidate import build_master_df
from etl_pipeline.matching import run_cascade_matching
from django.http import HttpResponse, JsonResponse

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


def consolidation_results(request):
    if request.method == 'POST':
        form = ConsolidationForm(request.POST)
        if form.is_valid():
            start = form.cleaned_data['start_date'].strftime('%d/%m/%Y')
            end = form.cleaned_data['end_date'].strftime('%d/%m/%Y')
            try:
                master_df = build_master_df(
                    dates_range=(start, end),
                    fail_on_error=False,
                )
                matched_df = run_cascade_matching(master_df)
                data = matched_df.to_dict(orient='records')
                return JsonResponse({'rows': data})
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
    return render(request, 'consolidation/results.html', {})