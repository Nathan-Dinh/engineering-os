# Quality-attribute prioritization

Run a focused Quality Attribute Workshop before consequential architecture choices. Do not assume every attribute matters equally, and do not score attributes just to produce numbers.

## Candidates

Performance, scalability, availability, reliability, security, privacy, maintainability, modifiability, testability, usability, accessibility, interoperability, observability, deployability, portability, and cost efficiency. Add or omit attributes to fit the project.

## Elicit and rank

Ask a few related questions at a time about user impact, operational expectations, threat and data boundaries, team capacity, growth, and cost. Follow up only where an answer changes the architecture or a trade-off. Have the user rank the most consequential attributes or compare them in pairs. Use numeric weights only when the user supplies meaningful relative values.

Record in `docs/architecture/quality-attributes.md` (template `quality-scenarios.md`): the method, participants or source, date, limitations, top drivers, secondary attributes, non-negotiable constraints, accepted trade-offs, and unresolved priorities. Revisit priorities when evidence or requirements change.

## Scenarios

For each high-priority attribute, capture source of stimulus, stimulus, environment, artifact, response, and response measure, with a `QA-####` ID. Make measures observable (for example, a latency percentile under an agreed load). Targets come from project evidence or explicit user acceptance; leave an unknown measure unresolved rather than inventing a threshold. Link scenarios to requirements, decisions, and verification. A scenario is verified only after an appropriate check has run and its scope and result are recorded.
