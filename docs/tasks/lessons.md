# Lessons

## Planned Tree Is Not Real Tree

### What Went Wrong

Detailed architecture and master-plan docs can look like implementation evidence even when the repo only contains planning documents.

### Preventive Rule

Always verify a file or folder exists in the workspace before describing it as part of the current codebase.

### When To Re-Check This Lesson

- before editing any planned path from the root docs
- before claiming a route, schema, or service already exists
- whenever the repo is still early-stage or scaffold-only

## Early Milestones Must Not Depend On Later Stories

### What Went Wrong

A bootstrap milestone for the visible UI picked verification targets that depend on backend stories scheduled later, such as real attendance data from `/api/v1/attendance`.

### Preventive Rule

Keep each milestone's exit checks limited to work that milestone actually delivers. If a check depends on a later story, move that check to the later milestone or explicitly mark it as stubbed.

### When To Re-Check This Lesson

- when defining milestone exit criteria
- when splitting "runnable shell" versus "fully integrated" goals
- before using API responses as proof that a UI-only milestone is complete

## Bootstrap Paths Should Not Require Unavailable Credentials

### What Went Wrong

The plan assumes Azure credentials may not be available immediately, but part of the early backend foundation still leans on Azure setup. That can block the first runnable UI goal for reasons unrelated to UI scaffolding.

### Preventive Rule

For the first runnable milestone, keep external-provider dependencies optional, stubbed, or deferred unless the milestone explicitly exists to validate that provider.

### When To Re-Check This Lesson

- when a local bootstrap plan includes cloud services
- when fail-fast config validation is being added
- before making "can run locally" depend on third-party credentials

## Route Contracts Must Stay Separate From Provider Contracts

### What Went Wrong

A plan check for the recognition endpoint started expecting provider-style fields like `subject_id` in the API response, even though the route-level contract in the master plan uses route fields like `status`, `identity_id`, `similarity`, `log_id`, and optional `review_id`.

### Preventive Rule

When writing plans or tests, verify contracts at the correct layer. Provider responses belong behind the provider abstraction. Public API routes should be validated against their documented route schemas, not the provider's internal shape.

### When To Re-Check This Lesson

- when adding endpoint verification steps
- when mapping provider methods to route responses
- before writing API tests from architecture notes

## Always Verify Files Actually Exist In Workspace

### What Went Wrong

When completing the Supabase plan, I verified code existed by reading files but did not explicitly state that the files were verified to exist in the workspace. The todo.md verification notes claimed certain files existed but should have included explicit file existence verification.

### Correct Action Taken

Used glob to verify each file path actually exists in the workspace before claiming it as evidence:
```python
glob("entrylens-api/app/supabase.py")  # returned file path = confirmed exists
```

### Preventive Rule

When marking work complete or writing verification notes, always use file search tools (glob, find) to confirm files exist. Do not just read files - confirm they exist in the workspace structure first.

### When To Re-Check This Lesson

- before marking any work "complete" in todo.md
- before claiming files exist in verification notes
- when updating project-truth docs with new file locations



<!-- graphify-links:start -->
## Graph Links

- [[graphify-out/wiki/index|Graphify Wiki]]
- [[graphify-out/GRAPH_REPORT|Graph Report]]
<!-- graphify-links:end -->
