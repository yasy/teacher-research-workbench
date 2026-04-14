import streamlit as st

from core.schemas import LiteratureItem, LiteratureReviewPack, TopicCard, WritingAsset


DEFAULT_PAGE = "选题助手"


def init_app_state() -> None:
    if "current_page" not in st.session_state:
        st.session_state.current_page = DEFAULT_PAGE
    if "topic_card" not in st.session_state:
        st.session_state.topic_card = None
    if "selected_topic" not in st.session_state:
        st.session_state.selected_topic = ""
    if "literature_items" not in st.session_state:
        st.session_state.literature_items = []
    if "literature_upload_queue" not in st.session_state:
        st.session_state.literature_upload_queue = []
    if "literature_uploader_nonce" not in st.session_state:
        st.session_state.literature_uploader_nonce = 0
    if "literature_review_pack" not in st.session_state:
        st.session_state.literature_review_pack = LiteratureReviewPack()
    if "current_paper_type" not in st.session_state:
        st.session_state.current_paper_type = ""
    if "writing_assets" not in st.session_state:
        st.session_state.writing_assets = []
    if "selected_review_themes" not in st.session_state:
        st.session_state.selected_review_themes = []
    if "selected_research_gaps" not in st.session_state:
        st.session_state.selected_research_gaps = []
    if "selected_writing_angles" not in st.session_state:
        st.session_state.selected_writing_angles = []
    if "writing_context_notes" not in st.session_state:
        st.session_state.writing_context_notes = ""
    if "writing_background_info" not in st.session_state:
        st.session_state.writing_background_info = ""
    if "writing_existing_practice" not in st.session_state:
        st.session_state.writing_existing_practice = ""
    if "writing_evidence_notes" not in st.session_state:
        st.session_state.writing_evidence_notes = ""
    if "writing_scope_limits" not in st.session_state:
        st.session_state.writing_scope_limits = ""
    if "preferred_writing_sections" not in st.session_state:
        st.session_state.preferred_writing_sections = []
    if "writing_build_plan" not in st.session_state:
        st.session_state.writing_build_plan = None
    if "polish_assets" not in st.session_state:
        st.session_state.polish_assets = []
    if "current_project_name" not in st.session_state:
        st.session_state.current_project_name = ""
    if "current_project_path" not in st.session_state:
        st.session_state.current_project_path = ""
    if "current_project_saved_at" not in st.session_state:
        st.session_state.current_project_saved_at = ""
    if "busy_actions" not in st.session_state:
        st.session_state.busy_actions = {}
    if "page_message" not in st.session_state:
        st.session_state.page_message = None


def get_topic_card() -> TopicCard | None:
    return st.session_state.topic_card


def set_topic_card(topic_card: TopicCard) -> None:
    st.session_state.topic_card = topic_card
    if topic_card.topic_candidates:
        st.session_state.selected_topic = topic_card.topic_candidates[0]
    elif topic_card.title:
        st.session_state.selected_topic = topic_card.title


def get_selected_topic() -> str:
    return st.session_state.selected_topic


def set_selected_topic(topic: str) -> None:
    st.session_state.selected_topic = topic.strip()


def get_literature_items() -> list[LiteratureItem]:
    return st.session_state.literature_items


def set_literature_items(items: list[LiteratureItem]) -> None:
    st.session_state.literature_items = items


def get_literature_upload_queue() -> list:
    return list(st.session_state.get("literature_upload_queue", []))


def add_literature_upload(uploaded_file) -> None:
    queue = list(st.session_state.get("literature_upload_queue", []))
    uploaded_signature = getattr(uploaded_file, "signature", "")
    if uploaded_signature:
        queue = [item for item in queue if getattr(item, "signature", "") != uploaded_signature]
    else:
        queue = [item for item in queue if getattr(item, "name", "") != getattr(uploaded_file, "name", "")]
    queue.append(uploaded_file)
    st.session_state.literature_upload_queue = queue


def remove_literature_upload(file_identifier: str) -> None:
    queue = list(st.session_state.get("literature_upload_queue", []))
    st.session_state.literature_upload_queue = [
        item
        for item in queue
        if getattr(item, "signature", getattr(item, "name", "")) != file_identifier
    ]


def clear_literature_upload_queue() -> None:
    st.session_state.literature_upload_queue = []


def bump_literature_uploader_nonce() -> int:
    st.session_state.literature_uploader_nonce = int(st.session_state.get("literature_uploader_nonce", 0)) + 1
    return st.session_state.literature_uploader_nonce


def get_literature_uploader_nonce() -> int:
    return int(st.session_state.get("literature_uploader_nonce", 0))


def get_literature_review_pack() -> LiteratureReviewPack:
    return st.session_state.get("literature_review_pack", LiteratureReviewPack())


def set_literature_review_pack(review_pack: LiteratureReviewPack) -> None:
    st.session_state.literature_review_pack = review_pack


def get_current_paper_type() -> str:
    return st.session_state.get("current_paper_type", "")


def set_current_paper_type(paper_type: str) -> None:
    st.session_state.current_paper_type = paper_type or ""


def get_writing_assets() -> list[WritingAsset]:
    return st.session_state.writing_assets


def set_writing_assets(items: list[WritingAsset]) -> None:
    st.session_state.writing_assets = items


def get_selected_review_themes() -> list[str]:
    return list(st.session_state.get("selected_review_themes", []))


def set_selected_review_themes(items: list[str]) -> None:
    st.session_state.selected_review_themes = [str(item).strip() for item in items if str(item).strip()]


def get_selected_research_gaps() -> list[str]:
    return list(st.session_state.get("selected_research_gaps", []))


def set_selected_research_gaps(items: list[str]) -> None:
    st.session_state.selected_research_gaps = [str(item).strip() for item in items if str(item).strip()]


def get_selected_writing_angles() -> list[str]:
    return list(st.session_state.get("selected_writing_angles", []))


def set_selected_writing_angles(items: list[str]) -> None:
    st.session_state.selected_writing_angles = [str(item).strip() for item in items if str(item).strip()]


def get_writing_context_notes() -> str:
    return str(st.session_state.get("writing_context_notes", "")).strip()


def set_writing_context_notes(text: str) -> None:
    st.session_state.writing_context_notes = str(text or "").strip()


def get_writing_background_info() -> str:
    return str(st.session_state.get("writing_background_info", "")).strip()


def set_writing_background_info(text: str) -> None:
    st.session_state.writing_background_info = str(text or "").strip()


def get_writing_existing_practice() -> str:
    return str(st.session_state.get("writing_existing_practice", "")).strip()


def set_writing_existing_practice(text: str) -> None:
    st.session_state.writing_existing_practice = str(text or "").strip()


def get_writing_evidence_notes() -> str:
    return str(st.session_state.get("writing_evidence_notes", "")).strip()


def set_writing_evidence_notes(text: str) -> None:
    st.session_state.writing_evidence_notes = str(text or "").strip()


def get_writing_scope_limits() -> str:
    return str(st.session_state.get("writing_scope_limits", "")).strip()


def set_writing_scope_limits(text: str) -> None:
    st.session_state.writing_scope_limits = str(text or "").strip()


def get_preferred_writing_sections() -> list[str]:
    return list(st.session_state.get("preferred_writing_sections", []))


def set_preferred_writing_sections(items: list[str]) -> None:
    st.session_state.preferred_writing_sections = [str(item).strip() for item in items if str(item).strip()]


def get_writing_build_plan():
    return st.session_state.get("writing_build_plan")


def set_writing_build_plan(plan) -> None:
    st.session_state.writing_build_plan = plan


def clear_writing_build_plan() -> None:
    st.session_state.writing_build_plan = None


def upsert_writing_assets(items: list[WritingAsset]) -> None:
    existing = {asset.asset_type: asset for asset in st.session_state.writing_assets}
    for asset in items:
        existing[asset.asset_type] = asset
    st.session_state.writing_assets = list(existing.values())


def update_writing_asset(asset_type: str, content: str, title: str | None = None) -> bool:
    updated = False
    assets: list[WritingAsset] = []
    for asset in st.session_state.writing_assets:
        if asset.asset_type == asset_type:
            assets.append(
                WritingAsset(
                    asset_type=asset.asset_type,
                    title=title if title is not None else asset.title,
                    content=content,
                    source_refs=asset.source_refs,
                )
            )
            updated = True
        else:
            assets.append(asset)
    st.session_state.writing_assets = assets
    return updated


def get_polish_assets() -> list[WritingAsset]:
    return st.session_state.polish_assets


def set_polish_assets(items: list[WritingAsset]) -> None:
    st.session_state.polish_assets = items


def get_current_project_meta() -> dict[str, str]:
    return {
        "project_name": st.session_state.get("current_project_name", ""),
        "project_path": st.session_state.get("current_project_path", ""),
        "saved_at": st.session_state.get("current_project_saved_at", ""),
    }


def set_current_project_meta(project_name: str = "", project_path: str = "", saved_at: str = "") -> None:
    st.session_state.current_project_name = project_name or ""
    st.session_state.current_project_path = project_path or ""
    st.session_state.current_project_saved_at = saved_at or ""


def get_busy_actions() -> dict:
    return dict(st.session_state.get("busy_actions", {}))


def get_busy_action(name: str):
    return st.session_state.get("busy_actions", {}).get(name)


def set_busy_action(name: str, payload=None) -> None:
    busy_actions = dict(st.session_state.get("busy_actions", {}))
    busy_actions[name] = payload if payload is not None else True
    st.session_state.busy_actions = busy_actions


def clear_busy_action(name: str) -> None:
    busy_actions = dict(st.session_state.get("busy_actions", {}))
    busy_actions.pop(name, None)
    st.session_state.busy_actions = busy_actions


def set_page_message(message_type: str, text: str) -> None:
    st.session_state.page_message = {"type": message_type, "text": text}


def pop_page_message():
    message = st.session_state.get("page_message")
    st.session_state.page_message = None
    return message


def has_literature_review_pack() -> bool:
    review_pack = get_literature_review_pack()
    return any(
        [
            review_pack.high_frequency_themes,
            review_pack.common_methods,
            review_pack.common_findings,
            review_pack.major_disagreements,
            review_pack.research_limitations,
            review_pack.suggested_angles,
        ]
    )


def get_writing_input_snapshot() -> dict:
    topic_card = get_topic_card()
    selected_topic = get_selected_topic()
    literature_items = get_literature_items()
    review_pack_loaded = has_literature_review_pack()
    return {
        "selected_topic": selected_topic,
        "research_problem": topic_card.research_problem if topic_card else "",
        "literature_count": len(literature_items),
        "review_pack_loaded": review_pack_loaded,
        "selected_review_themes": get_selected_review_themes(),
        "selected_research_gaps": get_selected_research_gaps(),
        "selected_writing_angles": get_selected_writing_angles(),
        "writing_context_notes": get_writing_context_notes(),
        "writing_background_info": get_writing_background_info(),
        "writing_existing_practice": get_writing_existing_practice(),
        "writing_evidence_notes": get_writing_evidence_notes(),
        "writing_scope_limits": get_writing_scope_limits(),
        "preferred_writing_sections": get_preferred_writing_sections(),
        "writing_build_plan": get_writing_build_plan(),
    }


def get_missing_writing_inputs() -> list[str]:
    missing = []
    if not get_selected_topic():
        missing.append("selected_topic")
    if not get_topic_card():
        missing.append("topic_card")
    if not get_literature_items():
        missing.append("literature_items")
    if not has_literature_review_pack():
        missing.append("literature_review_pack")
    return missing


def export_project_state() -> dict:
    topic_card = get_topic_card()
    review_pack = get_literature_review_pack()
    return {
        "selected_topic": get_selected_topic(),
        "topic_card": topic_card.__dict__ if topic_card else None,
        "literature_items": [item.__dict__ for item in get_literature_items()],
        "literature_review_pack": review_pack.__dict__,
        "writing_assets": [item.__dict__ for item in get_writing_assets()],
        "selected_review_themes": get_selected_review_themes(),
        "selected_research_gaps": get_selected_research_gaps(),
        "selected_writing_angles": get_selected_writing_angles(),
        "writing_context_notes": get_writing_context_notes(),
        "writing_background_info": get_writing_background_info(),
        "writing_existing_practice": get_writing_existing_practice(),
        "writing_evidence_notes": get_writing_evidence_notes(),
        "writing_scope_limits": get_writing_scope_limits(),
        "preferred_writing_sections": get_preferred_writing_sections(),
        "writing_build_plan": get_writing_build_plan(),
        "polish_assets": [item.__dict__ for item in get_polish_assets()],
        "current_paper_type": get_current_paper_type(),
    }


def import_project_state(data: dict) -> None:
    selected_topic = str(data.get("selected_topic", "")).strip()
    topic_card_data = data.get("topic_card")
    literature_items_data = data.get("literature_items", [])
    review_pack_data = data.get("literature_review_pack", {})
    writing_assets_data = data.get("writing_assets", [])
    selected_review_themes = data.get("selected_review_themes", [])
    selected_research_gaps = data.get("selected_research_gaps", [])
    selected_writing_angles = data.get("selected_writing_angles", [])
    writing_context_notes = data.get("writing_context_notes", "")
    writing_background_info = data.get("writing_background_info", "")
    writing_existing_practice = data.get("writing_existing_practice", "")
    writing_evidence_notes = data.get("writing_evidence_notes", "")
    writing_scope_limits = data.get("writing_scope_limits", "")
    preferred_writing_sections = data.get("preferred_writing_sections", [])
    writing_build_plan = data.get("writing_build_plan")
    polish_assets_data = data.get("polish_assets", [])

    st.session_state.selected_topic = selected_topic
    st.session_state.topic_card = TopicCard(**topic_card_data) if isinstance(topic_card_data, dict) else None
    st.session_state.literature_items = [
        LiteratureItem(**item) for item in literature_items_data if isinstance(item, dict)
    ]
    st.session_state.literature_review_pack = (
        LiteratureReviewPack(**review_pack_data) if isinstance(review_pack_data, dict) else LiteratureReviewPack()
    )
    st.session_state.writing_assets = [WritingAsset(**item) for item in writing_assets_data if isinstance(item, dict)]
    st.session_state.selected_review_themes = [
        str(item).strip() for item in selected_review_themes if str(item).strip()
    ]
    st.session_state.selected_research_gaps = [
        str(item).strip() for item in selected_research_gaps if str(item).strip()
    ]
    st.session_state.selected_writing_angles = [
        str(item).strip() for item in selected_writing_angles if str(item).strip()
    ]
    st.session_state.writing_context_notes = str(writing_context_notes or "").strip()
    st.session_state.writing_background_info = str(writing_background_info or "").strip()
    st.session_state.writing_existing_practice = str(writing_existing_practice or "").strip()
    st.session_state.writing_evidence_notes = str(writing_evidence_notes or "").strip()
    st.session_state.writing_scope_limits = str(writing_scope_limits or "").strip()
    st.session_state.preferred_writing_sections = [
        str(item).strip() for item in preferred_writing_sections if str(item).strip()
    ]
    st.session_state.writing_build_plan = writing_build_plan if isinstance(writing_build_plan, dict) else None
    st.session_state.polish_assets = [WritingAsset(**item) for item in polish_assets_data if isinstance(item, dict)]
    st.session_state.current_paper_type = str(data.get("current_paper_type", "")).strip()
