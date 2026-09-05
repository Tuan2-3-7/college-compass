"""LLM provider layer.

Two implementations behind one interface:

- MockLLM: deterministic, heuristic-based. Free, offline, testable. Active
  whenever no ANTHROPIC_API_KEY is configured. Feedback quality is real enough
  to drive the UI honestly (it is labeled "mock" everywhere).
- ClaudeLLM: the real thing via the official `anthropic` SDK, model
  `claude-opus-5`, with refusal handling and server-side fallbacks enabled.
  Activates automatically when backend/.env carries ANTHROPIC_API_KEY.

Both return the same JSON shapes, so routers and frontend never care which
one is running. The coach COACHES - neither provider writes essay content
for the student.
"""

from __future__ import annotations

import json
import re
from collections import Counter

from ..config import settings

# ----------------------------------------------------------------------------
# shared vocabulary for the mock heuristics
# ----------------------------------------------------------------------------

CLICHES = [
    "ever since i was young", "ever since i was a child", "for as long as i can remember",
    "changed my life", "outside my comfort zone", "make a difference",
    "follow my dreams", "hard work pays off", "the value of hard work",
    "at the end of the day", "in today's society", "broaden my horizons",
    "pushed me to be my best", "i have always been passionate",
]

REFLECTION_MARKERS = [
    "realized", "learned", "understood", "now i see", "looking back",
    "in retrospect", "taught me", "came to see", "i began to understand",
    "this experience showed me",
]

STORY_MARKERS = [
    "one day", "that day", "the moment", "i remember", "when i", "that night",
    "the first time", "suddenly", '"',
]

STOPWORDS = set(
    "the a an and or but of to in on for with was were is are be been i my me it "
    "at as that this by from we you they he she his her their our have had has not "
    "so when what who which".split()
)


def _words(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def _paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def _clamp_score(x: float) -> int:
    return int(max(0, min(100, round(x))))


class MockLLM:
    """Deterministic stand-in for Claude. Same output shapes, zero cost."""

    name = "mock"

    # ---------------- essay coach ----------------

    def analyze_essay(self, prompt: str, content: str, word_limit: int | None = None) -> dict:
        words = _words(content)
        n = len(words)
        paragraphs = _paragraphs(content)
        lower = content.lower()

        if n < 50:
            return self._too_short(n, paragraphs)

        # --- dimension scores ---
        cliches_found = [c for c in CLICHES if c in lower]
        reflection_hits = sum(lower.count(m) for m in REFLECTION_MARKERS)
        story_hits = sum(1 for m in STORY_MARKERS if m in lower)
        first_person = sum(1 for w in words if w in ("i", "my", "me"))

        counts = Counter(w for w in words if w not in STOPWORDS and len(w) > 3)
        most_common = counts.most_common(1)
        repetition_threshold = max(5, n // 80)
        repeated = [w for w, c in counts.most_common(3) if c > repetition_threshold]

        # specificity: numbers and proper-noun-ish tokens mid-sentence
        digits = len(re.findall(r"\d", content))
        proper = len(re.findall(r"(?<![.!?]\s)(?<!^)\b[A-Z][a-z]{2,}", content))
        specificity = _clamp_score(35 + (digits * 3 + proper * 2) / max(n / 100, 1))

        prompt_words = {w for w in _words(prompt) if len(w) > 4 and w not in STOPWORDS}
        overlap = sum(1 for w in prompt_words if w in set(words))
        prompt_alignment = (
            _clamp_score(30 + 70 * overlap / max(len(prompt_words), 1)) if prompt_words else 70
        )

        long_sentences = sum(
            1 for s in re.split(r"[.!?]", content) if len(_words(s)) > 40
        )
        grammar = _clamp_score(90 - long_sentences * 8 - content.count("  ") * 2)

        ideal_paras = 3 <= len(paragraphs) <= 7
        structure = _clamp_score(
            55 + (25 if ideal_paras else 0) + (10 if len(paragraphs) >= 2 else -20)
            + (10 if n >= 300 else 0)
        )

        scores = {
            "prompt_alignment": prompt_alignment,
            "storytelling": _clamp_score(40 + story_hits * 12),
            "personal_voice": _clamp_score(30 + 100 * first_person / max(n, 1) * 12),
            "specificity": specificity,
            "reflection": _clamp_score(30 + reflection_hits * 18),
            "structure": structure,
            "grammar": grammar,
        }
        overall = _clamp_score(
            0.20 * scores["prompt_alignment"]
            + 0.15 * scores["storytelling"]
            + 0.12 * scores["personal_voice"]
            + 0.15 * scores["specificity"]
            + 0.18 * scores["reflection"]
            + 0.10 * scores["structure"]
            + 0.10 * scores["grammar"]
            - len(cliches_found) * 3
        )

        weaknesses = self._weaknesses(scores, cliches_found, repeated, n, word_limit)
        questions = self._questions(scores)
        suggestions = self._suggestions(scores, cliches_found)

        return {
            "overall_score": overall,
            "scores": scores,
            "paragraph_feedback": self._paragraph_feedback(paragraphs),
            "weaknesses": weaknesses,
            "suggestions": suggestions,
            "questions": questions,
            "flags": {
                "cliches": cliches_found,
                "repeated_words": repeated,
                "word_count": n,
                "most_used_word": most_common[0][0] if most_common else None,
            },
            "provider": self.name,
        }

    def _too_short(self, n: int, paragraphs: list[str]) -> dict:
        return {
            "overall_score": 15,
            "scores": {k: 15 for k in (
                "prompt_alignment", "storytelling", "personal_voice",
                "specificity", "reflection", "structure", "grammar")},
            "paragraph_feedback": [
                {"paragraph": i + 1, "comment": "Too short to evaluate meaningfully."}
                for i in range(len(paragraphs))
            ],
            "weaknesses": [
                f"The draft is only {n} words - far too short to tell your story. "
                "Aim for a full draft before asking for analysis."
            ],
            "suggestions": ["Free-write the full story first; edit later."],
            "questions": ["What is the one moment this essay is really about?"],
            "flags": {"cliches": [], "repeated_words": [], "word_count": n, "most_used_word": None},
            "provider": self.name,
        }

    def _paragraph_feedback(self, paragraphs: list[str]) -> list[dict]:
        out = []
        for i, para in enumerate(paragraphs):
            pw = _words(para)
            low = para.lower()
            notes = []
            if len(pw) > 180:
                notes.append("Very long paragraph - consider splitting it.")
            if i == 0 and any(c in low for c in CLICHES):
                notes.append("Opens on a cliché - your first line is prime real estate; start inside the story instead.")
            if not any(m in low for m in REFLECTION_MARKERS) and i == len(paragraphs) - 1:
                notes.append("The ending describes events but doesn't reflect - what changed in you?")
            if re.search(r"\d", para) or re.search(r"\b[A-Z][a-z]{2,}\b", para[1:]):
                notes.append("Good concrete detail here - specifics like this make the essay yours.")
            if not notes:
                notes.append("Reads clearly; check that every sentence earns its place.")
            out.append({"paragraph": i + 1, "comment": " ".join(notes[:2])})
        return out

    def _weaknesses(self, scores, cliches, repeated, n, word_limit) -> list[str]:
        w = []
        if scores["reflection"] < 60:
            w.append(
                "Reflection is the weakest area: the essay recounts what happened but says "
                "little about how it changed your thinking. Admissions readers care more "
                "about the meaning you make than the events themselves."
            )
        if scores["specificity"] < 60:
            w.append(
                "Low specificity: few names, numbers, or concrete details. Generic essays "
                "could be written by anyone - details make it yours."
            )
        if scores["prompt_alignment"] < 60:
            w.append("The draft drifts from the prompt - a reader might wonder which question it answers.")
        if scores["storytelling"] < 55:
            w.append("There's no clear scene or moment - consider anchoring the essay in one specific story.")
        if cliches:
            w.append(f"Clichés found ({len(cliches)}): " + "; ".join(f'"{c}"' for c in cliches[:3]) + ".")
        if repeated:
            w.append("Repetition: the word(s) " + ", ".join(f'"{r}"' for r in repeated) + " appear very often.")
        if word_limit and n > word_limit:
            w.append(f"Over the word limit: {n} words vs. a {word_limit}-word limit.")
        return w

    def _questions(self, scores) -> list[str]:
        bank = {
            "reflection": "What do you understand now that you didn't before this experience?",
            "specificity": "Can you replace one general sentence with the exact detail - a name, a number, a smell, a line of dialogue?",
            "storytelling": "If this essay were a 30-second film, what single scene would we watch?",
            "personal_voice": "Read it aloud: does it sound like you talking, or like a formal report?",
            "prompt_alignment": "In one sentence, how does this essay answer the prompt?",
            "structure": "If you deleted your first paragraph, would the essay get stronger?",
            "grammar": "Which sentence is hardest to read aloud in one breath?",
        }
        weakest = sorted(scores, key=scores.get)[:3]
        return [bank[k] for k in weakest]

    def _suggestions(self, scores, cliches) -> list[str]:
        s = []
        weakest = min(scores, key=scores.get)
        s.append(f"Revise for {weakest.replace('_', ' ')} first - it's your lowest dimension.")
        if cliches:
            s.append("Cut every cliché and replace it with something only you could write.")
        s.append("Then read the whole draft aloud and mark anywhere you stumble.")
        return s

    # ---------------- tutor ----------------

    GLOSSARY = {
        ("course rigor", "rigor"): (
            "Course rigor means how challenging your classes are relative to what your school "
            "offers. Colleges read your transcript next to your school's profile: taking AP "
            "Calculus when it's offered signals more than an easy A. Example: an A in AP "
            "Biology generally reads stronger than an A+ in regular Biology.\n\nQuick check: "
            "are you taking the most challenging classes you can handle in the subjects that "
            "matter for your intended major?"
        ),
        ("supplemental essay", "supplement"): (
            "A supplemental essay is a school-specific essay beyond your main personal "
            "statement - usually 'Why this college?', 'Why this major?', or a community "
            "prompt. The key: be specific to THAT school (professors, programs, traditions), "
            "because a supplement you could paste into another school's box is a weak one.\n\n"
            "Want to try? Draft one paragraph on why one school on your list fits you."
        ),
        ("personal statement", "common app essay", "main essay"): (
            "The personal statement is your main 650-word essay (on the Common App) that goes "
            "to every college you apply to. Its job is to show who you are beyond grades - "
            "one story, told well, with real reflection - not to restate your resume."
        ),
        ("activity description", "activities list"): (
            "Strong activity descriptions lead with action verbs and quantify impact in the "
            "~150 characters you get. Weak: 'Member of robotics club.' Strong: 'Led 12-person "
            "build team; designed drivetrain that reached state finals.' Numbers + your "
            "specific role beat titles."
        ),
        ("early decision", "early action", "ed vs ea"): (
            "Early Action (EA) = apply early (usually Nov 1), hear back early, no commitment. "
            "Early Decision (ED) = apply early but BINDING - if admitted, you attend and "
            "withdraw other applications. ED can boost odds at some schools but only makes "
            "sense for a clear first choice you can afford; international students should "
            "check the aid implications carefully before binding."
        ),
        ("test optional", "test-optional"): (
            "Test-optional means the school doesn't require SAT/ACT scores - you choose "
            "whether to send them. Rule of thumb: send scores at or above the school's "
            "middle-50% range; otherwise your application is evaluated on everything else. "
            "Note: 'test-blind' schools won't look at scores even if you send them."
        ),
        ("i-20",): (
            "The I-20 is the official document a US school issues after you're admitted and "
            "show proof of funds. You need it to pay the SEVIS fee and apply for your F-1 "
            "student visa. Sequence: admission → financial documents → I-20 → SEVIS fee → "
            "visa interview."
        ),
        ("sevis",): (
            "SEVIS is the US government's tracking system for international students. After "
            "receiving your I-20 you pay the SEVIS I-901 fee (currently ~$350) and bring the "
            "receipt to your visa interview."
        ),
        ("f-1", "student visa"): (
            "The F-1 is the standard US student visa. You apply after getting your I-20: pay "
            "the SEVIS fee, complete the DS-160 form, then attend an interview at a US "
            "embassy/consulate. Bring your I-20, financial documents, and ties-to-home evidence."
        ),
        ("proof of funds", "financial documentation"): (
            "Proof of funds is documentation (bank statements, sponsor letters, scholarship "
            "awards) showing you can pay for at least the first year. Schools need it to issue "
            "your I-20, and the visa officer may ask for it again."
        ),
        ("fafsa",): (
            "The FAFSA (Free Application for Federal Student Aid) is the US government form "
            "for federal grants and loans - for US citizens/permanent residents. File it at "
            "studentaid.gov as early as possible; many states and schools have deadlines."
        ),
        ("css profile", "css"): (
            "The CSS Profile is the College Board's aid form used by ~200 mostly-private "
            "colleges for their institutional aid. More detailed than FAFSA, has a fee "
            "(waivers exist), and some schools require it from international applicants too."
        ),
        ("letter of recommendation", "recommendation"): (
            "Recommendation letters come from teachers (usually 2, junior-year core subjects) "
            "and your counselor. Ask early - a month before deadlines minimum - and give each "
            "writer a 'brag sheet' of your work in their class so they can be specific."
        ),
        ("demonstrated interest",): (
            "Demonstrated interest is how some colleges track whether you actually want to "
            "attend: campus visits, info sessions, opening their emails, supplemental essay "
            "specificity. Highly selective schools mostly don't track it; many mid-size "
            "privates do."
        ),
        ("gpa", "weighted", "unweighted"): (
            "Unweighted GPA maxes at 4.0 regardless of course difficulty; weighted GPA adds "
            "points for honors/AP/IB (often up to 5.0). Colleges usually recalculate GPA "
            "their own way, so course rigor matters more than the number alone."
        ),
        ("toefl", "ielts", "english proficiency"): (
            "TOEFL and IELTS are English-proficiency tests most US universities require from "
            "international applicants whose schooling wasn't in English. Typical competitive "
            "minimums: TOEFL 90-100+, IELTS 6.5-7.5. Many schools waive them after several "
            "years at an English-medium school - check each school's policy."
        ),
    }

    def tutor_reply(self, message: str, history: list[dict] | None = None) -> dict:
        low = message.lower()
        for keys, answer in self.GLOSSARY.items():
            if any(k in low for k in keys):
                return {"reply": answer, "provider": self.name}
        topics = sorted({keys[0] for keys in self.GLOSSARY})
        return {
            "reply": (
                "I'm running in demo mode (no AI key configured), so I can only explain a "
                "fixed set of admissions topics right now. Try asking about one of these:\n\n"
                + ", ".join(topics)
                + "\n\nOnce an Anthropic API key is added, I can tutor any subject - including "
                "academics like calculus - with examples, quizzes, and follow-ups."
            ),
            "provider": self.name,
        }


class ClaudeLLM:
    """Real Claude adapter (model claude-opus-5). Used when a key is configured.

    Includes server-side refusal fallbacks (recommended default for Opus 5) and
    a stop_reason check. Import of the SDK is lazy so the mock path never needs
    the package installed.
    """

    name = "anthropic"

    ESSAY_SYSTEM = (
        "You are an experienced college-essay coach. You NEVER write or rewrite essay "
        "content for the student - you coach: diagnose, explain, and ask questions that "
        "help them improve their own writing. Respond with ONLY a valid JSON object, no "
        "markdown fences, matching exactly this schema: "
        '{"overall_score": int 0-100, "scores": {"prompt_alignment": int, "storytelling": int, '
        '"personal_voice": int, "specificity": int, "reflection": int, "structure": int, '
        '"grammar": int}, "paragraph_feedback": [{"paragraph": int, "comment": str}], '
        '"weaknesses": [str], "suggestions": [str], "questions": [str], '
        '"flags": {"cliches": [str], "repeated_words": [str], "word_count": int}}'
    )

    TUTOR_SYSTEM = (
        "You are a patient tutor for high-school students preparing US college "
        "applications. Explain clearly, give one concrete example, and end with a short "
        "question or exercise that checks understanding. You may tutor academic subjects "
        "too. Keep answers under 250 words unless asked for more."
    )

    def __init__(self):
        import anthropic  # lazy: only needed when a key is configured

        self._anthropic = anthropic
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.anthropic_model

    def _create(self, system: str, messages: list[dict], max_tokens: int = 4096):
        response = self.client.beta.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        if response.stop_reason == "refusal":
            detail = ""
            if response.stop_details and response.stop_details.explanation:
                detail = f" ({response.stop_details.explanation})"
            raise RuntimeError(f"The model declined this request{detail}.")
        return "".join(b.text for b in response.content if b.type == "text")

    def analyze_essay(self, prompt: str, content: str, word_limit: int | None = None) -> dict:
        user = (
            f"Essay prompt:\n{prompt or '(no prompt given)'}\n\n"
            + (f"Word limit: {word_limit}\n\n" if word_limit else "")
            + f"Student draft:\n{content}"
        )
        text = self._create(self.ESSAY_SYSTEM, [{"role": "user", "content": user}])
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                raise RuntimeError("Model response was not valid JSON")
            data = json.loads(match.group(0))
        data["provider"] = self.name
        return data

    def tutor_reply(self, message: str, history: list[dict] | None = None) -> dict:
        messages = [
            {"role": m["role"], "content": m["content"]} for m in (history or [])[-10:]
        ]
        messages.append({"role": "user", "content": message})
        reply = self._create(self.TUTOR_SYSTEM, messages, max_tokens=2048)
        return {"reply": reply, "provider": self.name}


_provider = None


def get_llm():
    """Return the active provider; Claude when a key is configured, else mock."""
    global _provider
    if _provider is None:
        if settings.anthropic_api_key:
            try:
                _provider = ClaudeLLM()
            except ImportError:
                # key set but SDK missing: pip install anthropic
                _provider = MockLLM()
        else:
            _provider = MockLLM()
    return _provider
