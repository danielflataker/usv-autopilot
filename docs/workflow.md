# Development workflow

The project uses an issue-and-branch workflow so that the history on `main` stays easy to follow.

## Issues

Use GitHub issues for concrete work that is worth tracking.

Use area labels to show which part of the system an issue belongs to:

- `area: hardware`
- `area: estimation`
- `area: control`
- `area: guidance`

Use type labels only when they add useful information:

- `type: bug`
- `type: feature`

Not every issue needs a type label. Add new labels only when there is a recurring need for them.

Group related issues under milestones such as **Hardware bring-up**, **Heading control** and **Waypoint guidance**.

## Branches

Create a short-lived branch for each issue:

```text
<owner>/<short-description>
```

Examples:

```text
daniel/bmi270-spi
olav/esc-output
daniel/heading-hold
```

The prefix identifies who owns the branch history. The owner may rebase or force-push the branch; anyone else should coordinate before pushing to it.

The issue itself carries the area, milestone and detailed context.

## Commit messages

Use a short scope prefix when it helps make the history easier to scan:

```text
hardware: document esc pwm range
estimation: add gyro bias estimate
control: add heading controller
guidance: add waypoint acceptance
analysis: plot heading-hold test
docs: update project roadmap
```

Keep commit subjects short, imperative and lower-case. Use a small, stable set of scopes rather than inventing a new prefix for every change.

Pull request titles can use normal sentence casing, for example:

```text
Control: Add heading controller
```

The exact casing is less important than keeping the convention simple and consistent.

## Pull requests

Changes to `main` go through a pull request.

Keep the PR focused on one engineering result and link the issue in the description, for example:

```text
Closes #17
```

Clean up temporary fixup commits before merge. Rebase onto the current `main` when needed, then use rebase merge by default. Squash merge is fine when the branch history is only useful as temporary working history.

Merge commits are not used on `main`.

## Tests

Keep tests small and focused on behaviour that is easy to break and useful to verify.

A few clear tests are preferred over a large test suite that is difficult to understand or maintain. Avoid testing trivial implementation details or duplicating the implementation inside the tests. Hardware-dependent behaviour should still be checked on the real hardware when practical.

Add CI when there are useful host-side tests or analysis checks worth running automatically.

## Releases and tags

Git tags are reserved for meaningful project snapshots or demonstrations later on. Routine tasks and features are tracked with issues and labels instead.
