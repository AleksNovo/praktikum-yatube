import datetime as dt


def year(request):
    """Добавляет переменную с текущим годом."""
    today = dt.datetime.today()
    today_year = today.year
    return {
        'year': today_year
    }
