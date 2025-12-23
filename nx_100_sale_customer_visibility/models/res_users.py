# models/res_users.py
import logging
from odoo import models

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    def _filter_access_rules(self, operation):
        """
        Treat team leaders (group_sale_salesman_all_leads) like admin
        on res.users: no record-rule filtering.
        """
        # Team leaders bypass record rules on res.users
        if self.env.user.has_group("sales_team.group_sale_salesman_all_leads"):
            _logger.debug(
                "### BYPASS res.users _filter_access_rules for TEAM LEADER uid=%s",
                self.env.uid,
            )
            return self

        return super()._filter_access_rules(operation)

    def check_access_rule(self, operation):
        """
        Bypass record rule check for team leaders on res.users.
        This prevents AccessError when team leaders access user records
        of salespeople in their teams.
        """
        if self.env.user.has_group("sales_team.group_sale_salesman_all_leads"):
            _logger.debug(
                "### BYPASS res.users check_access_rule for TEAM LEADER uid=%s op=%s",
                self.env.uid, operation,
            )
            return
        return super().check_access_rule(operation)
