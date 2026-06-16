from edvibe_bot.evaluator.schema import EvalRequest, ExerciseType

RUBRIC_AUDIO = """\
You are grading a spoken-English homework answer in the "Pre-IELTS" marathon.
The target level is CEFR A2-B1, so calibrate expectations to an early-intermediate
learner — do not penalise minor slips that an A2-B1 speaker would naturally make.

The student answer below is a transcript of an audio recording. Judge:
- Task response: did they actually address the prompt/task?
- Pronunciation & intelligibility: could a listener follow them?
- Fluency: pace, hesitation, and connected speech for the A2-B1 band.
- Range & accuracy: vocabulary and grammar appropriate to A2-B1.

Be fair and encouraging. A blank, off-topic, or unintelligible answer scores low.
A clear, on-task A2-B1 answer scores in the upper range."""

RUBRIC_TEXT = """\
You are grading a written-English homework answer in the "Pre-IELTS" marathon.
The target level is CEFR A2-B1, so calibrate expectations to an early-intermediate
learner — do not penalise minor slips that an A2-B1 writer would naturally make.

The student answer below is written text. Judge:
- Task completion: did they actually address the prompt/task?
- Grammar accuracy: appropriate to the A2-B1 band.
- Vocabulary range: appropriate to the A2-B1 band.
- Coherence: is the answer organised and understandable?

Be fair and encouraging. A blank, off-topic, or empty answer scores low.
A clear, on-task A2-B1 answer scores in the upper range."""


def build_messages(req: "EvalRequest") -> "list[dict]":
    if req.exercise_type is ExerciseType.AUDIO:
        rubric = RUBRIC_AUDIO
    else:
        rubric = RUBRIC_TEXT

    system_content = (
        f"{rubric}\n\n"
        "Return your evaluation as a STRICT JSON object and nothing else "
        "(no markdown, no code fences, no commentary). The object MUST have "
        "exactly these keys:\n"
        '  "score": integer 0-10 (overall mark on a 0 to 10 scale),\n'
        '  "comment": string, a 1-2 sentence constructive comment IN ENGLISH '
        "addressed to the student,\n"
        '  "rationale": string, a brief internal justification (not shown to the student),\n'
        '  "confidence": number 0.0-1.0 (how confident you are in this score).\n'
        "If the answer is empty, off-topic, or you cannot assess it, give a low "
        "score and a low confidence."
    )

    user_content = (
        f"Section: {req.section}\n\n"
        f"Exercise task / prompt:\n{req.prompt_text}\n\n"
        f"Student answer:\n{req.student_answer}\n\n"
        "Evaluate the student answer against the task using the rubric above and "
        "respond with the strict JSON object."
    )

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]
