from django.contrib.admin.apps import AdminConfig


class CoremAdminConfig(AdminConfig):
    default_site = "config.admin_site.CoremAdminSite"
