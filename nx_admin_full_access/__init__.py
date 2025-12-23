def _post_init_hook(env):
    """Force update the base res.partner rule to allow creates and use 'in' for multi-company."""
    rule = env.ref('base.res_partner_rule', raise_if_not_found=False)
    if rule:
        rule.write({
            'domain_force': "['|', '|', '|', ('id', '=', False), ('partner_share', '=', False), ('company_id', 'in', company_ids), ('company_id', '=', False)]"
        })
