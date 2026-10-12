# Instructions for AI agents in this project

This is a starter project for formal linguistics with [linglib](https://github.com/linglib-community/linglib),
a Lean 4 library. You (the agent) install everything and do most of the Lean work. The person
you are working with checks that the formal statements say what the linguistics says.

## Who you are working with

Assume the user is a linguist, not a programmer. In practice:

- Explain what you are doing in plain language. Do not paste build logs or long command output
  unless they ask. Summarize instead.
- Ask before installing anything not covered by the setup below, before using `sudo`, and before
  any step that will take more than a few minutes beyond what is listed here.
- Use linguistic terms freely and Lean terms sparingly. When you mention a Lean concept, say in a
  sentence what it means.
- They care about attribution and about whether a formalization is faithful to its source. Treat
  those as first-class concerns, not afterthoughts.

## First-time setup

Setup is complete when `.lake/build/lib/lean/MyProject/Example.olean` exists. If it does not,
and the user has asked you to set up the project, do the following.

1. Tell the user, in two or three sentences, what will happen: you will install Lean (into
   `~/.elan`, no administrator rights needed), download linglib and the prebuilt Mathlib library,
   and build a worked example. It needs about 15 GB of disk space and takes about 10 minutes on a
   fast connection, and up to 30 on a slow one, mostly downloading. Ask for their go-ahead once.
2. Run `bash scripts/setup.sh` from the project root. It prints one line per step and writes full
   logs to `.lake/setup-logs/`. Let it run. Steps 1 to 3 take about a minute; steps 4 and 5
   are the slow ones. Give the user a short update when step 4 finishes and when step 5 finishes.
3. If it ends with `SETUP OK`, go to "After setup" below.
4. If it ends with `SETUP FAILED`, read the log it names and use the table below. Fix the cause,
   then run the script again; it skips finished steps.

| Symptom in the log | What to do |
|---|---|
| `lake: command not found` after elan installed | Use `~/.elan/bin/lake`, or run `source ~/.elan/env` first. Tell the user a new terminal will pick it up automatically. |
| Disk space error | Tell the user how much is free and that about 15 GB is needed. Do not delete anything to make room without asking. |
| Network errors in step 4 (timeouts, TLS, 403) | Retry once. If it fails again, tell the user the setup needs access to `github.com` and `cache.mathlib.org`, which some university or company networks block. Suggest trying another network. |
| Step 4 reports that cache files are missing, or Lean starts compiling Mathlib files | Stop the build. Do not let it compile Mathlib from source: that takes hours. Report the problem to the user and suggest they open an issue on linglib. |
| A toolchain or version mismatch error | Do not edit `lean-toolchain` or the linglib version in `lakefile.toml` to make the error go away. These must match linglib's. Report the exact error to the user. |
| `building from source; failed to fetch GitHub release` in step 5 | Lake could not download linglib's prebuilt files, so it is compiling the parts it needs instead. This is slower (a few minutes) but works. If it happens on every run, check that `rev` in `lakefile.toml` is a release tag. |
| Warnings (not errors) in the logs, for example from elan's self-update check or linter warnings in linglib files | Ignore them. Only errors, or a `SETUP FAILED` line, need attention. |
| An error in a linglib file during step 5 | This is a problem in linglib, not in the user's setup. Report it with the file name and error, and suggest opening an issue on linglib. |

### In a cloud workspace driven from a chat app

If you are working in a cloud workspace that the user reaches through a chat app (for example the
Claude app), rather than on their own computer, the following applies. If you are not sure which
situation you are in, ask the user once whether you are working on their own computer.


- The workspace may not last beyond this conversation. Early on, tell the user how their work
  will be saved, and at the end of each session save it before they leave: push to their own
  copy of the starter on GitHub if they have one and you can reach it; otherwise save to a folder
  on their computer if the app is connected to one, or give them the changed files to download.
  Never let a session end with unsaved work without saying so.
- If the app can show a web page or rendered document in the chat, show results that way (for
  example the worked example's scoreboard as a table of accounts by conditions) rather than
  asking the user to read Lean files.
- If setup fails because the workspace cannot reach `cache.mathlib.org` or has too little disk
  space, say so plainly. These are limits of the workspace, not problems the user can fix.

### In GitHub Codespaces

If the environment variable `CODESPACES` is `true`, setup ran automatically when the codespace
was created, so there is nothing to install. If `.lake/build/lib/lean/MyProject/Example.olean` is
missing, setup may still be running or may have failed: check `.lake/setup-logs/`, and tell the
user they can also see progress with the command "Codespaces: View Creation Log". If it failed,
run `bash scripts/setup.sh` and continue as above.

Codespaces use the user's free monthly allowance, and this one takes about 12 GB of storage.
Remind the user to stop the codespace when they finish a session, and to delete it from
github.com/codespaces once they no longer need it (after committing anything they want to keep).

### Windows

`scripts/setup.sh` needs a Unix shell. On Windows, prefer WSL if it is installed. Otherwise, do the
same steps by hand in PowerShell: install elan with the Windows installer from
https://github.com/leanprover/elan, then run `lake --version`, `lake exe cache get` and
`lake build MyProject.Example` from the project root. The table above still applies.

## After setup

Show the user the worked example in `MyProject/Example.lean`, briefly and in plain language:

- It uses data from Chemla & Schlenker (2012), whose experiments tested whether sentences with
  *too* license the conditional or the unconditional presupposition, in canonical and inverse
  orders.
- linglib registers eleven accounts of presupposition projection and scores each one on each
  experimental condition: correct, wrong, or silent.
- The result Lean has checked: the incremental accounts are wrong on the inverse-order
  sentences, and the symmetric accounts and Limited Symmetry are right on every tested condition.
- Lean checked the derivations. Whether the definitions capture each theory faithfully is
  something a person has to judge. Point them to the definitions if they want to look:
  - The eleven accounts: `.lake/packages/linglib/Eval/Projection/Account.lean`.
  - The scoring, including which accounts count as incremental (`incremental`):
    `.lake/packages/linglib/Eval/Projection/ChemlaSchlenker2012.lean`.
  - Limited Symmetry: `.lake/packages/linglib/Linglib/Studies/Kalomoiros2023.lean`.

Then offer two or three things to try next, for example:

- "Show me how linglib defines Limited Symmetry, next to how Kalomoiros states it."
- "Which accounts make the same predictions on these sentences, and why?"
- "Help me formalize one claim from a paper I know." (Use `MyProject/MyFirstStudy.lean`.)

## Working in this project

### Where things are

- The user's own work goes in `MyProject/`. Add new files there and import them in
  `MyProject.lean`.
- linglib's source is in `.lake/packages/linglib/`. Read it freely; never edit it.
  - `Linglib/Studies/` has one file per formalized paper, named by author and year.
  - `Linglib/Semantics/`, `Linglib/Pragmatics/`, `Linglib/Syntax/` and so on hold the theories.
  - `Linglib/Data/` and `Linglib/Phenomena/` hold empirical data.
  - `Eval/` scores theories against data.
- Search with `grep -rn` inside `.lake/packages/linglib/` before writing a definition yourself.
  If linglib already has it, use it. API documentation is at https://linglib.io.

### Building

- `lake` lives in `~/.elan/bin`. Setup adds it to the user's shell profile, but a shell you
  start may not read that file. If `lake` is not found, run
  `export PATH="$HOME/.elan/bin:$PATH"` first, or call `~/.elan/bin/lake` directly.
- Check one file at a time: `lake env lean MyProject/<File>.lean`, or
  `lake build MyProject.<File>`. Avoid building all of linglib; it is large and almost never
  needed.
- After a change, rebuild before you tell the user something works.
- The first build of a file that imports a new part of linglib can take several minutes,
  because that part of linglib is compiled then. Tell the user when this happens.

### Formalizing a claim

For each claim you formalize, keep three things together in the file, as in
`MyProject/MyFirstStudy.lean`:

1. The source: author, year, page, and the exact passage, quoted.
2. The claim in plain words.
3. The Lean statement and proof.

Rules:

- When you report a result, show (2) and the Lean statement side by side, and say plainly what
  Lean checked (that the proof is valid) and what it did not (that the statement matches the
  paper).
- Never write `Status: checked by` yourself. Only the user marks a claim as checked.
- If a proof does not go through, never weaken or alter the statement to make it pass without
  telling the user. A failed proof may mean the paper's claim does not follow from its
  definitions, which is a finding. Say which it is: the claim is false (show a counterexample if
  you have one), the definitions need adjusting, or you could not find a proof.
- Do not leave `sorry` in a file without telling the user where and why.

### Cost

Long sessions with an AI agent can use a lot of credits. Before a large task, such as formalizing
a whole paper, say roughly how big it is and check that the user wants to go ahead.

## Updating linglib

linglib is pinned to a release tag in `lakefile.toml` (`rev = "v4.34.1"`, for example), and the
Lean version in `lean-toolchain` must match the one in linglib's own `lean-toolchain` at that tag.
Each release comes with prebuilt files, which Lake downloads instead of compiling linglib.

To update, which you should do only when the user asks:

1. Pick a newer release from https://github.com/linglib-community/linglib/releases. Use a
   release tag, not a branch or commit: only releases have prebuilt files.
2. Set `rev` in `lakefile.toml` to that tag, and copy linglib's `lean-toolchain` from that tag
   if it changed.
3. Run `lake update`, then `lake build MyProject.Example`, and check that the user's own files
   still build. Tell the user if a change in linglib broke any of their files.

## Saving work to GitHub

If the project was cloned from `linglib-community/starter` directly, its `origin` is the shared
starter, which the user cannot push to. If they want their work on GitHub, help them create their
own copy ("Use this template" on the starter's GitHub page, or `gh repo create` if they use the
GitHub command line), then point `origin` at it with `git remote set-url origin <their copy>`
and push.

## Contributing back to linglib

When the user has a formalization they are happy with, and has checked its statements, offer to
help them contribute it to linglib as a study file (see linglib's `CONTRIBUTING.md`). That way
others can build on it and it is checked against the rest of the library.
