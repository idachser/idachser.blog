from datetime import datetime


def global_context(request):
    return {"date_now": datetime.now()}
