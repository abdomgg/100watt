import logging
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleOrderApprover(models.Model):
    _name = 'sale.order.approver'
    _description = 'Sale Order Approver'
    _order = 'sequence, id'

    user_id = fields.Many2one('res.users', string='User', required=True, ondelete='cascade')
    approver_user_id = fields.Many2one('res.users', string='Approver', required=True)
    required = fields.Boolean(string='Required', default=True)
    sequence = fields.Integer(string='Sequence', default=10)


class SaleOrderApproverLine(models.Model):
    _name = 'sale.order.approver.line'
    _description = 'Sale Order Approver Line'
    _order = 'sequence, id'

    order_id = fields.Many2one('sale.order', string='Sale Order', required=True, ondelete='cascade')
    approver_user_id = fields.Many2one('res.users', string='Approver', required=True)
    required = fields.Boolean(string='Required', default=True)
    sequence = fields.Integer(string='Sequence', default=10)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='pending', readonly=True)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    approval_required = fields.Boolean(string='Approval Required', compute='_compute_approval_required', store=False)
    state = fields.Selection(
        selection=[
            ('draft', "Quotation"),
            ('sent', "Quotation Sent"),
            ('waiting_for_approval', 'Pending Approval'),
            ('sale', "Sales Order"),
            ('cancel', "Cancelled"),
        ],
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft'
    )
    approval_state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Approval Status', default='draft', readonly=True, copy=False, tracking=True)
    approver_ids = fields.One2many('sale.order.approver.line', 'order_id', string='Approvers')
    approved_by_ids = fields.Many2many(
        'res.users',
        'sale_order_approval_rel',
        'order_id',
        'user_id',
        string='Approved By',
        readonly=True
    )
    is_current_user_approver = fields.Boolean(string='Is Current User Approver', compute='_compute_is_current_user_approver')

    @api.depends('user_id', 'state', 'partner_id')
    def _compute_approval_required(self):
        for order in self:
            if order.state == 'draft' and order.user_id:
                order.approval_required = bool(order.user_id.sale_approver_ids)
            else:
                order.approval_required = False

    @api.depends('approver_ids', 'state', 'approved_by_ids')
    def _compute_is_current_user_approver(self):
        current_user = self.env.user
        for order in self:
            if order.state == 'waiting_for_approval' and order.approver_ids:
                is_approver = current_user in order.approver_ids.mapped('approver_user_id')
                has_approved = current_user in order.approved_by_ids
                order.is_current_user_approver = is_approver and not has_approved
            else:
                order.is_current_user_approver = False

    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        user_id = order.user_id or self.env.user
        has_approvers = bool(user_id.sale_approver_ids) if user_id else False
        
        if (has_approvers and 
            order.state == 'draft' and 
            order.partner_id and
            user_id and
            not order.approver_ids):
            try:
                order._auto_request_approval()
            except Exception as e:
                _logger.warning('Auto-approval request failed on create: %s', str(e))
        return order

    def write(self, vals):
        skip_approval = self.env.context.get('skip_approval_check', False)
        result = super(SaleOrder, self).write(vals)
        
        if skip_approval:
            return result
        
        for order in self:
            user_id = order.user_id or self.env.user
            has_approvers = bool(user_id.sale_approver_ids) if user_id else False
            
            if (has_approvers and 
                order.state == 'draft' and 
                order.partner_id and
                user_id and
                not order.approver_ids):
                try:
                    if not order.user_id:
                        order.with_context(skip_approval_check=True).write({'user_id': user_id.id})
                    order._auto_request_approval()
                except Exception as e:
                    _logger.error('Auto-approval request failed for order %s: %s', order.name, str(e), exc_info=True)
        
        return result

    def _auto_request_approval(self):
        self.ensure_one()
        
        if not self.user_id or not self.user_id.sale_approver_ids:
            return
        
        if self.approval_state == 'pending' or self.approver_ids:
            return
        
        approver_lines = self.env['sale.order.approver.line']
        for approver in self.user_id.sale_approver_ids:
            approver_lines |= self.env['sale.order.approver.line'].create({
                'order_id': self.id,
                'approver_user_id': approver.approver_user_id.id,
                'required': approver.required,
                'sequence': approver.sequence,
            })
        
        self.with_context(skip_approval_check=True).write({'approver_ids': [(6, 0, approver_lines.ids)]})
        
        order_details = self._get_approval_activity_note()
        for approver_line in self.approver_ids:
            try:
                self.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=approver_line.approver_user_id.id,
                    summary='Approve Sale Order %s' % self.name,
                    note=order_details,
                )
            except Exception as e:
                _logger.error('Failed to create activity for approver %s: %s', approver_line.approver_user_id.name, str(e))
        
        self.approval_state = 'pending'
        if self.state == 'draft':
            self.with_context(skip_approval_check=True).write({'state': 'waiting_for_approval'})

    def _get_approval_activity_note(self):
        return '<p>Please review and approve Sale Order <strong>%s</strong>.</p>' % self.name

    def action_confirm(self):
        for order in self:
            if order.approval_required:
                if order.state == 'waiting_for_approval':
                    required_approvers = order.approver_ids.filtered('required')
                    approved_required = required_approvers.filtered(
                        lambda a: a.approver_user_id in order.approved_by_ids
                    )
                    
                    if len(approved_required) < len(required_approvers):
                        raise UserError(
                            'This quotation requires approval before it can be confirmed.\n'
                            'Please wait for all required approvers to approve the order.'
                        )
                    if order.approval_state == 'approved':
                        order.state = 'draft'
                elif order.approval_state == 'draft' and not order.approver_ids:
                    raise UserError(
                        'This quotation requires approval before it can be confirmed.\n'
                        'Approval will be automatically requested once you select a customer.'
                    )
        
        result = super(SaleOrder, self).action_confirm()
        
        if self.approval_required:
            activities = self.env['mail.activity'].search([
                ('res_model', '=', 'sale.order'),
                ('res_id', '=', self.id),
                ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),
            ])
            for activity in activities:
                confirmation_status = '✓ ORDER CONFIRMED on %s' % (
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
                activity.note = (activity.note or '') + '\n\n' + confirmation_status
        
        return result

    def action_approve(self):
        self.ensure_one()
        
        if self.state != 'waiting_for_approval':
            raise UserError('This order is not pending approval.')
        
        if self.env.user not in self.approver_ids.mapped('approver_user_id'):
            raise UserError('You are not authorized to approve this order. Only designated approvers can approve.')
        
        if self.env.user in self.approved_by_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Already Approved',
                    'message': 'You have already approved this sale order.',
                    'type': 'info',
                    'sticky': False,
                }
            }
        
        self.approved_by_ids = [(4, self.env.user.id)]
        
        approver_line = self.approver_ids.filtered(
            lambda a: a.approver_user_id == self.env.user
        )
        if approver_line:
            approver_line.state = 'approved'
        
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', self.id),
            ('user_id', '=', self.env.user.id),
            ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),
        ])
        for activity in activities:
            approval_status = '✓ APPROVED by %s on %s' % (
                self.env.user.name,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            activity.note = (activity.note or '') + '\n\n' + approval_status
        
        required_approvers = self.approver_ids.filtered('required')
        approved_required = required_approvers.filtered(
            lambda a: a.approver_user_id in self.approved_by_ids
        )
        
        if len(approved_required) >= len(required_approvers):
            self.approval_state = 'approved'
            if self.state == 'waiting_for_approval':
                self.state = 'draft'
            self.message_post(
                body='Sale order has been approved by all required approvers.',
                subject='Order Approved'
            )
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'context': self.env.context,
        }

    def action_reject(self):
        self.ensure_one()
        
        if self.state != 'waiting_for_approval':
            raise UserError('This order is not pending approval.')
        
        if self.env.user not in self.approver_ids.mapped('approver_user_id'):
            raise UserError('You are not authorized to reject this order. Only designated approvers can reject.')
        
        self.approval_state = 'rejected'
        
        approver_line = self.approver_ids.filtered(
            lambda a: a.approver_user_id == self.env.user
        )
        if approver_line:
            approver_line.state = 'rejected'
        
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', self.id),
            ('user_id', '=', self.env.user.id),
            ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),
        ])
        for activity in activities:
            rejection_status = '✗ REJECTED by %s on %s' % (
                self.env.user.name,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            activity.note = (activity.note or '') + '\n\n' + rejection_status
        
        self.message_post(
            body='Sale order has been rejected by %s.' % self.env.user.name,
            subject='Order Rejected'
        )
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'context': self.env.context,
        }
