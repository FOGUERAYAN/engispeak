"""Contenu pédagogique de la roadmap (issu de la page Notion
« English Public Speaking Masterclass (1-Month Roadmap) »).

Chaque semaine = 3 sessions + 1 Sunday Showcase = 4 étapes à valider.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Step:
    id: str
    kind: str  # "session" | "showcase"
    title: str
    talk: str | None = None
    learn: tuple[str, ...] = field(default_factory=tuple)
    challenge: tuple[str, ...] = field(default_factory=tuple)
    checkpoints: str | None = None


@dataclass(frozen=True)
class Week:
    number: int
    level: str
    color: str
    themes: str
    focus: str
    steps: tuple[Step, ...]


SESSION_FORMAT = (
    "Mode couple (recommandé)",
    "45–60 min / session",
    "Visionnage actif + prise de notes",
    "Analyse : structure, transitions, vocab, delivery",
    "1 mini prise filmée + feedback croisé",
)

ROADMAP: tuple[Week, ...] = (
    Week(
        number=1,
        level="Intermediate",
        color="green",
        themes="Inspiration & Habits",
        focus="Mastering the basics, storytelling, and voice tone.",
        steps=(
            Step(
                id="w1-s1",
                kind="session",
                title="Session 1 : Inspiration & Openings",
                talk="TED's secret to great public speaking — Chris Anderson",
                learn=(
                    "Construire une seule idée centrale (Throughline)",
                    "Hook + promesse dans les 30 premières secondes",
                ),
                challenge=(
                    "Re-raconter l'introduction avec vos mots",
                    "Enregistrer une vidéo de 2 minutes",
                ),
            ),
            Step(
                id="w1-s2",
                kind="session",
                title="Session 2 : Building Strong Habits",
                talk="Try something new for 30 days — Matt Cutts",
                learn=(
                    "Les mots de transition (first… then…, however…, as a result…, so…)",
                    "Comment passer d'une idée à l'autre sans rupture",
                ),
                challenge=(
                    "Résumer la structure principale sans notes",
                    "Objectif : 60–90 sec, clair, avec 3 transitions",
                ),
            ),
            Step(
                id="w1-s3",
                kind="session",
                title="Session 3 : The Power of Voice",
                talk="How to speak so that people want to listen — Julian Treasure",
                learn=(
                    "Les « 7 deadly sins of speaking »",
                    "Outils vocaux : pitch, volume, timbre, pace",
                ),
                challenge=(
                    "Lire un court texte 2 fois : (1) énergie haute",
                    "(2) énergie basse + résonance profonde",
                ),
            ),
            Step(
                id="w1-showcase",
                kind="showcase",
                title="Sunday Showcase : The Filmed Debrief",
                challenge=(
                    "Smartphone + chacun délivre un speech de 3 minutes : "
                    "« My Vision for the Next 5 Years »",
                ),
                checkpoints="Eye Contact (regard) + Body Language (posture, gestes)",
            ),
        ),
    ),
    Week(
        number=2,
        level="Upper-Intermediate",
        color="yellow",
        themes="Tech, Mindset & Society",
        focus="Explaining complex ideas simply, audience engagement, and rhetorical questions.",
        steps=(
            Step(
                id="w2-s4",
                kind="session",
                title="Session 4 : Mindset & Failure",
                talk="The power of believing that you can improve — Carol Dweck",
                learn=(
                    "Mélange data + storytelling pour changer une croyance",
                    "Vocab « growth mindset » + verbes d'argumentation (prove, suggest, challenge…)",
                ),
                challenge=(
                    "Speech 3 minutes : un échec personnel → une leçon",
                    "1 phrase de pivot obligatoire : « What I learned was… »",
                ),
            ),
            Step(
                id="w2-s5",
                kind="session",
                title="Session 5 : Inside the Human Mind",
                talk="Inside the mind of a master procrastinator — Tim Urban",
                learn=(
                    "Métaphores visuelles (Instant Gratification Monkey) + humour",
                    "Rendre un sujet psycho simple et mémorable",
                ),
                challenge=(
                    "Démarrer votre speech avec 2 rhetorical questions",
                    "Puis annoncer une « big idea » en 1 phrase",
                ),
            ),
            Step(
                id="w2-s6",
                kind="session",
                title="Session 6 : Technology & Connection",
                talk="Connected, but alone? — Sherry Turkle",
                learn=(
                    "Mise en scène, pacing émotionnel, pauses",
                    "Phrases courtes + silence = impact",
                ),
                challenge=(
                    "Expliquer comment une app fonctionne avec une seule analogie",
                    "Finir par une question au public : « So what are we trading off? »",
                ),
            ),
            Step(
                id="w2-showcase",
                kind="showcase",
                title="Sunday Showcase : The Filmed Debrief",
                challenge=(
                    "Débat 1-on-1 (3 min chacun) : " "« Are smartphones ruining real-world relationships? »",
                ),
                checkpoints="Gestes (open vs closed posture) + filler words",
            ),
        ),
    ),
    Week(
        number=3,
        level="Advanced",
        color="orange",
        themes="Body Language, Leadership & Persuasion",
        focus="Advanced vocabulary, elimination of filler words, and dramatic pacing.",
        steps=(
            Step(
                id="w3-s7",
                kind="session",
                title="Session 7 : Body Language Alchemy",
                talk="Your body language may shape who you are — Amy Cuddy",
                learn=(
                    "Présence, autorité, crédibilité non-verbale",
                    "Alignement : posture → voix → message",
                ),
                challenge=(
                    "Pitch 90 sec en « high-power posture »",
                    "Objectif : voix posée + rythme maîtrisé",
                ),
            ),
            Step(
                id="w3-s8",
                kind="session",
                title="Session 8 : Leadership & Persuasion",
                talk="How great leaders inspire action — Simon Sinek",
                learn=(
                    "Golden Circle (Why / How / What)",
                    "Répétition persuasive + phrases courtes",
                ),
                challenge=(
                    "Convaincre votre partenaire de tester une nouvelle routine",
                    "Structure obligatoire : Why → How → What (2–3 min)",
                ),
            ),
            Step(
                id="w3-s9",
                kind="session",
                title="Session 9 : Creative Thinking",
                talk="Do schools kill creativity? — Sir Ken Robinson",
                learn=(
                    "Humour « conversationnel » + timing",
                    "Delivery naturel + storytelling fluide",
                ),
                challenge=(
                    "Mini présentation de 2 minutes avec une pause intentionnelle "
                    "de 3 secondes avant l'argument clé",
                ),
            ),
            Step(
                id="w3-showcase",
                kind="showcase",
                title="Sunday Showcase : The Filmed Debrief",
                challenge=("Présentation filmée de 4 minutes (sujet passion)",),
                checkpoints="Défi « Zero Filler Words » (compter uh / um / du coup)",
            ),
        ),
    ),
    Week(
        number=4,
        level="Expert",
        color="red",
        themes="Charisma, Global Vision & Impact",
        focus="Rhetoric, storytelling, advanced vocabulary, and ultimate fluency.",
        steps=(
            Step(
                id="w4-s10",
                kind="session",
                title="Session 10 : Charisma & Resonance",
                talk="The power of vulnerability — Brené Brown",
                learn=(
                    "Connexion émotionnelle + vulnérabilité comme autorité",
                    "Variété lexicale + images fortes",
                ),
                challenge=(
                    "Raconter une histoire courte avec 5 adjectifs avancés (nouveaux pour vous)",
                    "Objectif : naturel, pas une « liste de mots »",
                ),
            ),
            Step(
                id="w4-s11",
                kind="session",
                title="Session 11 : Global Perspectives",
                talk="The danger of a single story — Chimamanda Ngozi Adichie",
                learn=(
                    "Pacing, précision, symétrie narrative",
                    "Vocab nuancé (subtle, biased, nuanced, compelling…)",
                ),
                challenge=(
                    "Anecdote personnelle : un malentendu",
                    "Focus : adjectifs précis + 1 phrase « lesson » finale",
                ),
            ),
            Step(
                id="w4-s12",
                kind="session",
                title="Session 12 : The Ultimate Pitch",
                talk="How to pitch to a VC — David S. Rose",
                learn=(
                    "Clarté à haute vitesse + confiance",
                    "Metrics, preuves, phrases « punchy »",
                ),
                challenge=(
                    "Pitch d'exactement 60 secondes (timer)",
                    "Finir par une demande claire : « What I'm asking for is… »",
                ),
            ),
            Step(
                id="w4-showcase",
                kind="showcase",
                title="Sunday Showcase : The Final Masterclass",
                challenge=("Keynote filmée de 5 minutes (sujet libre)",),
                checkpoints="Charisma, Fluency, Pacing, Dynamic Range (note /10 + 1 action)",
            ),
        ),
    ),
)

ALL_STEPS: tuple[Step, ...] = tuple(step for week in ROADMAP for step in week.steps)
STEP_IDS: frozenset[str] = frozenset(step.id for step in ALL_STEPS)


def get_week(number: int) -> Week | None:
    return next((w for w in ROADMAP if w.number == number), None)


def get_step(step_id: str) -> Step | None:
    return next((s for s in ALL_STEPS if s.id == step_id), None)


def week_of(step_id: str) -> int | None:
    for week in ROADMAP:
        if any(s.id == step_id for s in week.steps):
            return week.number
    return None
