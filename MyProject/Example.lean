import Eval.Projection.ChemlaSchlenker2012

/-!
# Worked example: scoring theories of presupposition projection

This file checks a few results that linglib has already proved about
Chemla & Schlenker (2012), "Incremental vs. symmetric accounts of presupposition
projection: an experimental approach" (Natural Language Semantics 20).

The experiments asked participants whether sentences such as conditionals and
disjunctions with *too* license the conditional presupposition ("if p, then q") or the
unconditional one ("q"). Each sentence came in a canonical order (the clause that
satisfies the presupposition comes first) and an inverse order (the trigger comes first).

linglib registers eleven accounts of projection, including Heim's dynamic semantics,
several versions of Schlenker's Transparency theory, and Kalomoiros's Limited Symmetry.
For each account and each experimental condition it derives the account's prediction
from the account's own definitions, compares it with the recorded result, and gives a
verdict: correct, wrong, or silent.

If this file builds without errors, every statement below has been checked by Lean.
What Lean does not check is whether the definitions say what the papers mean. That
step is for a person to verify.
-/

namespace MyProject.Example

open Eval.Projection Eval.Projection.ChemlaSchlenker2012
open _root_.ChemlaSchlenker2012 (Construction Order)

/-- Heim's dynamic account predicts the unconditional presupposition for the
inverse-order conditional, but participants preferred the conditional one.
So the verdict in Experiment 1 is "wrong". -/
example : verdict observed1 .dynamic .ifSentence .inverse = .wrong := by
  rw [(verdict_eq _ _ _).2]
  decide

/-- Kalomoiros's Limited Symmetry gets the same condition right. -/
example : verdict observed1 .limitedSymmetry .ifSentence .inverse = .correct := by
  rw [(verdict_eq _ _ _).2]
  decide

/-- The canonical-order *unless* sentence was not tested, so every account is
"silent" on it. -/
example (a : Account) : verdict observed1 a .unlessSentence .canonical = .silent := by
  rw [(verdict_eq _ _ _).2]
  simp

/-- The full scoreboard, proved in linglib: Experiments 1 and 4 give the same verdicts;
every incremental account is wrong on each inverse-order sentence and right on each
canonical one; every other account is right on all tested conditions. -/
example (a : Account) (k : Construction) (o : Order) :
    verdict observed1 a k o = verdict observed4 a k o ∧
      verdict observed1 a k o =
        if k = .unlessSentence ∧ o = .canonical then .silent
        else if a ∈ incremental ∧ o = .inverse then .wrong else .correct :=
  verdict_eq a k o

end MyProject.Example
