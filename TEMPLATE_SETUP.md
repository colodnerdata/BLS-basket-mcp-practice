# Set up this template

This is a small Python default for solo development with AI assistance.
It provides repeatable commands, checks, review prompts, and concise project
context. Add specialized tooling when a project needs it.

## Create the template repository itself

1. Create `colodnerdata/solo-project-template` on GitHub. Private is a sensible
   starting choice while refining your defaults. Start with an empty repository
   if you are uploading or pushing these files.
2. Add the contents of this directory at the repository root, including dotfiles,
   and push the initial commit. Do not upload the enclosing ZIP as the source.
3. Open Settings → General and select **Template repository**.
4. Confirm the CI check runs. Connect your coding tools to this new repository
   if their GitHub installation is limited to selected repositories.

Creating a repository and changing its template setting are GitHub operations;
having these files alone does not perform them.

## Start a new project from it

1. Select **Use this template → Create a new repository**. Copy only the default
   branch. The new repository starts a separate history; future edits to the
   template are not automatically applied to it.
2. Clone the new repository.
3. Rename `project-name` in `pyproject.toml` and `project_name` in its wheel
   package path, `src/project_name/`, and `tests/test_installation.py`.
4. Replace the README title, purpose, and usage prompts. Update `docs/NEXT.md`.
   Choose a license and add a LICENSE file before public reuse.
5. Run `uv lock` after the metadata change, then `uv sync --locked` and
   `uv run --locked poe check`. Commit the renamed files and updated lockfile.
6. Review the GitHub settings described below.
7. Remove this file from the generated project when it is no longer useful.
   Keep it in the template repository.

There is no initialization script: the few edits are visible and reviewable,
and do not automatically commit, delete files, or alter GitHub settings.

## Settings to choose on GitHub

Repository files and repository settings are separate. Check these on every
new project; do not assume that enabling template mode copies them.

- Select a merge method and enable automatic deletion of merged branches.
  Squash merging is a useful default when an AI produces many small fix commits.
- For substantive work, use a PR as a self-review checkpoint. If you want that
  enforced, add a main-branch rule requiring PRs and the passing **Checks**
  status after the first CI run. Leave required approving reviews at zero for
  solo work: an author cannot approve their own PR. Availability of enforcement
  depends on repository visibility and your GitHub plan.
- If you enforce PRs for main, even prose fixes must use PRs unless an explicitly
  configured bypass applies. Do not make a bypass your everyday workflow.
- Enable useful security alerts and, for public projects, decide how private
  vulnerability reports should reach you. Add community policies when the
  project actually needs them.
- Configure any needed secrets, environments, Pages settings, and app access.
  The starter does not need secrets or deployment permissions to run checks.

## Improve the template gradually

Use it for one real project before adding more machinery. Promote a convention
back into this template when it has saved effort in practice. Bring worthwhile
updates into existing projects with a small, explicit commit; a template is not
a synchronized parent repository. Record the adopted template revision if you
later need to track propagation across many projects.

For a non-Python project, retain the documentation and review pattern, then
replace the Python files and CI commands with the stack's actual tools.

Official guides:

- https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-template-repository
- https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template
- https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/approving-a-pull-request-with-required-reviews
