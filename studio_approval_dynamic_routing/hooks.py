def pre_init_hook(cr):
    """Create dynamic-routing columns before Studio register hooks run."""
    cr.execute("ALTER TABLE studio_approval_rule ADD COLUMN IF NOT EXISTS python_code text")
    cr.execute("ALTER TABLE studio_approval_rule ADD COLUMN IF NOT EXISTS notify_python_code text")
