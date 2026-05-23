import json

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from .services import metricas_dashboard


@staff_member_required
def admin_dashboard(request):
    data = metricas_dashboard()
    # Serializar a JSON los datos que consumen los charts en JS
    data["series_json"] = json.dumps(data["series"])
    data["distribucion_json"] = json.dumps(data["distribucion"])
    return render(request, "admin/platform/dashboard.html", data)


