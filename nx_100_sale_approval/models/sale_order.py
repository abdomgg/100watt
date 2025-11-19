from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


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
        try:
            order = super(SaleOrder, self).create(vals)
        except Exception as e:
            # Check if it's an access rights error
            error_msg = str(e)
            if 'create' in error_msg.lower() and 'access' in error_msg.lower():
                # Check if user has sales group
                if not self.env.user.has_group('sales_team.group_sale_salesman'):
                    raise UserError(
                        'You do not have permission to create sale orders. '
                        'Please contact your administrator to grant you the Sales User access rights.'
                    ) from e
                else:
                    # User has group but still getting error - might be record rule issue
                    raise UserError(
                        'You do not have permission to create sale orders for this customer. '
                        'This might be due to record rules or company restrictions. '
                        'Please contact your administrator.'
                    ) from e
            # Re-raise other errors as-is
            raise
        
        user_id = order.user_id or self.env.user
        has_approvers = bool(user_id.sale_approver_ids) if user_id else False
        
        if (has_approvers and 
            order.state == 'draft' and 
            order.partner_id and
            user_id and
            not order.approver_ids):
            order._auto_request_approval()
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
                if not order.user_id:
                    order.with_context(skip_approval_check=True).write({'user_id': user_id.id})
                order._auto_request_approval()
        
        return result

    def _auto_request_approval(self):
        self.ensure_one()
        self._check_stock_guard()
        
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
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=approver_line.approver_user_id.id,
                summary='Approve Sale Order %s' % self.name,
                note=order_details,
            )
        
        self.approval_state = 'pending'
        if self.state == 'draft':
            self.with_context(skip_approval_check=True).write({'state': 'waiting_for_approval'})

    def _get_approval_activity_note(self):
        return '<p>Please review and approve Sale Order <strong>%s</strong>.</p>' % self.name

    def action_confirm(self):
        self._check_stock_guard()

        orders_to_confirm = self.env['sale.order']

        for order in self:
            needs_approval = bool(order.approver_ids) or order.approval_state in ('pending', 'approved') \
                or order.state == 'waiting_for_approval' or order.approval_required

            if not needs_approval:
                orders_to_confirm |= order
                continue

            if order.state in ('draft', 'sent'):
                order._auto_request_approval()
                continue

            if order.state == 'waiting_for_approval':
                if not order.approved_by_ids:
                    raise UserError(
                        'This quotation requires approval before it can be confirmed.\n'
                        'Please wait for an approver to approve the order.'
                    )
                order.with_context(skip_approval_check=True).write({'state': 'draft'})
                orders_to_confirm |= order
                continue

            orders_to_confirm |= order

        result = True
        if orders_to_confirm:
            result = super(SaleOrder, orders_to_confirm).action_confirm()
            orders_to_confirm._close_approval_activities_post_confirm()

        return result

    def _close_approval_activities_post_confirm(self):
        approvals_required = self.filtered('approval_required')
        if not approvals_required:
            return
        Activity = self.env['mail.activity']
        todo = self.env.ref('mail.mail_activity_data_todo')
        for order in approvals_required:
            activities = Activity.search([
                ('res_model', '=', 'sale.order'),
                ('res_id', '=', order.id),
                ('activity_type_id', '=', todo.id),
            ])
            for activity in activities:
                confirmation_status = '✓ ORDER CONFIRMED on %s' % (
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
                activity.note = (activity.note or '') + '\n\n' + confirmation_status

    def _check_stock_guard(self):
        for order in self:
            warehouse_name = order.warehouse_id.display_name or _('unspecified warehouse')
            lines = order.order_line.filtered(
                lambda l: l.product_id and l.product_id.type in ('product', 'consu') and not l.display_type and not l.is_downpayment
            )
            for line in lines:
                line._compute_qty_on_hand()
                qty_available = line.qty_on_hand
                if qty_available <= 0:
                    raise ValidationError(
                        _(
                            "Cannot confirm %(order)s because %(product)s is out of stock in %(warehouse)s.",
                            order=order.name or _('this quotation'),
                            product=line.product_id.display_name,
                            warehouse=warehouse_name,
                        )
                    )
                if line.product_uom_qty > qty_available:
                    raise ValidationError(
                        _(
                            "Cannot confirm %(order)s because %(product)s has only %(available)s %(uom)s "
                            "available in %(warehouse)s, but %(requested)s %(uom)s were requested.",
                            order=order.name or _('this quotation'),
                            product=line.product_id.display_name,
                            available=qty_available,
                            requested=line.product_uom_qty,
                            uom=line.product_uom.name,
                            warehouse=warehouse_name,
                        )
                    )

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
        
        # Approve immediately when any approver approves (not requiring all)
        self.approval_state = 'approved'
        
        # Automatically confirm the order when approved
        if self.state == 'waiting_for_approval':
            # Set state to sent first to allow confirmation
            self.with_context(skip_approval_check=True).write({
                'state': 'sent',
                'approval_state': 'approved'
            })
            # Automatically confirm the order (bypass approval check since already approved)
            try:
                self.with_context(skip_approval_check=True).action_confirm()
                self.message_post(
                    body='Sale order has been approved by %s and automatically confirmed.' % self.env.user.name,
                    subject='Order Approved and Confirmed'
                )
            except Exception:
                self.message_post(
                    body='Sale order has been approved by %s. Please confirm manually.' % self.env.user.name,
                    subject='Order Approved'
                )
        else:
            self.message_post(
                body='Sale order has been approved by %s.' % self.env.user.name,
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
        
        # Reset to draft state and clear approvers so user can edit and resend
        self.with_context(skip_approval_check=True).write({
            'state': 'draft',
            'approval_state': 'draft',
            'approver_ids': [(5, 0, 0)],  # Clear all approver lines
            'approved_by_ids': [(5, 0, 0)],  # Clear approved by list
        })
        
        self.message_post(
            body='Sale order has been rejected by %s. The order has been reset to draft for editing.' % self.env.user.name,
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
