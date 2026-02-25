def pre_init_hook(env_or_cr):
    """Ensure columns exist before web_studio register hooks read the table."""
    cr = getattr(env_or_cr, "cr", env_or_cr)
    cr.execute("ALTER TABLE studio_approval_rule ADD COLUMN IF NOT EXISTS python_code text")
    cr.execute("ALTER TABLE studio_approval_rule ADD COLUMN IF NOT EXISTS notify_python_code text")
