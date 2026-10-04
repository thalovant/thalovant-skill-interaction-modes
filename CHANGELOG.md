# Changelog

## 0.1.9 (2026-10-04)

- Use SkillKit 0.24.2's cached command matching and explicit speaker/language replies.
- Require complete commands for mode changes; preserve contextual status questions.
- Reject anonymous framework identities instead of sharing a mode accidentally.
- Repair contradictory enable/disable translations and political-party mistranslations;
  regenerate common regional resources from the corrected sources.
- Exercise every packaged command and all 65 locales through native OVOS turns.
- Declare Python 3.10+ and license metadata; verify source archives and wheels.
- Build once for independent PyPI, GitHub, and marketplace publication.

## 0.1.8 (2026-09-26)

- Spell the French party-mode lines with their accents: "Le mode fête est
  activé", "désactivé", "Mode fête activé". Without them espeak-ng, which
  phonemises for the Thalovant voice, said "fəte" and "dəzaktiv". The
  regional French locales are regenerated from fr-FR.
- Requires thalovant-skillkit 0.22.0, which sends `utterance_ssml` and checks
  speech markup. Nothing here needs markup: every reply is one short status
  line, spoken through the kit's `speak`.

## 0.1.7 (2026-09-19)

- Complete 19 common regional resource sets using shared translations and explicit
  regional wording; keep existing regional translations.
- Use SkillKit 0.15 regional generation and freshness checks, with complete files
  for native OVOS and direct resource readers.
- Update resource and regional behavior tests and document translation provenance.


## 0.1.6 - 2026-09-19

- Use SkillKit 0.14 regional fallback for compatible language variants without duplicating translations. Preserve the requesting session language.
- Exercise regional requests through the native OVOS test harness.

## 0.1.5 - 2026-09-13

- Use a synchronized SkillKit state store with monotonic expiry and a 1,024-scope capacity.
- Handle malformed TTL settings and replace unrelated Danish/Basque/Thai commands with explicit mode requests.
- Include requirements.txt in the source distribution and verify native OVOS fallback routing.
- Run complete unit/native OVOS suites on Python 3.10, 3.12 and 3.14; verify built wheel and source-distribution resources in CI.
