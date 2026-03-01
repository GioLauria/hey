# Terraform

Notes and tips for working with the Terraform configuration in this repository.

- Run `terraform init -backend=false` before `terraform validate` when working locally to avoid modifying remote state.
- If you change Terraform provider versions, verify resource argument compatibility (some older providers use `hash_key` on `aws_dynamodb_table`; newer providers may prefer `key_schema`).
- Validate and format before committing:

```bash
cd terraform
terraform fmt
terraform init -backend=false
terraform validate
```

If you plan to change provider versions, test migration in a disposable branch and update docs accordingly.
