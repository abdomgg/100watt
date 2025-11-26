# -*- coding: utf-8 -*-

def _update_sale_approvers_translation(env):
    """Helper function to update Sales Approvers translation"""
    # Get the view
    try:
        view = env.ref('nx_100_sale_approval.view_users_form_sale_approvers')
    except:
        return False
    
    # Find all Arabic languages installed in the system
    # Odoo typically uses ar_001 for Modern Standard Arabic
    arabic_langs = env['res.lang'].search([('code', 'like', 'ar%'), ('active', '=', True)])
    
    # If no active Arabic languages found, search all Arabic languages
    if not arabic_langs:
        arabic_langs = env['res.lang'].search([('code', 'like', 'ar%')])
    
    # If still no Arabic languages found, try common codes
    if not arabic_langs:
        for lang_code in ['ar_001', 'ar_AR', 'ar', 'ar_SY', 'ar_SA', 'ar_EG', 'ar_AE', 'ar_JO', 'ar_LB']:
            lang = env['res.lang'].search([('code', '=', lang_code)], limit=1)
            if lang:
                arabic_langs |= lang
                break
    
    if not arabic_langs:
        return False
    
    # Update or create translation for "Sales Approvers" for all Arabic languages
    # Prioritize ar_001 (Modern Standard Arabic) if it exists
    sorted_langs = sorted(arabic_langs, key=lambda l: 0 if l.code == 'ar_001' else 1)
    
    updated = False
    for lang in sorted_langs:
        lang_code = lang.code
        # Search for any translation matching this string (with or without res_id)
        translation = env['ir.translation'].search([
            ('type', 'in', ['model', 'model_terms']),
            ('name', '=', 'ir.ui.view,arch_db'),
            ('lang', '=', lang_code),
            ('src', '=', 'Sales Approvers')
        ], limit=1)
        
        if translation:
            # Update existing translation (ensure res_id is set)
            translation.write({
                'value': 'موافقو المبيعات', 
                'state': 'translated',
                'res_id': view.id
            })
            updated = True
        else:
            # Create new translation - always try with res_id first
            try:
                env['ir.translation'].create({
                    'type': 'model',
                    'name': 'ir.ui.view,arch_db',
                    'lang': lang_code,
                    'src': 'Sales Approvers',
                    'value': 'موافقو المبيعات',
                    'res_id': view.id,
                    'state': 'translated'
                })
                updated = True
            except Exception as e:
                # If that fails, try without res_id
                try:
                    env['ir.translation'].create({
                        'type': 'model',
                        'name': 'ir.ui.view,arch_db',
                        'lang': lang_code,
                        'src': 'Sales Approvers',
                        'value': 'موافقو المبيعات',
                        'state': 'translated'
                    })
                    updated = True
                except:
                    # Log but continue
                    import logging
                    _logger = logging.getLogger(__name__)
                    _logger.warning("Failed to create translation for Sales Approvers in %s: %s", lang_code, str(e))
    
    return updated

def post_init_hook(cr, registry):
    """Update Arabic translations for view strings after module installation"""
    from odoo import api, SUPERUSER_ID
    
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        result = _update_sale_approvers_translation(env)
        if result:
            cr.commit()
    except Exception as e:
        # Log error but don't fail installation
        import logging
        _logger = logging.getLogger(__name__)
        _logger.warning("Failed to update Sales Approvers translation: %s", str(e))
        cr.rollback()

