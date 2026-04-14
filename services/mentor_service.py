from pathlib import Path


PROMPTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "prompts"


def load_prompt_template(file_name: str) -> str:
    return (PROMPTS_DIR / file_name).read_text(encoding="utf-8")


def build_mentor_system_prompt() -> str:
    return load_prompt_template("mentor_prompt.md")


def build_topic_user_prompt(
    school_stage: str,
    subject: str,
    teaching_problem: str,
    research_context: str,
) -> str:
    template = load_prompt_template("topic_clarify_prompt.md")
    return template.format(
        school_stage=school_stage.strip(),
        subject=subject.strip(),
        teaching_problem=teaching_problem.strip(),
        research_context=research_context.strip(),
    )
