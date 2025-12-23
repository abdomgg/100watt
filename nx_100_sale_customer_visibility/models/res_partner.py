# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _filter_access_rules(self, operation):
        """
        Bypass record rule filtering for salespeople on partners linked to their opportunities.
        This prevents AccessError when loading opportunity forms.
        """
        if operation == 'read' and self.env.user.has_group("sales_team.group_sale_salesman"):
            salesperson = self.env.user
            
            # Get partners from opportunities owned by this salesperson
            opportunity_partner_ids = self.env['crm.lead'].sudo().search([
                ('user_id', '=', salesperson.id)
            ]).mapped('partner_id').ids
            
            # Filter: only bypass for opportunity partners
            bypass_ids = [pid for pid in self.ids if pid in opportunity_partner_ids]
            check_ids = [pid for pid in self.ids if pid not in opportunity_partner_ids]
            
            if bypass_ids:
                _logger.debug(
                    "### BYPASS res.partner _filter_access_rules for Salesperson uid=%s partner_ids=%s",
                    self.env.uid, bypass_ids
                )
                # Return all records if all are bypassed
                if not check_ids:
                    return self
                # Return bypassed + filtered non-bypassed
                return self.browse(bypass_ids) | super(ResPartner, self.browse(check_ids))._filter_access_rules(operation)
        
        return super()._filter_access_rules(operation)

    def check_access_rule(self, operation):
        """
        Bypass record rule check for team leaders and salespeople on partner records
        that are linked to users in their team or linked to their opportunities.
        This allows sale order and CRM operations to access partner records.
        """
        if operation == 'read':
            # Team leaders: bypass for user partners in their team
            if self.env.user.has_group("sales_team.group_sale_salesman_all_leads"):
                team_leader = self.env.user
                team_user_partner_ids = self.env['res.users'].sudo().search([
                    ('sale_team_id.user_id', '=', team_leader.id)
                ]).mapped('partner_id').ids
                
                # Add the team leader's own partner
                team_user_partner_ids.append(team_leader.partner_id.id)
                
                # Filter: only bypass for user partners in the team
                bypass_ids = [pid for pid in self.ids if pid in team_user_partner_ids]
                check_ids = [pid for pid in self.ids if pid not in team_user_partner_ids]
                
                if bypass_ids:
                    _logger.debug(
                        "### BYPASS res.partner check_access_rule for Team Leader uid=%s partner_ids=%s",
                        self.env.uid, bypass_ids
                    )
                
                # Only check access for non-bypass partners
                if check_ids:
                    return super(ResPartner, self.browse(check_ids)).check_access_rule(operation)
                return
            
            # Salespeople: bypass for partners linked to their opportunities
            elif self.env.user.has_group("sales_team.group_sale_salesman"):
                salesperson = self.env.user
                
                # Get partners from opportunities owned by this salesperson
                opportunity_partner_ids = self.env['crm.lead'].sudo().search([
                    ('user_id', '=', salesperson.id)
                ]).mapped('partner_id').ids
                
                # Filter: only bypass for opportunity partners
                bypass_ids = [pid for pid in self.ids if pid in opportunity_partner_ids]
                check_ids = [pid for pid in self.ids if pid not in opportunity_partner_ids]
                
                if bypass_ids:
                    _logger.debug(
                        "### BYPASS res.partner check_access_rule for Salesperson uid=%s partner_ids=%s",
                        self.env.uid, bypass_ids
                    )
                
                # Only check access for non-bypass partners
                if check_ids:
                    return super(ResPartner, self.browse(check_ids)).check_access_rule(operation)
                return
        
        return super().check_access_rule(operation)

    team_leader_id = fields.Many2one(
        "res.users",
        string="Team Leader",
        compute="_compute_team_leader_id",
        store=True,
        readonly=True,
        compute_sudo=True,   # مهم لتفادي AccessError عند حسابه
    )

    @api.depends("user_id", "user_id.sale_team_id", "user_id.sale_team_id.user_id")
    def _compute_team_leader_id(self):
        for partner in self:
            leader = partner.user_id.sale_team_id.user_id if partner.user_id and partner.user_id.sale_team_id else False
            partner.team_leader_id = leader

    @api.onchange("user_id")
    def _onchange_user_id_set_team_leader(self):
        for partner in self:
            partner.team_leader_id = partner.user_id.sale_team_id.user_id if partner.user_id and partner.user_id.sale_team_id else False
