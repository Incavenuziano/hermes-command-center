# HCC-design-advisor

## Summary

`HCC-design-advisor` is a lightweight internal design recommendation agent for Hermes Command Center.

It exposes a narrow advisory endpoint instead of importing the full upstream UI/UX repository stack.

## Endpoints

- `GET /ops/design-advisor/catalog`
- `POST /ops/design-advisor/recommend`

### Catalog response

The catalog exposes:
- `agent.id`
- `supported_page_types`
- `prompt_starters`
- `surface_presets`

Each surface preset can include:
- `best_fit_style`
- `layout_pattern`
- `recommended_components`
- `prompt_suggestions`

### Recommendation request body

```json
{
  "page_type": "skills",
  "intent": "refine the skill browser for operator workflows",
  "visual_profile": "premium-dark-ops"
}
```

### Recommendation response shape

- `agent.id` — always `HCC-design-advisor`
- `recommendation.page_type`
- `recommendation.intent`
- `recommendation.visual_profile`
- `recommendation.best_fit_style`
- `recommendation.layout_pattern`
- `recommendation.color_direction[]`
- `recommendation.typography_direction[]`
- `recommendation.interaction_cues[]`
- `recommendation.avoid[]`
- `recommendation.implementation_notes[]`
- `recommendation.recommended_components[]`
- `recommendation.prompt_suggestions[]`
- `recommendation.next_actions[]`
- `recommendation.summary`

## Current MVP behavior

The current implementation is intentionally narrow but now more product-oriented:

- page-type-aware presets for:
  - `skills`
  - `cron`
  - `activity`
  - `chat`
  - `usage`
- fallback preset for other surfaces
- strict request validation for required fields
- no runtime dependency on the upstream external repo

## Frontend integration

The `Skills Page` now includes a dedicated `HCC-design-advisor` panel with:

- advisor catalog summary
- prompt suggestions / starters
- prompt textarea
- run button
- structured recommendation output

The frontend requests:
- one catalog payload during normal page load
- one default recommendation during normal page load

## Why this shape

This preserves the product goal:

- Hermes-native capability
- low operational weight
- reusable UI guidance surface
- no hard dependency on the external `ui-ux-pro-max-skill` project structure

## Next extensions

Natural follow-ups:

1. vendor selected upstream CSV datasets into the repo
2. add queryable style families and visual profiles
3. expose the advisor on additional pages beyond the skill browser
4. persist accepted recommendations into docs/design tokens or settings
