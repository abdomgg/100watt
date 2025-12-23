# models/ir_rule.py
import logging
from odoo import api, models

_logger = logging.getLogger(__name__)


class IrRule(models.Model):
    _inherit = "ir.rule"

    @api.model
    def domain_get(self, model_name, mode='read'):
        """
        Bypass record rules for team leaders on specific models.
        """
        if self.env.user.has_group("sales_team.group_sale_salesman_all_leads") and \
           not self.env.user.has_group("base.group_system"):
            # Team leaders bypass res.users record rules for read operations
            if model_name == "res.users" and mode == "read":
                _logger.debug(
                    "### BYPASS ir.rule domain_get FOR res.users READ - Team Leader uid=%s",
                    self.env.uid
                )
                return [], [], ['"res_users"."id"']

        return super().domain_get(model_name, mode)

    @api.model
    def _compute_domain(self, model_name, mode="read"):
        """
        Bypass record rules on res.users for team leaders.
        """
        if self.env.user.has_group("sales_team.group_sale_salesman_all_leads") and \
           not self.env.user.has_group("base.group_system"):
            # Team leaders bypass res.users record rules for read operations
            if model_name == "res.users" and mode == "read":
                _logger.debug(
                    "### BYPASS ir.rule _compute_domain FOR res.users READ - Team Leader uid=%s",
                    self.env.uid
                )
                # Return empty domain = no restrictions
                return []

        return super()._compute_domain(model_name, mode)
