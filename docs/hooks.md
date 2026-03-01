# Repository Hooks

This repo includes a repository-level pre-commit hook to validate Terraform formatting/validation and Python syntax.

To enable the hooks locally:

```bash
git config core.hooksPath .githooks
```

Notes:
- The hook runs only on staged files. It performs `terraform fmt -check` and `terraform validate` when `.tf` files are staged.
- If you need to bypass the hook for a one-off commit, use `git commit --no-verify`.

The `.githooks/pre-commit` is committed to the repo; enabling `core.hooksPath` makes it active for contributors.
