# -*- coding: utf-8 -*-

from odoo import fields, models


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    product_category_ids = fields.Many2many(
        'product.category',
        'crm_team_product_category_rel',
        'team_id',
        'category_id',
        string='فئات المنتجات',
        help='فئات المنتجات التي يمكن لهذا الفريق رؤيتها'
    )


