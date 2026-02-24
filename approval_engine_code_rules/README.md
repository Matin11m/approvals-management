# Approval Engine - Python Code Rules

Extension module for `approval_engine`.

## Features
- Adds per-request Python execute-code fields.
- Supports execution modes: manual / approve / reject / both.
- Runs code with `safe_eval(mode='exec')`.
- Blocks action when code sets `result = False`.

## Variables available in code
- `request`
- `record`
- `env`
- `user`
- `action` (`manual`/`approve`/`reject`)

## Expected outputs
- `result` (bool): allow/block action
- `message` (str): optional user message when blocked

Example:
```python
if record.amount_total > 10000:
    result = False
    message = 'Amount is over allowed threshold.'
```
