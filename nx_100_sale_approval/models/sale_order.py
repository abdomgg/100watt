import logging
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

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
    approver_ids = fields.One2many('sale.order.approver.line', 'order_id', string='Approvers', copy=False)
    approved_by_ids = fields.Many2many(
        'res.users',
        'sale_order_approval_rel',
        'order_id',
        'user_id',
        string='Approved By',
        readonly=True,
        copy=False
    )
    is_current_user_approver = fields.Boolean(string='Is Current User Approver', compute='_compute_is_current_user_approver')

    @api.depends('user_id', 'state', 'partner_id', 'approver_ids', 'approval_state')
    def _compute_approval_required(self):
        current_user = self.env.user
        for order in self:
            # Don't show approval required if already has approvers or is in approval workflow
            if order.approver_ids or order.approval_state != 'draft':
                order.approval_required = False
            elif order.state == 'draft' and order.user_id:
                # Only show approval required if current user is the salesperson with approvers
                order.approval_required = (
                    current_user == order.user_id and 
                    bool(order.user_id.sudo().sale_approver_ids)
                )
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
        
        current_user = self.env.user
        user_id = order.user_id or current_user
        
        # Only auto-request approval if current user is the salesperson
        # Team leaders creating orders for their salespeople should not trigger approval
        if current_user != user_id:
            return order
            
        has_approvers = bool(user_id.sudo().sale_approver_ids) if user_id else False
        
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
        
        current_user = self.env.user
        for order in self:
            user_id = order.user_id or current_user
            
            # Only auto-request approval if current user is the salesperson
            # Team leaders creating/editing orders for their salespeople should not trigger approval
            if current_user != user_id:
                continue
                
            has_approvers = bool(user_id.sudo().sale_approver_ids) if user_id else False
            
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
        
        # Use sudo to bypass record rules when reading approver configuration
        if not self.user_id or not self.user_id.sudo().sale_approver_ids:
            return
        
        if self.approval_state == 'pending' or self.approver_ids:
            return
        
        # Check stock availability before sending approval request
        try:
            self._check_stock_guard()
        except ValidationError as e:
            raise UserError(
                _('Cannot request approval because of stock availability issues:\n\n%s') % str(e)
            )
        
        # Create a context that will be used for all operations that might trigger notifications
        # This helps prevent access errors when sending notifications
        safe_context = self.with_context(
            mail_create_nosubscribe=True,  # Don't subscribe followers automatically
            mail_notify_force_send=False,  # Don't send emails immediately
            mail_notrack=True,  # Don't track field changes that would trigger notifications
            tracking_disable=True,  # Disable tracking for this operation
            no_reset_password=True,  # Don't send password reset emails
        )
        
        try:
            # Use sudo to read approver configuration without access restrictions
            approver_lines = self.env['sale.order.approver.line']
            for approver in self.user_id.sudo().sale_approver_ids:
                approver_lines |= self.env['sale.order.approver.line'].sudo().create({
                    'order_id': self.id,
                    'approver_user_id': approver.approver_user_id.id,
                    'required': approver.required,
                    'sequence': approver.sequence,
                })
            
            # Update the order with the new approvers
            safe_context.with_context(skip_approval_check=True).write({
                'approver_ids': [(6, 0, approver_lines.ids)],
                'approval_state': 'pending',
            })
            
            # Get order details using sudo to prevent access errors
            order_details = safe_context._get_approval_activity_note()
            
            # Create activities for each approver
            for approver_line in self.approver_ids:
                try:
                    # Use sudo to prevent access errors when creating activities
                    safe_context.sudo().with_context(
                        mail_create_nosubscribe=True,
                        mail_notify_force_send=False,
                    ).activity_schedule(
                        'mail.mail_activity_data_todo',
                        user_id=approver_line.approver_user_id.id,
                        summary=_('Approve Sale Order %s') % self.name,
                        note=order_details,
                    )
                except Exception as e:
                    _logger.error('Failed to create activity for approver %s: %s', 
                                approver_line.approver_user_id.name, str(e), exc_info=True)
            
            # Update the state if needed
            if self.state in ('draft', 'sent'):
                safe_context.with_context(skip_approval_check=True).write({
                    'state': 'waiting_for_approval'
                })
                
        except Exception as e:
            _logger.error('Error in _auto_request_approval for order %s: %s', 
                         self.name, str(e), exc_info=True)
            # Don't fail the entire operation, just log the error
            return False
            
        return True

    def _get_approval_activity_note(self):
        return '<p>%s</p>' % (_('Please review and approve Sale Order <strong>%s</strong>.') % self.name)

    def action_confirm(self):
        try:
            self._check_stock_guard()
        except Exception as e:
            _logger.error('Stock check failed for order %s: %s', self.name, str(e))
            raise UserError(_('Unable to confirm order due to a stock availability issue. Please try again or contact support.'))

        orders_to_confirm = self.env['sale.order']
        
        for order in self:
            try:
                # Check if the current user is the salesperson assigned to the order
                current_user = self.env.user
                order_salesperson = order.user_id or current_user
                
                # Only require approval if the current user is the same as the salesperson
                # and that salesperson has approvers configured
                # Team leaders or other users can confirm without approval
                requires_approval = (
                    current_user == order_salesperson and 
                    bool(order_salesperson.sudo().sale_approver_ids)
                )
                
                # If approval is required and not yet requested, request it now
                if requires_approval and order.state in ('draft', 'sent') and not order.approver_ids:
                    try:
                        order._auto_request_approval()
                        # Don't confirm, just request approval
                        continue
                    except Exception as e:
                        _logger.error('Failed to request approval for order %s: %s', order.name, str(e), exc_info=True)
                        raise UserError(
                            _('Failed to process approval request for this quotation. '
                              'The approval workflow could not be initiated.')
                        ) from None
                
                # If already waiting for approval, check if approved or if current user can bypass
                if order.state == 'waiting_for_approval':
                    # Team leaders or users who are not the salesperson can bypass approval
                    can_bypass_approval = current_user != order_salesperson
                    
                    if not order.approved_by_ids and not can_bypass_approval:
                        raise UserError(
                            _('This quotation requires approval before it can be confirmed.\n'
                              'Please wait for an approver to approve the order.')
                        )
                    # Set state to draft so super().action_confirm() can convert it to 'sale'
                    order.with_context(skip_approval_check=True).write({'state': 'draft'})
                
                orders_to_confirm |= order
                
            except UserError:
                # Re-raise UserError as is (these are intentional messages for the user)
                raise
            except Exception as e:
                _logger.error('Unexpected error during order confirmation %s: %s', order.name, str(e), exc_info=True)
                raise UserError(
                    _('An unexpected error occurred while processing your request. '
                      'Please try again or contact support if the problem persists.')
                ) from None

        result = True
        if orders_to_confirm:
            try:
                # Use sudo to prevent access errors when confirming orders
                result = super(SaleOrder, orders_to_confirm.sudo()).action_confirm()
                orders_to_confirm._close_approval_activities_post_confirm()
            except Exception as e:
                _logger.error('Failed to confirm orders: %s', str(e), exc_info=True)
                raise UserError(
                    _('Failed to confirm the order. Please verify the order details and try again.')
                ) from None

        return result

    def _close_approval_activities_post_confirm(self):
        """Update approval activities after order confirmation.
        
        This method is called after an order is confirmed to update any open
        approval activities with a confirmation note. It's designed to be
        resilient to access errors that might occur when reading partner data.
        """
        if not self:
            return
            
        # Use sudo to prevent access errors when reading activities
        Activity = self.env['mail.activity'].sudo()
        todo = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        
        if not todo:
            _logger.warning('Todo activity type not found, skipping activity updates')
            return
            
        for order in self.filtered('approval_required'):
            try:
                # Search for activities in a way that won't trigger access errors
                activities = Activity.search([
                    ('res_model', '=', 'sale.order'),
                    ('res_id', '=', order.id),
                    ('activity_type_id', '=', todo.id),
                ])
                
                if not activities:
                    continue
                    
                confirmation_status = _('✓ ORDER CONFIRMED on %s') % (
                    fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
                
                # Update activities with confirmation status
                for activity in activities:
                    try:
                        activity.write({
                            'note': (activity.note or '') + '\n\n' + confirmation_status
                        })
                    except Exception as e:
                        _logger.error(
                            'Failed to update activity %s for order %s: %s',
                            activity.id, order.name, str(e), exc_info=True
                        )
                        
            except Exception as e:
                _logger.error(
                    'Error updating activities for order %s: %s',
                    order.name, str(e), exc_info=True
                )
                # Continue with other orders even if one fails

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
            raise UserError(_('This order is not pending approval.'))
        
        if self.env.user not in self.approver_ids.mapped('approver_user_id'):
            raise UserError(_('You are not authorized to approve this order. Only designated approvers can approve.'))
        
        if self.env.user in self.approved_by_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Already Approved'),
                    'message': _('You have already approved this sale order.'),
                    'type': 'info',
                    'sticky': False,
                }
            }
        
        # Create a safe context to prevent notification and tracking
        safe_context = self.with_context(
            mail_create_nosubscribe=True,
            mail_notify_force_send=False,
            mail_notrack=True,
            tracking_disable=True,
            no_reset_password=True,
        )
        
        try:
            # Update approved_by_ids using sudo to prevent access errors
            self.sudo().approved_by_ids = [(4, self.env.user.id)]
            
            # Update approver line status
            approver_line = self.approver_ids.filtered(
                lambda a: a.approver_user_id == self.env.user
            )
            if approver_line:
                approver_line.sudo().state = 'approved'
            
            # Update activities with sudo to prevent access errors
            try:
                Activity = self.env['mail.activity'].sudo()
                todo = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
                
                if todo:
                    activities = Activity.search([
                        ('res_model', '=', 'sale.order'),
                        ('res_id', '=', self.id),
                        ('user_id', '=', self.env.user.id),
                        ('activity_type_id', '=', todo.id),
                    ])
                    
                    for activity in activities:
                        try:
                            approval_status = _('✓ APPROVED by %s on %s') % (
                                self.env.user.name,
                                fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            )
                            activity.write({
                                'note': (activity.note or '') + '\n\n' + approval_status
                            })
                        except Exception as e:
                            _logger.error('Failed to update activity %s: %s', activity.id, str(e), exc_info=True)
            except Exception as e:
                _logger.error('Error updating activities: %s', str(e), exc_info=True)
            
            # Approve immediately when any approver approves
            safe_context.with_context(skip_approval_check=True).write({
                'approval_state': 'approved'
            })
            
            # Automatically confirm the order when approved
            if self.state == 'waiting_for_approval':
                try:
                    # Set state to draft first, then call action_confirm to convert to 'sale'
                    safe_context.with_context(skip_approval_check=True).write({
                        'state': 'draft',
                        'approval_state': 'approved'
                    })
                    
                    # Call action_confirm which will convert draft directly to 'sale' (Sales Order)
                    safe_context.with_context(skip_approval_check=True).action_confirm()
                    
                    # Post message with sudo to prevent access errors
                    self.sudo().message_post(
                        body=_('Sale order has been approved by %s and automatically confirmed.') % self.env.user.name,
                        subject=_('Order Approved and Confirmed'),
                        subtype_id=self.env.ref('mail.mt_comment').id,
                    )
                except Exception as e:
                    _logger.error('Failed to auto-confirm order after approval: %s', str(e), exc_info=True)
                    self.sudo().message_post(
                        body=_('Sale order has been approved by %s. Please confirm manually.') % self.env.user.name,
                        subject=_('Order Approved'),
                        subtype_id=self.env.ref('mail.mt_comment').id,
                    )
            else:
                self.sudo().message_post(
                    body=_('Sale order has been approved by %s.') % self.env.user.name,
                    subject=_('Order Approved'),
                    subtype_id=self.env.ref('mail.mt_comment').id,
                )
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'current',
                'context': self.env.context,
            }
            
        except Exception as e:
            _logger.error('Error in action_approve for order %s: %s', self.name, str(e), exc_info=True)
            raise UserError(
                _('An error occurred while processing your approval. Please try again or contact support.')
            ) from None

    def action_reject(self):
        self.ensure_one()
        
        if self.state != 'waiting_for_approval':
            raise UserError(_('This order is not pending approval.'))
        
        if self.env.user not in self.approver_ids.mapped('approver_user_id'):
            raise UserError(_('You are not authorized to reject this order. Only designated approvers can reject.'))
        
        # Create a safe context to prevent notification and tracking
        safe_context = self.with_context(
            mail_create_nosubscribe=True,
            mail_notify_force_send=False,
            mail_notrack=True,
            tracking_disable=True,
            no_reset_password=True,
        )
        
        try:
            # Update approver line status with sudo to prevent access errors
            approver_line = self.approver_ids.filtered(
                lambda a: a.approver_user_id == self.env.user
            )
            if approver_line:
                approver_line.sudo().state = 'rejected'
            
            # Update activities with sudo to prevent access errors
            try:
                Activity = self.env['mail.activity'].sudo()
                todo = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
                
                if todo:
                    activities = Activity.search([
                        ('res_model', '=', 'sale.order'),
                        ('res_id', '=', self.id),
                        ('user_id', '=', self.env.user.id),
                        ('activity_type_id', '=', todo.id),
                    ])
                    
                    for activity in activities:
                        try:
                            rejection_status = _('✗ REJECTED by %s on %s') % (
                                self.env.user.name,
                                fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            )
                            activity.write({
                                'note': (activity.note or '') + '\n\n' + rejection_status
                            })
                        except Exception as e:
                            _logger.error('Failed to update activity %s: %s', activity.id, str(e), exc_info=True)
            except Exception as e:
                _logger.error('Error updating activities: %s', str(e), exc_info=True)
            
            # Update order status
            safe_context.with_context(skip_approval_check=True).write({
                'approval_state': 'rejected',
                'state': 'draft',
                'approver_ids': [(5, 0, 0)],  # Clear all approver lines
                'approved_by_ids': [(5, 0, 0)],  # Clear approved by list
            })
            
            # Notify the requester
            self.sudo().message_post(
                body=_('Sale order has been rejected by %s. The order has been reset to draft for editing.') % self.env.user.name,
                subject=_('Order Rejected'),
                subtype_id=self.env.ref('mail.mt_comment').id,
            )
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'current',
                'context': self.env.context,
            }
            
        except Exception as e:
            _logger.error('Error in action_reject for order %s: %s', self.name, str(e), exc_info=True)
            raise UserError(
                _('An error occurred while processing your rejection. Please try again or contact support.')
            ) from None
