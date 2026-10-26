# UX principles

Use these to find and explain design problems, not to prove a design works. A principle is a basis for an inferred claim; usability is verified only by testing with users or by a check that ran. Accessibility requirements and the project's established design system take precedence over any principle here. Apply the ones a decision actually depends on, and name the principle behind a consequential choice in the design notes.

## Usability and cognitive psychology

| Principle | What it means | Apply it as |
|---|---|---|
| Aesthetic-usability effect | Attractive interfaces are perceived as easier to use. | Polish matters, but in reviews and tests, look past praise for the look to whether tasks succeed. |
| Paradox of the active user | People start using a product instead of reading instructions. | Make the first use work without docs or tours: sensible defaults, inline hints, safe undo. |
| Progressive disclosure | Reveal features gradually to reduce overload. | Show what most users need first; put advanced options behind a clearly labeled entry. Never hide something needed often. |
| Recognition rather than recall | Visible options beat remembered ones. | Label icons, show recent and available choices, and carry context across steps instead of asking users to remember it. |
| Von Restorff effect | A distinctive item is noticed and remembered. | Make the one primary action per view stand out. If everything is emphasized, nothing is. Don't rely on color alone. |
| Peak-end rule | Experiences are judged by their most intense moment and their end. | Design the hardest moment (errors, waits, payment) and the completion state with care; end with a clear confirmation and next step. |
| Goal-gradient effect | Motivation rises near the goal. | Show progress in multi-step flows, and count steps already done. |
| Tesler's law | Some complexity can't be removed, only moved. | Decide who carries it; move it to the system, not the user, wherever possible. Record where it went. |
| Postel's law | Accept input flexibly, respond predictably. | Accept common formats (spaces in card numbers, pasted dates) and normalize them; format output consistently. Flexible input never relaxes validation or security. |
| Occam's razor | Prefer the simplest adequate solution. | Use the fewest screens, steps, and elements that meet the requirements. |
| Feedback loops | Respond clearly and promptly to every action. | Acknowledge each action, show state changes, and make errors say what happened and how to fix it. |

## Interaction and interface design

| Principle | What it means | Apply it as |
|---|---|---|
| Hick's law | Decision time grows with the number and complexity of choices. | Cut or group options, and mark a recommended default where one exists. |
| Fitts's law | Time to reach a target depends on its size and distance. | Make frequent and primary targets large and close to where attention is; keep destructive actions away from frequent ones. Meet the minimum target size (WCAG 2.2: 24×24 CSS px at level AA). |
| Jakob's law | Users expect your product to work like the ones they already know. | Follow platform and existing product conventions; record the reason for any deviation. |
| Miller's law | Working memory is limited. | Chunk information into small, labeled groups. Don't treat "seven plus or minus two" as a hard limit on menu length. |
| Doherty threshold | Responses under about 400 ms keep people engaged. | Respond within that, or show immediate feedback and progress (skeletons, optimistic updates) when work takes longer. |
| Serial position effect | First and last items are remembered best. | Put the most important items at the start and end of navigation and lists, not in the middle. |
| Law of Prägnanz | People see complex arrangements in their simplest form. | Prefer simple, regular layouts and shapes; remove visual noise that suggests structure that isn't there. |
| Law of similarity | Things that look alike seem to belong together. | Give the same look to the same behavior; never style static content like a control. |
| Law of common region | Things inside one boundary seem related. | Group related controls and content in a shared container (card, fieldset, section). |
| Visual hierarchy | Arrangement guides attention by importance. | Order by size, weight, contrast, and position; one clear primary element per view; visual headings match the semantic heading structure. |
