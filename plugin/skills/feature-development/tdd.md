# Choosing verification and test-first

Choose a verification method that matches the observable behavior and the risk. Use Red-Green-Refactor when it fits:

1. Define an acceptance criterion or observable contract.
2. Add a focused test that fails for the missing behavior (red).
3. Make the smallest change that passes it (green).
4. Refactor while keeping the behavior.
5. Run focused and relevant regression checks, and record the exact results.

Pick among unit, integration, contract, end-to-end, performance, security, migration, accessibility, and exploratory checks. Use the lowest level that gives real confidence, and add broader checks where boundaries or risks need them. Do not force unit-level test-first onto exploratory UI design, infrastructure provisioning, or work where another method fits better.

For each check, note the requirement or quality scenario it covers, the command or method, the environment, the result, and its limits. A passing test proves only the behavior in its scope. It does not show production status, general security, or untested requirements.
