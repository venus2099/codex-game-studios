### Creative decisions are always the user's

`project.yaml` sets `modes.automation: guided` and lists four creative
categories in `modes.automation_always_ask`. Upstream only consults that list
in autonomous mode; in this project it applies in **every** mode. Treat any
decision in these categories as **major**: present options with your
recommendation, ask in chat, and wait. Never "recommend and proceed", and never
pick-and-log.

| Category | Covers |
|---|---|
| `art_and_visuals` | art style and art bible, character/creature/environment look, color palette, UI visual style, VFX look, concept and asset specs |
| `story_and_narrative` | plot, characters and their arcs, world and lore, factions, quests, endings, tone |
| `player_facing_text` | dialogue, barks, item/skill/quest descriptions, UI copy, tutorials, store page and marketing copy, patch notes for players |
| `music_and_audio` | music direction and tracks, sound palette and SFX style, voice casting and VO direction, audio mix intent |

This includes decisions made by subagents: a subagent returns these as
questions instead of deciding. Technical work around creative content (file
formats, import settings, wiring an approved line or sound into the game)
follows the normal guided rules.
