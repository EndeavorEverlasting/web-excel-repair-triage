# Pull Request Execution Order

Per latest direction, process and close pull requests in stack-pop order:

1. Pull Request 3
2. Pull Request 2
3. Pull Request 1

Rationale: treat PRs like a stack (LIFO), so the most recent item is handled first as changes are pushed to `main`.
