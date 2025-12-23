from . import models
from . import hooks

# Expose post_init_hook at module level for Odoo
post_init_hook = hooks.post_init_hook

