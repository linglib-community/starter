# linglib starter

A starting point for formal linguistics with [linglib](https://github.com/linglib-community/linglib), a
Lean 4 library that checks whether theories make the predictions their authors claim.

You do not need to install Lean yourself or know how to program. An AI agent installs
everything, writes most of the Lean, and explains what it did. Your job is the part that needs a
linguist: checking that each formal statement says what the paper says.

There are three ways to start. The first is the easiest for most people.

## Option 1: in the AI chat app you already use

This works with any AI app that can run commands in a workspace with internet access, not just
answer in text. The Claude app (on desktop or the web) can do this. Other apps may too; check
that yours can install software and run commands before relying on it. Agent features usually
need a paid plan, and long sessions use credits.

1. Recommended: make your own copy of this project, so your work is saved somewhere permanent.
   On GitHub, click "Use this template", then "Create a new repository" (a free GitHub account is
   enough). If your app can connect to GitHub, connect it.
2. Start a new chat and give it this prompt, using the address of your copy if you made one:

   > Set up the linglib starter: clone https://github.com/linglib-community/starter, read
   > AGENTS.md, and follow its setup instructions. Then walk me through the worked example.

3. The agent tells you what it will install and asks you to confirm. Setup takes about 10
   minutes on a fast connection, and up to 30 on a slow one. Then it explains the worked example and suggests what to try next.

Saving your work: at the end of a session, ask the agent to save it. It can push your changes to
your copy on GitHub, save the files to a folder on your computer if your app is connected to one,
or give you a file to download. A new chat may start with a fresh workspace, in which case setup
runs again.

## Option 2: on your own computer, with an AI agent

Use this if you want everything to stay on your machine. You need:

- An AI agent that can edit files and run commands on your computer, such as the Claude app
  connected to a folder, Claude Code, OpenAI's Codex, or Cursor.
- About 15 GB of free disk space, and a network connection that allows access to `github.com` and
  `cache.mathlib.org`.
- macOS or Linux works best. Windows works through WSL or with a few manual steps.

Give your agent this prompt:

> Clone https://github.com/linglib-community/starter into a new folder called my-linglib, then
> read AGENTS.md in that folder and follow its setup instructions.

Setup takes about 10 minutes on a fast connection, and up to 30 on a slow one, mostly
downloading. To keep your work on GitHub as well as your computer, make your own copy first
("Use this template", as in Option 1) and give the agent its address instead.

## Option 3: in a code editor in your browser

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/linglib-community/starter?quickstart=1)

This opens a full code editor in your browser with everything already set up, and the Claude
Code panel in the sidebar. It suits workshops, where everyone needs the same environment, and
people who are comfortable with code editors.

- Codespaces are paid for by your GitHub account, which includes a free monthly allowance, or by
  the linglib-community organization for its members. This project uses about 12 GB of storage,
  so stop the codespace when you finish a session and delete it from github.com/codespaces when
  you no longer need it.
- Claude Code requires a paid Claude plan.

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
- `scripts/setup.sh`: the setup steps, which the agent (or the codespace) runs for you.
- `.devcontainer/`: the configuration for Option 1.
- `lakefile.toml` and `lean-toolchain`: which versions of linglib and Lean this project uses.
