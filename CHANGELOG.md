# Changelog

## 0.1.5 - 2026-09-13

- Use a synchronized SkillKit state store with monotonic expiry and a 1,024-scope capacity.
- Handle malformed TTL settings and replace unrelated Danish/Basque/Thai commands with explicit mode requests.
- Include requirements.txt in the source distribution and verify native OVOS fallback routing.
- Run complete unit/native OVOS suites on Python 3.10, 3.12 and 3.14; verify built wheel and source-distribution resources in CI.
