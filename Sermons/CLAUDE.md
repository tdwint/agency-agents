# Project Context

## What I Am Building
A full sermon processing pipeline that takes YouTube/web sermon URLs, transcribes them, and extracts structured content: outlines, scripture references, key quotes, application points, and discussion questions. The output is a comprehensive sermon study guide that congregation members can use for personal study and small group discussion.

## Who It Is For
Congregation members at a non-denominational church who want to revisit and dig deeper into sermons throughout the week. This is a chapel in the woods, open air, very informal. The people who attend are for the most part believers but they might range from new believers to mature Christians, so output must be accessible without dumbing down the content. There are occassional skeptics who attendThey may not have seminary training or familiarity with theological jargon.

## What Success Looks Like
- Every sermon URL produces a complete, structured study guide within a single run
- Scripture references are accurate, linked to CSB translation, and include full verse text
- The outline faithfully represents the pastor's actual structure — not a reinterpretation
- A first-time visitor could read the output and understand every point without insider knowledge
- Discussion questions are open-ended and personal, not trivia about the sermon


# Architecture Constraints

## Output Format
- Markdown files (`.md`)
- File naming: `YYYY-MM-DD-sermon-title-slug.md`
- Each output file includes: metadata header, sermon outline, scripture list, key quotes, application points, discussion questions

## File Structure

```
/Sermons/
  CLAUDE.md              - This file
  /skills/               - Skill instruction files (extraction prompts, processing steps)
  /outputs/              - Generated sermon study guides and 20 minute version of the sermon
  /references/           - Style guide, example outputs, church branding notes
  /test-data/            - Sample sermon URLs, raw transcripts for testing
```

## Do NOT Build
- Do not generate original theological commentary or doctrinal positions
- Do not add points the pastor did not make — extraction only, not expansion
- Do not create children's or youth versions of the content
- Do not build audio/video editing or media production tools
- Do not summarize in a way that replaces watching/listening to the sermon
- Do not correct or critique the pastor's theology
- Do not generate social media posts or marketing content
- Do not build a web app, API, or database — this is a file-based pipeline


# Voice and Quality Rules

## Brand Voice
- Warm, clear, and inviting — like a trusted friend explaining what the pastor said
- Confident but not preachy — present the content, don't re-deliver the sermon
- Use short sentences and everyday language — if a word has a simpler synonym, use it
- Inclusive tone — assume the reader might be brand new to church
- Do this: "This passage reminds us that generosity starts with gratitude"
- Not this: "The exegetical framework of this pericope underscores stewardship theology"
- Write in a plain, direct, conversational tone — the way a thoughtful man talks to a peer he respects.
- Use short declarative sentences mixed with longer ones that connect naturally with "and."
- Drop straight into the situation with no preamble.
- Anchor abstract ideas in specific, concrete details.
- Use fragments for emphasis.
- End sections with a single short punchy line.
- No flowery language, no hedging, no passive voice, no words chosen to impress.
- Personality shows up in dry understatement, not wit

## Domain Language
- "fellowship" = community, doing life together
- "stewardship" = generosity and financial responsibility
- "lost" = not yet connected to faith (never use "lost" to describe people)
- "sanctification" = growing in faith, becoming more like Jesus
- "justification" = being made right with God
- "the Word" = the Bible, Scripture
- "quiet time" = personal Bible reading and prayer
- "conviction" = a sense that God is prompting change (not guilt or punishment)
- "body of Christ" = the church community (clarify on first use)
- "means of grace" = practices that help us grow — prayer, Scripture, community
- "exegesis" = studying what a Bible passage actually says in context

## Tone Rules
- Never condescending — assume the reader is intelligent but may be unfamiliar
- Never guilt-inducing — application points should inspire, not shame
- Stay faithful to the pastor's words — do not editorialize or add spin
- When the pastor uses humor, note it briefly but do not try to recreate the joke
- Use second person ("you") for application points, not third person ("one should")

## Quality Checks
- [ ] Every scripture reference includes book, chapter, and verse (e.g., John 3:16 CSB)
- [ ] The outline matches the pastor's actual sermon structure (not a generic reformat)
- [ ] No theological jargon appears without a plain-language explanation
- [ ] Discussion questions are open-ended (cannot be answered yes/no)
- [ ] Key quotes are verbatim from the sermon, in quotation marks
- [ ] Application points are specific and actionable, not vague ("pray more")
- [ ] The file follows the naming convention: `YYYY-MM-DD-sermon-title-slug.md`
- [ ] Metadata header includes: date, speaker, series name (if applicable), scripture passage


# Reference Files

## Brand Guide
`/Sermons/references/style-guide.md` — voice and formatting standards

## Templates
`/Sermons/references/sermon-template.md` — output template for study guides

## Example Outputs
`/Sermons/references/example-output.md` — example of a completed sermon study guide

## Source Data
`/Sermons/test-data/` — sample sermon URLs and transcripts for testing
