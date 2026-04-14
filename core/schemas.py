from dataclasses import dataclass, field


@dataclass
class TopicCard:
    title: str = ""
    topic_candidates: list[str] = field(default_factory=list)
    research_problem: str = ""
    research_questions: list[str] = field(default_factory=list)
    target_population: str = ""
    context: str = ""
    keywords: list[str] = field(default_factory=list)
    recommended_methods: list[str] = field(default_factory=list)
    mentor_analysis: str = ""


@dataclass
class LiteratureItem:
    file_name: str = ""
    title: str = ""
    authors: list[str] = field(default_factory=list)
    year: str = ""
    abstract: str = ""
    method: str = ""
    findings: str = ""
    theme: str = ""


@dataclass
class LiteraturePreprocessResult:
    file_name: str = ""
    original_file_name: str = ""
    stored_file_name: str = ""
    title: str = ""
    authors: list[str] = field(default_factory=list)
    year: str = ""
    abstract_text: str = ""
    intro_snippets: list[str] = field(default_factory=list)
    conclusion_snippets: list[str] = field(default_factory=list)
    body_snippets: list[str] = field(default_factory=list)
    extraction_backend: str = ""
    is_ai_ready: bool = False
    preprocess_error: str = ""


@dataclass
class LiteratureReviewPack:
    high_frequency_themes: list[str] = field(default_factory=list)
    common_methods: list[str] = field(default_factory=list)
    common_findings: list[str] = field(default_factory=list)
    major_disagreements: list[str] = field(default_factory=list)
    research_limitations: list[str] = field(default_factory=list)
    suggested_angles: list[str] = field(default_factory=list)


@dataclass
class WritingAsset:
    asset_type: str = ""
    title: str = ""
    content: str = ""
    source_refs: list[str] = field(default_factory=list)
