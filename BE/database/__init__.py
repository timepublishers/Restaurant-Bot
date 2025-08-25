from .main_db import init_main_db, get_main_db, MainDatabase, Restaurant, AdminOTP
from .tenant_db import get_tenant_db, TenantDatabase

__all__ = [
    'init_main_db',
    'get_main_db',
    'MainDatabase',
    'Restaurant',
    'AdminOTP',
    'get_tenant_db',
    'TenantDatabase'
]