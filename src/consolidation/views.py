from django.shortcuts import render
from .forms import ConsolidationForm
from etl_pipeline.consolidate import build_master_df

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