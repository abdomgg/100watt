import logging
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PurchaseOrderApprover(models.Model):
    _name = 'purchase.order.approver'
    _description = 'Purchase Order Approver'
    _order = 'sequence, id'

    user_id = fields.Many2one('res.users', string='User', required=True, ondelete='cascade')
    approver_user_id = fields.Many2one('res.users', string='Approver', required=True)
    required = fields.Boolean(string='Required', default=True)
    sequence = fields.Integer(string='Sequence', default=10)


class PurchaseOrderApproverLine(models.Model):
    _name = 'purchase.order.approver.line'
    _description = 'Purchase Order Approver Line'
    _order = 'sequence, id'

    order_id = fields.Many2one('purchase.order', string='Purchase Order', required=True, ondelete='cascade')
    approver_user_id = fields.Many2one('res.users', string='Approver', required=True)
    required = fields.Boolean(string='Required', default=True)
    sequence = fields.Integer(string='Sequence', default=10)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='pending', readonly=True)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    approval_required = fields.Boolean(string='Approval Required', compute='_compute_approval_required', store=False)
    state = fields.Selection(
        selection=[
            ('draft', 'RFQ'),
            ('sent', 'RFQ Sent'),
            ('waiting_for_approval', 'Pending Approval'),
            ('to approve', 'To Approve'),
            ('purchase', 'Purchase Order'),
            ('done', 'Locked'),
            ('cancel', 'Cancelled')
        ],
        string='Status',
        readonly=True, index=True, copy=False, default='draft', tracking=True
    )
    approval_state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Approval Status', default='draft', readonly=True, copy=False, tracking=True)
    approver_ids = fields.One2many('purchase.order.approver.line', 'order_id', string='Approvers', copy=False)
    approved_by_ids = fields.Many2many(
        'res.users',
        'purchase_order_approval_rel',
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
                # Only show approval required if current user is the buyer with approvers
                order.approval_required = (
                    current_user == order.user_id and 
                    bool(order.user_id.sudo().purchase_approver_ids)
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
        order = super(PurchaseOrder, self).create(vals)
        
        current_user = self.env.user
        user_id = order.user_id or current_user
        
        # Only auto-request approval if current user is the buyer
        # Managers creating orders for their buyers should not trigger approval
        if current_user != user_id:
            return order
            
        has_approvers = bool(user_id.sudo().purchase_approver_ids) if user_id else False
        
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
        result = super(PurchaseOrder, self).write(vals)
        
        if skip_approval:
            return result
        
        current_user = self.env.user
        for order in self:
            user_id = order.user_id or current_user
            
            # Only auto-request approval if current user is the buyer
            # Managers creating/editing orders for their buyers should not trigger approval
            if current_user != user_id:
                continue
                
            has_approvers = bool(user_id.sudo().purchase_approver_ids) if user_id else False
            
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
        if not self.user_id or not self.user_id.sudo().purchase_approver_ids:
            return False
        
        if self.approval_state == 'pending' or self.approver_ids:
            return True
        
        # Create a context that will be used for all operations that might trigger notifications
        safe_context = self.with_context(
            mail_create_nosubscribe=True,  # Don't subscribe followers automatically
            mail_notify_force_send=False,  # Don't send emails immediately
            mail_notrack=True,  # Don't track field changes that would trigger notifications
            tracking_disable=True,  # Disable tracking for this operation
            no_reset_password=True,  # Don't send password reset emails
        )
        
        try:
            # Use sudo to read approver configuration without access restrictions
            approver_lines = self.env['purchase.order.approver.line']
            for approver in self.user_id.sudo().purchase_approver_ids:
                approver_lines |= self.env['purchase.order.approver.line'].sudo().create({
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
                        summary=_('Approve Purchase Order %s') % self.name,
                        note=order_details,
                    )
                except Exception as e:
                    _logger.error('Failed to create activity for approver %s: %s', 
                                approver_line.approver_user_id.name, str(e), exc_info=True)
            
            # Update the state if needed
            if self.state == 'draft':
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
        return '<p>%s</p>' % (_('Please review and approve Purchase Order <strong>%s</strong>.') % self.name)

    def button_confirm(self):
        orders_to_confirm = self.env['purchase.order']
        
        for order in self:
            try:
                # Check if the current user is the buyer assigned to the order
                current_user = self.env.user
                order_buyer = order.user_id or current_user
                
                # Only require approval if the current user is the same as the buyer
                # and that buyer has approvers configured
                # Managers or other users can confirm without approval
                requires_approval = (
                    current_user == order_buyer and 
                    bool(order_buyer.sudo().purchase_approver_ids)
                )
                
                # If approval is required and not yet requested, request it now
                if requires_approval and order.state == 'draft' and not order.approver_ids:
                    try:
                        if order._auto_request_approval():
                            # Show notification that approval was requested
                            return {
                                'type': 'ir.actions.client',
                                'tag': 'display_notification',
                                'params': {
                                    'title': _('Approval Requested'),
                                    'message': _('This purchase order requires approval. Approval request has been sent to the designated approvers.'),
                                    'type': 'warning',
                                    'sticky': False,
                                    'next': {'type': 'ir.actions.act_window_close'},
                                }
                            }
                        else:
                            _logger.warning('Auto-approval request failed silently for order %s', order.name)
                            # Continue with normal confirmation if approval request fails
                            orders_to_confirm |= order
                    except Exception as e:
                        _logger.error('Failed to request approval for order %s: %s', 
                                    order.name, str(e), exc_info=True)
                        # Continue with normal confirmation if approval request fails
                        orders_to_confirm |= order
                
                # If already waiting for approval, check if approved or if current user can bypass
                elif order.state == 'waiting_for_approval':
                    # Managers or users who are not the buyer can bypass approval
                    can_bypass_approval = current_user != order_buyer
                    
                    if not order.approved_by_ids and not can_bypass_approval:
                        raise UserError(
                            _('This purchase order requires approval before it can be confirmed.\n'
                              'Please wait for an approver to approve the order.')
                        )
                    # Set state to draft so super().button_confirm() can process it
                    order.with_context(skip_approval_check=True).write({'state': 'draft'})
                    orders_to_confirm |= order
                
                else:
                    orders_to_confirm |= order
                
            except UserError:
                # Re-raise UserError as is (these are intentional messages for the user)
                raise
            except Exception as e:
                _logger.error('Unexpected error during purchase order confirmation %s: %s', 
                            order.name, str(e), exc_info=True)
                raise UserError(
                    _('An unexpected error occurred while processing your request. '
                      'Please try again or contact support if the problem persists.')
                ) from None
        
        result = True
        if orders_to_confirm:
            try:
                # Use sudo to prevent access errors during confirmation
                result = super(PurchaseOrder, orders_to_confirm.sudo()).button_confirm()
                
                # Update activity notes for confirmed orders that required approval
                confirmed_orders = orders_to_confirm.filtered('approval_required')
                if confirmed_orders:
                    try:
                        # Use sudo to prevent access errors when updating activities
                        Activity = self.env['mail.activity'].sudo()
                        todo = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
                        
                        if todo:
                            activities = Activity.search([
                                ('res_model', '=', 'purchase.order'),
                                ('res_id', 'in', confirmed_orders.ids),
                                ('activity_type_id', '=', todo.id),
                            ])
                            
                            for activity in activities:
                                try:
                                    confirmation_status = _('✓ ORDER CONFIRMED on %s') % (
                                        fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    )
                                    activity.write({
                                        'note': (activity.note or '') + '\n\n' + confirmation_status
                                    })
                                except Exception as e:
                                    _logger.error(
                                        'Failed to update activity %s for order %s: %s',
                                        activity.id, activity.res_id, str(e), exc_info=True
                                    )
                    except Exception as e:
                        _logger.error(
                            'Error updating activities for purchase orders: %s', 
                            str(e), exc_info=True
                        )
                        
            except Exception as e:
                _logger.error('Failed to confirm purchase orders: %s', str(e), exc_info=True)
                raise UserError(
                    _('Failed to confirm the purchase order. Please verify the order details and try again.')
                ) from None
        
        return result

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
                    'message': _('You have already approved this purchase order.'),
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
                        ('res_model', '=', 'purchase.order'),
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
                    # Set state to sent first to allow confirmation
                    safe_context.with_context(skip_approval_check=True).write({
                        'state': 'sent',
                        'approval_state': 'approved'
                    })
                    
                    # Automatically confirm the order (bypass approval check since already approved)
                    safe_context.with_context(skip_approval_check=True).button_confirm()
                    
                    # Post message with sudo to prevent access errors
                    self.sudo().message_post(
                        body=_('Purchase order has been approved by %s and automatically confirmed.') % self.env.user.name,
                        subject=_('Order Approved and Confirmed'),
                        subtype_id=self.env.ref('mail.mt_comment').id,
                    )
                except Exception as e:
                    _logger.error('Failed to auto-confirm order after approval: %s', str(e), exc_info=True)
                    self.sudo().message_post(
                        body=_('Purchase order has been approved by %s. Please confirm manually.') % self.env.user.name,
                        subject=_('Order Approved'),
                        subtype_id=self.env.ref('mail.mt_comment').id,
                    )
            else:
                self.sudo().message_post(
                    body=_('Purchase order has been approved by %s.') % self.env.user.name,
                    subject=_('Order Approved'),
                    subtype_id=self.env.ref('mail.mt_comment').id,
                )
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
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
                        ('res_model', '=', 'purchase.order'),
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
                body=_('Purchase order has been rejected by %s. The order has been reset to draft for editing.') % self.env.user.name,
                subject=_('Order Rejected'),
                subtype_id=self.env.ref('mail.mt_comment').id,
            )
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
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
