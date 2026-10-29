# NERV skill set

Agent skills that set up and look after bioinformatics sequencing projects. Names borrow from Neon Genesis Evangelion, and each one is paired with a plain description of what it does, so someone who has never seen the show can still tell what a term means. Some terms also have a _Codename_: an Evangelion nickname for informal use in conversation and docs. The plain term is the one code and specs use.

## Language

### The skill set

**NERV**:
The skill set as a whole: the organization that sets up a sequencing project and keeps it in order.
_Avoid_: toolkit, framework, plugin

**Generated project**:
A bioinformatics project directory created by `nerv-init`, as opposed to this repository, which holds the skills.
_Avoid_: target project, output project, user project
_Codename_: Unit (each project is an Eva unit that NERV builds and launches)

### Setting up a project (`nerv-init`)

**Interview**:
The short set of questions asked before anything is created: assay, workflow engine, language, compute, and data sensitivity.
_Avoid_: wizard, questionnaire, prompt

**Skeleton**:
The folder layout every generated project gets, whatever the assay.
_Avoid_: template, scaffold, boilerplate
_Codename_: GeoFront (the underground structure every NERV base is built inside)

**Add-on**:
A layer of assay-specific or engine-specific content placed on top of the skeleton. It holds only what differs from the skeleton.
_Avoid_: plugin, preset, variant, flavor

**AGENTS.md**:
The short entry document an agent always reads first. It holds the hard rules, the run and test commands, and pointers to deeper documents, not the detail itself.
_Avoid_: project instructions, rules file

**Folder README**:
A README in each main folder with four sections: Purpose, Conventions, Current state, and Last major change. It gives an agent working in that folder its local context.
_Avoid_: folder doc, local doc, sub-README

**Hard rule**:
A short, non-negotiable rule listed in AGENTS.md, such as never modifying raw data in place. Hard rules are enforced where the tools allow.
_Avoid_: guardrail, constraint, policy

**Principle**:
A flexible best-practice guideline, such as KISS or Fail Fast. Principles shape the skills and templates but are not listed one by one in AGENTS.md.
_Avoid_: soft rule, convention, best practice

**Next steps**:
The follow-up actions the scaffold reports to the user after it creates a project, such as trusting the Codex hooks. The list lives in one place, `NEXT_STEPS` in `scaffold.py`, and the agent shows it in full.
_Avoid_: todo list, checklist, post-install steps

### Keeping documents current (`sync-ratio`)

**Sync ratio**:
How closely a folder's README matches what is currently in that folder. The name comes from the Evangelion measure of how well a pilot and an Eva move as one.
_Avoid_: freshness, doc coverage, staleness

**Major change**:
A change to a folder large enough that its README is expected to be updated: a file added or removed, or a big edit.
_Avoid_: significant change, big diff

**Out of sync**:
A folder with a major change whose README was not updated alongside it.
_Avoid_: stale, outdated, drifted
_Codename_: Angel (an out-of-sync folder is the threat the sync reminder reports)

**Sync reminder**:
The single message telling an agent which folders are out of sync. It reminds and never blocks, and it is shown once per unchanged state.
_Avoid_: nudge, warning, alert

### Reviewing a change (`magi-review`)

**MAGI**:
The three-seat review panel for critical changes. Named for the three supercomputers in Evangelion that decide by majority vote.
_Avoid_: review board, committee, council

**Seat**:
One of the three independent reviewers on the MAGI: MELCHIOR-1, BALTHASAR-2, or CASPER-3. Each seat judges the whole change through its own lens.
_Avoid_: reviewer, judge, agent

**Lens**:
A viewpoint a change is judged through: science (is it valid), safety (is it safe), or craft (is it well made). MELCHIOR-1 takes the science lens, BALTHASAR-2 safety, and CASPER-3 craft.
_Avoid_: aspect, dimension, perspective

**Review level**:
How deeply a change is reviewed, set by what it touches and how large it is: TRIVIAL (no review), STANDARD (one reviewer, three lenses), or CRITICAL (the full MAGI).
_Avoid_: tier, severity, risk class

**Vote**:
A seat's verdict on a change: APPROVE, CONDITIONAL (approve if its required fixes are applied), or REJECT.
_Avoid_: ballot, score, rating

**Veto**:
A REJECT from BALTHASAR-2 that cites a hard rule, which makes the outcome REJECT whatever the other votes are.
_Avoid_: override, block

**Escalation**:
Moving a review from STANDARD to CRITICAL because the first reviewer found a Blocker or a hard-rule violation. A review level can be raised but never lowered.
_Avoid_: upgrade, promotion

**Brief**:
The context given to a reviewer: the diff range, the stated requirements, and the hard rules. It never includes the authoring session's history.
_Avoid_: prompt, context pack

**Finding**:
One problem a reviewer reports, tagged Blocker (must fix before merging), Fix (should fix), Nit (minor), or Pre-existing (not introduced by this change).
_Avoid_: issue, comment, defect

### Protecting data

**Raw data**:
The original, untouched files under `data/raw/`, kept exactly as received.
_Avoid_: input data, source data, original files

**Provenance record**:
The entry in `data/README.md` giving where a raw file came from and its checksum.
_Avoid_: metadata, data log, manifest

**Raw-data guard**:
The hook that lets agents add new raw files but requires a person's approval to change or delete an existing one, and reports raw files changed some other way after the fact. It is a best-effort safeguard, not a security boundary.
_Avoid_: lock, firewall, protection
_Codename_: AT Field (the barrier around raw data; strong, but not absolute)

**Raw snapshot**:
The raw-data guard's saved record of each raw file's size and modification time. Comparing raw data with it shows which raw files are new, modified, or removed since the last check.
_Avoid_: manifest, checksum list, index, baseline
