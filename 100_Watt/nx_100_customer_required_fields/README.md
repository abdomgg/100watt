# Customer Required Fields - 100 Watt

## Description
This module makes the following fields required when creating a customer in Odoo:
- **Name** (الاسم)
- **Phone Number** (رقم الهاتف)
- **Address/Street** (العنوان)

And adds a required Tax ID field in sales orders that auto-populates from the customer.

## Features
- Makes customer name, phone, and address mandatory fields
- Adds Tax ID field to sales orders (required)
- Auto-populates Tax ID from customer if available
- Allows manual entry if customer doesn't have Tax ID
- Full Arabic language support
- Validation at both UI and database level
- Works with Odoo Community Edition

## Installation
1. Copy this module to your Odoo addons directory
2. Update the apps list
3. Install the module from Apps menu

## Configuration
No configuration needed. The module works automatically after installation.

## Usage

### Customer Creation:
When creating or editing a customer, the system will require:
- Name field to be filled
- Phone field to be filled  
- Street/Address field to be filled

### Sales Order:
When creating a sales order:
- A Tax ID field appears after the customer field
- If customer has a Tax ID, it auto-populates
- If customer doesn't have a Tax ID, you must enter it manually
- The field is required and cannot be left empty

If any of these required fields are empty, the system will show an error message in Arabic.

## Dependencies
- base
- contacts
- sale

## Technical Details
- **Module Name**: nx_100_customer_required_fields
- **Version**: 1.0.0
- **Author**: 100 Watt
- **Category**: Sales
- **License**: LGPL-3

## Support
For support and questions, contact the 100 Watt development team.

