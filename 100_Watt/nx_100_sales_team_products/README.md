# Sales Team Products Filter - 100 Watt

## Description
This module allows you to assign specific products to sales teams and filter products by categories. Each sales team will only see the products assigned to them and/or products in their allowed categories.

## Features
- **Category Filter per Team**: Assign product categories to each sales team
- **Product-Level Filter**: "تفعيل فلتر فريق المبيعات" (Enable Sales Team Filter) checkbox
- **Sales Team Assignment**: Assign multiple sales teams to each product
- **Automatic Filtering**: Sales team members automatically see only their assigned products and categories
- **Hierarchical Categories**: Supports parent/child category relationships
- **Flexible Control**: Products without teams assigned or with filter disabled are visible to everyone
- Full Arabic language support

## Installation
1. Copy this module to your Odoo addons directory
2. Update the apps list
3. Install the module from Apps menu

## Configuration
No special configuration needed. The module works automatically after installation.

## Usage

### Sales Team Configuration (Category Filter):
1. Go to **Sales → Configuration → Sales Teams**
2. Open a sales team or create a new one
3. Go to the **"فئات المنتجات"** (Product Categories) tab
4. Select the product categories that this team should see
5. Save the sales team

### Product Configuration (Team Assignment):
1. Go to **Sales → Products → Products**
2. Open any product
3. In the product form, you'll see a new section: **"فلتر فريق المبيعات"** (Sales Team Filter)
4. Check the box **"تفعيل فلتر فريق المبيعات"** (Enable Sales Team Filter)
5. Select the sales teams that should see this product in **"فرق المبيعات"** field
6. Save the product

### How It Works:
The filtering combines both category and team filters:

**Category Filter (Team Level):**
- If a team has categories selected → Team members see only products in those categories
- If a team has NO categories selected → Team members see products in all categories

**Team Filter (Product Level):**
- **Filter Disabled**: Product is visible to all users
- **Filter Enabled + No Teams**: Product is visible to all users
- **Filter Enabled + Teams Selected**: Product is visible ONLY to members of selected teams

### Examples:

**Example 1 - Category Filtering:**
- Team A has categories: "Electronics", "Computers"
- Team B has categories: "Furniture", "Office Supplies"
- Members of Team A only see products in Electronics and Computers categories
- Members of Team B only see products in Furniture and Office Supplies categories

**Example 2 - Product Team Assignment:**
- Product "Special Widget" has filter enabled and assigned to "Team A"
- Only members of "Team A" can see "Special Widget"
- Members of other teams won't see it

**Example 3 - Combined Filtering:**
- Team A has category "Electronics"
- Product "Laptop X" is in "Electronics" category AND assigned to Team A
- Only Team A members can see "Laptop X"
- If Product "Laptop Y" is in "Electronics" but NOT assigned to any team, Team A can still see it (category match)

## Dependencies
- base
- product
- sale
- sales_team

## Technical Details
- **Module Name**: nx_100_sales_team_products
- **Version**: 1.0.0
- **Author**: 100 Watt
- **Category**: Sales
- **License**: LGPL-3

## Fields Added

### Sales Team (crm.team):
- `product_category_ids` (Many2many): Product categories that this team can see

### Product Template (product.template):
- `use_sales_team_filter` (Boolean): Enable/disable the sales team filter
- `sales_team_ids` (Many2many): List of sales teams that can see this product

## Security Rules
The module adds record rules that automatically filter products based on:
- User's current sales team
- Team's allowed product categories
- Product's filter status
- Product's assigned teams
- Product's category (including parent categories)

## Support
For support and questions, contact the 100 Watt development team.

