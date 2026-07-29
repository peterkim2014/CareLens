import re
from dataclasses import dataclass
from re import Pattern

from app.ai.intake.schemas import (
    ClinicalQuery,
    RiskAssessment,
    RiskLevel,
    RiskSignal,
    RoutingAction,
)


@dataclass(frozen=True)
class RiskRule:
    code: str
    label: str
    risk_level: RiskLevel
    patterns: tuple[Pattern[str], ...]


def compile_patterns(*patterns: str) -> tuple[Pattern[str], ...]:
    return tuple(re.compile(pattern, re.IGNORECASE) for pattern in patterns)


EMERGENCY_RULES: tuple[RiskRule, ...] = (
    RiskRule(
        code="chest_pain",
        label="Possible cardiac emergency",
        risk_level=RiskLevel.EMERGENCY,
        patterns=compile_patterns(
            r"\bchest pain\b",
            r"\bpressure in (my|the) chest\b",
            r"\bchest tightness\b",
        ),
    ),
    RiskRule(
        code="breathing_difficulty",
        label="Severe breathing difficulty",
        risk_level=RiskLevel.EMERGENCY,
        patterns=compile_patterns(
            r"\bcan(?:not|'t) breathe\b",
            r"\bstruggling to breathe\b",
            r"\bsevere shortness of breath\b",
            r"\bnot breathing\b",
        ),
    ),
    RiskRule(
        code="stroke_signs",
        label="Possible stroke symptoms",
        risk_level=RiskLevel.EMERGENCY,
        patterns=compile_patterns(
            r"\b(?:my|their|his|her)?\s*speech is slurred\b",
            r"\bslurred speech\b",
            r"\bone[- ]sided weakness\b",
            r"\bone side (?:feels|is) weak\b",
            r"\bweakness on one side\b",
            r"\bsudden numbness\b",
            r"\bface (?:is )?droop(?:ing)?\b",
        ),
    ),
    RiskRule(
        code="unconsciousness",
        label="Loss of consciousness",
        risk_level=RiskLevel.EMERGENCY,
        patterns=compile_patterns(
            r"\bunconscious\b",
            r"\bnot waking up\b",
            r"\bpassed out\b",
        ),
    ),
    RiskRule(
        code="severe_bleeding",
        label="Severe bleeding",
        risk_level=RiskLevel.EMERGENCY,
        patterns=compile_patterns(
            r"\bbleeding heavily\b",
            r"\bwon(?:not|'t) stop bleeding\b",
            r"\bsevere bleeding\b",
        ),
    ),
    RiskRule(
        code="self_harm",
        label="Possible self-harm emergency",
        risk_level=RiskLevel.EMERGENCY,
        patterns=compile_patterns(
            r"\bwant to kill myself\b",
            r"\bplanning to kill myself\b",
            r"\bwant to end my life\b",
            r"\bhurt myself\b",
        ),
    ),
)

URGENT_RULES: tuple[RiskRule, ...] = (
    RiskRule(
        code="high_fever",
        label="Potentially serious fever",
        risk_level=RiskLevel.URGENT,
        patterns=compile_patterns(
            r"\bhigh fever\b",
            r"\bfever (?:over|above) 10[34](?:\.\d+)?\b",
            r"\btemperature (?:over|above) 10[34](?:\.\d+)?\b",
        ),
    ),
    RiskRule(
        code="persistent_vomiting",
        label="Persistent vomiting",
        risk_level=RiskLevel.URGENT,
        patterns=compile_patterns(
            r"\b(?:cannot|can't) keep (?:food|fluids|water) down\b",
            r"\bvomiting continuously\b",
            r"\bpersistent vomiting\b",
        ),
    ),
    RiskRule(
        code="worsening_symptoms",
        label="Rapidly worsening symptoms",
        risk_level=RiskLevel.URGENT,
        patterns=compile_patterns(
            r"\bgetting worse quickly\b",
            r"\brapidly worsening\b",
            r"\bsuddenly getting worse\b",
        ),
    ),
)


class RiskClassifier:
    def __init__(
        self,
        emergency_rules: tuple[RiskRule, ...] = EMERGENCY_RULES,
        urgent_rules: tuple[RiskRule, ...] = URGENT_RULES,
    ) -> None:
        self._emergency_rules = emergency_rules
        self._urgent_rules = urgent_rules

    def classify(self, query: ClinicalQuery) -> RiskAssessment:
        emergency_signals = self._match_rules(
            query.text,
            self._emergency_rules,
        )

        if emergency_signals:
            return RiskAssessment(
                risk_level=RiskLevel.EMERGENCY,
                routing_action=RoutingAction.SEEK_EMERGENCY_CARE,
                signals=emergency_signals,
                reasoning=[
                    "One or more emergency warning signals were detected.",
                    "Further automated analysis should not delay emergency care.",
                ],
                emergency_message=(
                    "This may be a medical emergency. Contact local emergency "
                    "services now or go to the nearest emergency department. "
                    "Do not rely on this application for emergency treatment."
                ),
            )

        urgent_signals = self._match_rules(
            query.text,
            self._urgent_rules,
        )

        if urgent_signals:
            return RiskAssessment(
                risk_level=RiskLevel.URGENT,
                routing_action=RoutingAction.SEEK_PROMPT_CARE,
                signals=urgent_signals,
                reasoning=[
                    "One or more potentially urgent warning signals were detected.",
                    (
                        "Prompt evaluation by a qualified healthcare "
                        "professional is advised."
                    ),
                ],
            )

        return RiskAssessment(
            risk_level=RiskLevel.ROUTINE,
            routing_action=RoutingAction.CONTINUE_ANALYSIS,
            signals=[],
            reasoning=[
                "No configured emergency or urgent warning signals were detected.",
                "The query may continue through the evidence retrieval pipeline.",
            ],
        )

    @staticmethod
    def _match_rules(
        text: str,
        rules: tuple[RiskRule, ...],
    ) -> list[RiskSignal]:
        signals: list[RiskSignal] = []

        for rule in rules:
            for pattern in rule.patterns:
                match = pattern.search(text)

                if match is None:
                    continue

                signals.append(
                    RiskSignal(
                        code=rule.code,
                        label=rule.label,
                        matched_phrase=match.group(0),
                        risk_level=rule.risk_level,
                    )
                )
                break

        return signals
