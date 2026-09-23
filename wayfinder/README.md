# Wayfinder tracker (GitHub Issues)

This repo's issue tracker is **GitHub Issues** on `mbarnfield63/MARVEL_db`. This
doc is the "Wayfinding operations" reference future sessions should consult.

## Wayfinding operations

- **Map** = an issue labelled `wayfinder:map`.
- **Ticket** = an issue labelled `wayfinder:research`, `wayfinder:prototype`,
  `wayfinder:grilling`, or `wayfinder:task`, linked as a **native GitHub
  sub-issue** of its map.
- **Claim** a ticket = `gh issue edit <n> --add-assignee @me`.
- **Blocking** = GitHub's native issue-dependency relation (`blocked by` /
  `blocking`), visible in the issue sidebar. Query/set via REST:
  `gh api repos/mbarnfield63/MARVEL_db/issues/<n>/dependencies/blocked_by`.
- **Unblocked** = zero open issues in that dependency list.
- **Frontier** = open, unassigned, unblocked sub-issues of a map:
  `gh issue list --repo mbarnfield63/MARVEL_db --json number,title,assignees,labels`,
  cross-referenced against each issue's `issue_dependencies_summary`.
- **Resolve** a ticket = comment the answer, `gh issue close <n>`, then append a
  one-line entry to the map issue's `## Decisions so far` section
  (`gh issue edit <map-n> --body ...`).
- `/research` and `/domain-modeling` skills are not installed in this
  environment — substitute a general-purpose/Explore agent (research tickets)
  and `/grilling` alone (domain-modeling tickets).

## Current maps

- [MARVEL run database — POC scaffold](https://github.com/mbarnfield63/MARVEL_db/issues/1) — destination reached, no open frontier.
- [db_MARVEL public API — architecture decisions](https://github.com/mbarnfield63/MARVEL_db/issues/18) — destination reached 2026-09-22. Built in `api/` (commit 4145890).
- [MARVEL-online website — architecture decisions](https://github.com/mbarnfield63/MARVEL_db/issues/9) — destination reached 2026-09-23. Built as the separate repo [MARVELdb_online](https://github.com/mbarnfield63/MARVELdb_online); not live until the API has a public host.
