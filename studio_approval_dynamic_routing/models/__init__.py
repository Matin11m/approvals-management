"""Dynamic routing model entrypoint.

This module intentionally loads only `approval_rule_dynamic` as the single
source of truth for approval dynamic logic.
"""

from . import approval_rule_dynamic
