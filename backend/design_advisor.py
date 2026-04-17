from __future__ import annotations

from dataclasses import dataclass

from http_api import RequestValidationError


@dataclass(frozen=True)
class DesignPreset:
    best_fit_style: str
    layout_pattern: str
    color_direction: list[str]
    typography_direction: list[str]
    interaction_cues: list[str]
    avoid: list[str]
    implementation_notes: list[str]
    recommended_components: list[str]
    prompt_suggestions: list[str]
    next_actions: list[str]


_DEFAULT_PRESET = DesignPreset(
    best_fit_style='Data-Dense Dashboard',
    layout_pattern='fixed sidebar + compact topbar + two-column operator workspace',
    color_direction=['green-black base', 'champagne-gold hierarchy accents', 'teal status glow for positive signals'],
    typography_direction=['geometric sans headings', 'neutral sans body copy', 'monospace reserved for operational payloads'],
    interaction_cues=['sticky local actions', 'clear empty states', 'fast scan hierarchy with restrained chrome'],
    avoid=['oversized hero sections', 'low-contrast metadata', 'decorative motion on operational screens'],
    implementation_notes=['keep cards compact', 'separate critical actions visually', 'prefer summary + drill-down instead of long scrolling walls'],
    recommended_components=['summary KPI strip', 'detail drill-down panel', 'contextual action rail'],
    prompt_suggestions=['Tighten information hierarchy for this surface.', 'Recommend operator-safe CTA placement.', 'Improve density without harming scanability.'],
    next_actions=['Choose one visual direction.', 'Reduce competing emphasis zones.', 'Apply the recommendation to the top-priority panel first.'],
)

_PAGE_PRESETS = {
    'skills': DesignPreset(
        best_fit_style='Executive Dashboard',
        layout_pattern='browser list + recommendation composer + structured drill-down panel',
        color_direction=['dark graphite surfaces', 'champagne-gold emphasis for headings', 'teal highlights for active guidance'],
        typography_direction=['premium sans heading weight', 'high-legibility neutral sans body', 'monospace only for generated notes'],
        interaction_cues=['prefill prompts from current page context', 'one-click recommendation refresh', 'copyable implementation checklist'],
        avoid=['buried primary action', 'too many competing cards', 'full-width prose without structure'],
        implementation_notes=['place the advisor beside the skill list', 'keep output in short bullet clusters', 'show agent identity explicitly as HCC-design-advisor'],
        recommended_components=['skill browser list', 'prompt starter chips', 'implementation checklist output'],
        prompt_suggestions=['Refine the skill browser for operator workflows.', 'Improve the visual hierarchy between skills and advisor.', 'Recommend denser layout for scanning many skills.'],
        next_actions=['Compare two hierarchy options.', 'Reduce duplicate captions.', 'Highlight the selected skill and matching recommendation together.'],
    ),
    'cron': DesignPreset(
        best_fit_style='Drill-Down Analytics',
        layout_pattern='job registry + run history + output inspection rail',
        color_direction=['charcoal base', 'amber warning accents', 'teal healthy-state indicators'],
        typography_direction=['compact heading scale', 'table-friendly body font', 'monospace for schedules and payloads'],
        interaction_cues=['status-first labels', 'history filtered by selection', 'guarded actions grouped near context'],
        avoid=['visual noise around destructive actions', 'oversized empty-state art', 'soft contrast on schedule text'],
        implementation_notes=['keep cron actions near each job', 'default detail panel to latest selection', 'make schedule/status scannable at a glance'],
        recommended_components=['job registry list', 'run history panel', 'output inspection detail'],
        prompt_suggestions=['Refine the cron control hierarchy.', 'Recommend clearer state labels for cron jobs.', 'Improve the run history scanability.'],
        next_actions=['Highlight risky controls.', 'Keep history tied to selection.', 'Reduce repetition in schedule metadata.'],
    ),
    'activity': DesignPreset(
        best_fit_style='Drill-Down Analytics',
        layout_pattern='timeline feed + focused JSON drill-down panel',
        color_direction=['graphite background', 'teal for inspect state', 'gold only for high-priority emphasis'],
        typography_direction=['dense list typography', 'muted metadata secondary text', 'monospace for payload preview'],
        interaction_cues=['windowed pagination', 'inspect action per event', 'stable drill-down target'],
        avoid=['unbounded infinite scroll', 'multi-color event spam', 'animated timeline gimmicks'],
        implementation_notes=['preserve event density', 'let newest item seed the drill-down', 'make retention/window state obvious'],
        recommended_components=['timeline list', 'drill-down payload panel', 'window/retention summary'],
        prompt_suggestions=['Improve the activity drill-down readability.', 'Recommend a denser event card pattern.', 'Refine the activity timeline hierarchy for operators.'],
        next_actions=['Reduce redundant event chrome.', 'Promote inspect action consistently.', 'Keep the current window state visible.'],
    ),
    'chat': DesignPreset(
        best_fit_style='Bento Box Grid',
        layout_pattern='session list + transcript + stream status stack',
        color_direction=['green-black shell', 'teal active stream indicators', 'gold reserved for agent controls'],
        typography_direction=['clear transcript role labels', 'neutral body font', 'monospace for tool payload snippets'],
        interaction_cues=['persistent stream status', 'message cards with strong role separation', 'quick session switch'],
        avoid=['chat bubbles that waste horizontal space', 'oversized avatars', 'blended role colors with low contrast'],
        implementation_notes=['optimize for transcript scanability', 'keep tool calls visually distinct', 'treat stream state as operational telemetry'],
        recommended_components=['session switcher', 'role-separated transcript cards', 'live stream status module'],
        prompt_suggestions=['Improve transcript scanability for operators.', 'Recommend better separation of tool calls and messages.', 'Reduce visual clutter in the chat workspace.'],
        next_actions=['Tighten message spacing.', 'Emphasize active session context.', 'Reserve accent color for stream state and critical controls.'],
    ),
    'usage': DesignPreset(
        best_fit_style='Drill-Down Analytics',
        layout_pattern='KPI summary + per-agent breakdown + circuit breaker control panel',
        color_direction=['dark graphite base', 'teal for healthy spend signals', 'amber/red for breaker risk states'],
        typography_direction=['tabular-friendly numerics', 'compact heading scale', 'neutral operator body text'],
        interaction_cues=['surface risk state first', 'show thresholds beside live totals', 'make per-agent drill-down one click away'],
        avoid=['buried token/cost metrics', 'detached control forms without live context', 'overdecorated charts for tiny datasets'],
        implementation_notes=['keep totals visible above the fold', 'pair breaker config with current tripped reasons', 'make top sessions directly inspectable'],
        recommended_components=['usage KPI cards', 'circuit breaker form', 'per-agent breakdown list', 'top sessions drill-down'],
        prompt_suggestions=['Recommend a more actionable usage overview.', 'Improve the breaker panel hierarchy.', 'Refine the per-agent cost breakdown for scanability.'],
        next_actions=['Promote the tripped state into the summary strip.', 'Reduce repeated metric labels.', 'Keep live totals and controls in the same viewport.'],
    ),
}


class HCCDesignAdvisor:
    agent_id = 'HCC-design-advisor'
    supported_page_types = sorted(_PAGE_PRESETS)
    prompt_starters = [
        'Refine hierarchy for an operator dashboard.',
        'Recommend denser layout without losing scanability.',
        'Improve placement of critical controls and warnings.',
    ]

    def catalog(self) -> dict[str, object]:
        return {
            'agent': {'id': self.agent_id, 'kind': 'internal-design-advisor'},
            'supported_page_types': list(self.supported_page_types),
            'prompt_starters': list(self.prompt_starters),
            'surface_presets': {
                page_type: {
                    'best_fit_style': preset.best_fit_style,
                    'layout_pattern': preset.layout_pattern,
                    'recommended_components': list(preset.recommended_components),
                    'prompt_suggestions': list(preset.prompt_suggestions),
                }
                for page_type, preset in _PAGE_PRESETS.items()
            },
        }

    def recommend(self, *, page_type: str, intent: str, visual_profile: str | None = None) -> dict[str, object]:
        normalized_page_type = self._normalize_page_type(page_type)
        clean_intent = self._validate_text_field(intent, field='intent')
        clean_profile = self._normalize_optional_text(visual_profile)
        preset = _PAGE_PRESETS.get(normalized_page_type, _DEFAULT_PRESET)
        recommendation = {
            'page_type': normalized_page_type,
            'intent': clean_intent,
            'visual_profile': clean_profile or 'premium-dark-ops',
            'best_fit_style': preset.best_fit_style,
            'layout_pattern': preset.layout_pattern,
            'color_direction': list(preset.color_direction),
            'typography_direction': list(preset.typography_direction),
            'interaction_cues': list(preset.interaction_cues),
            'avoid': list(preset.avoid),
            'implementation_notes': list(preset.implementation_notes),
            'recommended_components': list(preset.recommended_components),
            'prompt_suggestions': list(preset.prompt_suggestions),
            'next_actions': list(preset.next_actions),
        }
        recommendation['summary'] = self._build_summary(recommendation)
        return {
            'agent': {
                'id': self.agent_id,
                'kind': 'internal-design-advisor',
                'supported_page_types': list(self.supported_page_types),
            },
            'recommendation': recommendation,
        }

    @staticmethod
    def _normalize_page_type(page_type: str | None) -> str:
        return HCCDesignAdvisor._validate_text_field(page_type, field='page_type').lower().replace(' ', '-')

    @staticmethod
    def _normalize_optional_text(value: str | None) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None

    @staticmethod
    def _validate_text_field(value: str | None, *, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise RequestValidationError(status=400, code='ops.invalid_request', message=f'{field} is required', details={'field': field})
        return value.strip()

    @staticmethod
    def _build_summary(recommendation: dict[str, object]) -> str:
        style = recommendation['best_fit_style']
        layout = recommendation['layout_pattern']
        profile = recommendation['visual_profile']
        return f"{style} for {recommendation['page_type']} using {layout} under {profile}."


hcc_design_advisor = HCCDesignAdvisor()
