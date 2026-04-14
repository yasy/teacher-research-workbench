import json
from pathlib import Path

from core.utils import ensure_dir, now_ts, safe_filename


PROJECTS_DIR = Path(__file__).resolve().parent.parent / "data" / "projects"


def get_projects_dir() -> Path:
    ensure_dir(str(PROJECTS_DIR))
    return PROJECTS_DIR


def save_project(project_name: str, state: dict) -> str:
    projects_dir = get_projects_dir()
    safe_name = safe_filename(project_name or "未命名项目")
    project_path = projects_dir / f"{safe_name}.json"
    saved_at = now_ts()
    payload = {
        "project_name": project_name or "未命名项目",
        "saved_at": saved_at,
        "state": state,
    }
    project_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "project_name": payload["project_name"],
        "saved_at": saved_at,
        "path": str(project_path),
    }


def list_projects() -> list[dict]:
    projects_dir = get_projects_dir()
    projects = []
    for path in sorted(projects_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        projects.append(
            {
                "project_name": payload.get("project_name", path.stem),
                "saved_at": payload.get("saved_at", ""),
                "path": str(path),
            }
        )
    return projects


def load_project(project_path: str) -> dict:
    payload = json.loads(Path(project_path).read_text(encoding="utf-8"))
    return {
        "project_name": payload.get("project_name", Path(project_path).stem),
        "saved_at": payload.get("saved_at", ""),
        "path": str(project_path),
        "state": payload.get("state", {}),
    }
