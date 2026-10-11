# linglib starter

A starting point for formal linguistics with [linglib](https://github.com/linglib-community/linglib), a
Lean 4 library that checks whether theories make the predictions their authors claim.

You do not need to install Lean yourself or know how to program. An AI agent installs
everything, writes most of the Lean, and explains what it did. Your job is the part that needs a
linguist: checking that each formal statement says what the paper says.

## What you need

- An AI coding agent that runs on your own computer and can edit files and run commands, such as
  Claude Code or OpenAI's Codex. A chat window in a web browser is not enough. These agents
  usually need a paid plan, and long sessions use credits.
- About 15 GB of free disk space, and a network connection that allows access to `github.com` and
  `cache.mathlib.org`.
- macOS or Linux works best. Windows works through WSL or with a few manual steps.

## Getting started

Open your agent in the folder where you keep projects, and give it this prompt:

> Clone https://github.com/linglib-community/starter into a new folder called my-linglib, then
> read AGENTS.md in that folder and follow its setup instructions.

The agent will tell you what it is about to install and ask you to confirm. Setup takes about
10 to 30 minutes depending on your connection, mostly downloading. When it is done, the agent will walk you through a worked
example.

## What you should see at the end

The worked example, `MyProject/Example.lean`, uses the experiments in Chemla & Schlenker (2012)
on presupposition projection. linglib scores eleven accounts of projection against those results
and proves the outcome: the incremental accounts are wrong on the inverse-order sentences, and the
symmetric accounts and Limited Symmetry are right on every tested condition.

Good first things to ask your agent:

- "Show me how linglib defines Limited Symmetry, next to how Kalomoiros states it."
- "Which accounts make the same predictions on these sentences, and why?"
- "Help me formalize one claim from a paper I know."

## What Lean checks, and what it does not

Lean checks that every proof is valid. It does not check that a formal definition captures what
an author meant. An agent can write a statement that compiles but misrepresents a theory. Each
formalized claim in this project keeps its source passage, a plain-language version and the Lean
statement together, so you can compare them. Only you should mark a claim as checked.

## Setting up without an agent

If you are comfortable with a terminal, run `bash scripts/setup.sh` from this folder.

## Files

- `AGENTS.md`: instructions the agent reads (`CLAUDE.md` points to it).
- `MyProject/`: your work. `Example.lean` is the worked example; `MyFirstStudy.lean` is a
  template for formalizing a claim.
- `scripts/setup.sh`: the setup steps, which the agent runs for you.
- `lakefile.toml` and `lean-toolchain`: which versions of linglib and Lean this project uses.
