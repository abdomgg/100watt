# Sale Order Approval - 100 Watt

## Description
This module adds an approval workflow for sale orders/quotations. When a user creates a new quotation, it automatically requires approval from configured approvers before the quotation can be confirmed.

## Features
- **Configure Approvers**: In user settings (Sales tab), administrators can configure approvers for each user
- **Automatic Approval Request**: When a quotation is created, approval is automatically requested if the user has approvers configured
- **Activity-Based Approval**: Approval requests are sent as activities to the specified approvers
- **Required/Optional Approvers**: Each approver can be marked as required or optional
- **Approval Status Tracking**: Track approval status (Draft, Pending, Approved, Rejected)
- **Prevent Confirmation**: Quotations cannot be confirmed until all required approvers have approved

## Installation
1. Place the module in your Odoo addons path
2. Update the Apps list
3. Install "Sale Order Approval - 100 Watt"

## Configuration

### Setting Up Approvers
1. Go to **Settings > Users & Companies > Users**
2. Open a user's form
3. Go to the **Sales** tab
4. In the **Approvers** section, add approvers:
   - Click "Add a line"
   - Select the approver user
   - Check "Required" if this approver must approve (uncheck for optional)
5. Save the user

### Using the Approval Workflow
1. When a user with configured approvers creates a new quotation:
   - Approval is automatically requested
   - Activities are created for each approver
   - The quotation status shows "Pending Approval"

2. Approvers receive an activity:
   - They can click "Approve" or "Reject" from the sale order form
   - Required approvers must approve before confirmation

3. Once all required approvers have approved:
   - The quotation status changes to "Approved"
   - The "Confirm" button becomes available
   - The quotation can be confirmed

## Technical Details

### Models
- `sale.order.approver`: Stores approver configuration for users
- `sale.order.approver.line`: Stores approvers for each sale order
- `sale.order`: Extended with approval fields and workflow

### Fields Added to Sale Order
- `approval_required`: Computed field indicating if approval is needed
- `approval_state`: Status of approval (draft, pending, approved, rejected)
- `approver_ids`: List of approvers for this order
- `approved_by_ids`: Users who have approved the order

### Workflow
1. Quotation created → Auto-request approval (if user has approvers)
2. Activities sent to approvers
3. Approvers approve/reject
4. Once all required approvers approve → Order can be confirmed

## Troubleshooting

### Access Rights Error: "doesn't have 'create' access to: Sales Order Line"

If you encounter this error when creating sale orders, it means the user doesn't have the necessary permissions. To fix:

1. **Check User Groups**: Ensure the user is in the "Sales / User" group (`sales_team.group_sale_salesman`)
   - Go to **Settings > Users & Companies > Users**
   - Open the user's form
   - Go to **Access Rights** tab
   - Ensure "Sales / User" is checked

2. **Check Record Rules**: If the error occurs with some customers but not others, it might be a record rule issue:
   - Go to **Settings > Technical > Security > Record Rules**
   - Check rules for `sale.order` and `sale.order.line`
   - Ensure the user can create records for the specific customer/company

3. **Check Company Access**: Ensure the user has access to the company of the customer:
   - Go to **Settings > Users & Companies > Users**
   - Open the user's form
   - Go to **Companies** tab
   - Ensure the company is in the "Allowed Companies" list

## Module Information
- **Author**: Ahmed Tarek
- **Version**: 1.0.0
- **License**: LGPL-3
- **Dependencies**: base, sale, mail

