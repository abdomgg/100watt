# -*- coding: utf-8 -*-
import logging
from odoo import api, models

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = "crm.lead"

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        """
        Override search to filter opportunities for team leaders.
        Team leaders should only see their own opportunities and opportunities
        of salespeople in their team.
        """
        # Only apply filtering for team leaders (not admins)
        if self.env.user.has_group("sales_team.group_sale_salesman_all_leads") and \
           not self.env.user.has_group("base.group_system"):
            
            team_leader = self.env.user
            
            # Get all salespeople in teams led by this user
            team_user_ids = self.env['res.users'].sudo().search([
                ('sale_team_id.user_id', '=', team_leader.id)
            ]).ids
            
            # Add the team leader themselves
            team_user_ids.append(team_leader.id)
            
            # Add domain to filter by user_id
            team_domain = [
                ('user_id', 'in', team_user_ids),
                ('user_id', '!=', False)
            ]
            
            domain = domain + team_domain if domain else team_domain
            
            _logger.debug(
                "### CRM Lead _search filter for Team Leader uid=%s, team_user_ids=%s",
                self.env.uid, team_user_ids
            )
        
        # Apply filtering for regular salespeople
        elif self.env.user.has_group("sales_team.group_sale_salesman") and \
             not self.env.user.has_group("sales_team.group_sale_salesman_all_leads") and \
             not self.env.user.has_group("base.group_system"):
            
            salesperson_domain = [
                ('user_id', '=', self.env.user.id),
                ('user_id', '!=', False)
            ]
            
            domain = domain + salesperson_domain if domain else salesperson_domain
            
            _logger.debug(
                "### CRM Lead _search filter for Salesperson uid=%s",
                self.env.uid
            )
        
        return super()._search(domain, offset=offset, limit=limit, order=order)
