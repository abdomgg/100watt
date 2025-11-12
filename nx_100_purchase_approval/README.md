# Purchase Order Approval - 100 Watt

## Description
This module adds an approval workflow for purchase orders in Odoo, similar to the sale order approval module.

## Features
- Configure approvers in user settings (Purchase Approvers tab)
- Require approval before confirming purchase orders
- Send approval activities to specified approvers
- Track approval status
- Multiple approvers support with required/optional settings
- "Pending Approval" state in the purchase order status bar
- Automatic approval request when vendor is selected

## Installation
1. Place this module in your Odoo addons path
2. Update the apps list
3. Install the module "Purchase Order Approval - 100 Watt"

## Configuration
1. Go to Settings > Users & Companies > Users
2. Open a user who creates purchase orders
3. Go to the "Purchase Approvers" tab
4. Add approvers who can approve purchase orders created by this user
5. Mark approvers as "Required" if their approval is mandatory

## Usage
1. When creating a new purchase order (RFQ), select a vendor
2. The system will automatically request approval if the user has approvers configured
3. The purchase order state will change to "Pending Approval"
4. Approvers will receive an activity notification
5. Approvers can approve or reject the purchase order
6. Once all required approvers have approved, the purchase order can be confirmed
7. The "Confirm Order" button is hidden while waiting for approval

## Notes
- Approvers need Purchase module access to see activities in the Purchase module
- The approval state is visible in the purchase order form under the "Approval" tab
- Approval activities remain visible after confirmation for history tracking

## Module developed for 100 Watt

