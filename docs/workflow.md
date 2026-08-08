# Development workflow

The project uses an issue-and-branch workflow so that the history on `main` stays easy to follow.

## Milestones

Use milestones for the major working stages of the project. They may be planned further ahead than individual issues, but should describe outcomes rather than detailed implementation tasks.

Create detailed issues only as a milestone approaches. Avoid due dates unless they become genuinely useful.

When a milestone is completed and verified, its release point is tagged on `main` as described below.

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

Assign issues to the milestone they help complete.

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

The issue itself carries the area, milestone and detailed context. Work on a future milestone may start on its own branch, but it is normally not merged to `main` until the current milestone has reached its stable release point.

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

Changes to `main` go through a pull request. Keep `main` buildable and reasonably stable so it remains a useful integration baseline.

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

Each completed milestone marks a stable project snapshot. After the milestone has been verified, tag the corresponding commit on `main` and create a short GitHub Release.

During development, milestone releases use the milestone number as the minor version:

```text
M1 -> v0.1.0
M2 -> v0.2.0
M3 -> v0.3.0
...
```

A final validated system may be tagged `v1.0.0`. Release notes should stay short and describe what was actually demonstrated or verified.

Tags are the stable recovery points: an older known-good firmware version can always be checked out and built directly from its tag. Published release tags are not moved or rewritten.

Release branches and release candidates are not used by default. Add them only if a concrete need for parallel maintenance or a separate validation phase appears later.
