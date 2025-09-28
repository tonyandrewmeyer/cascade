"""Path utilities for resolving and normalizing file paths."""


# TODO: I thought there would be more of these. Probably this can live somewhere else.

def resolve_path(current_dir: str, path: str, home_dir: str) -> str:
    """Resolve a path relative to current directory, expanding ~ to home_dir (must be provided)."""
    if path == "~":
        return home_dir
    if path.startswith("~/"):
        return home_dir + path[1:]
    if path.startswith("~") and "/" not in path:
        return home_dir
    if path.startswith("/"):
        return path
    if current_dir == "/":
        return "/" + path
    return current_dir + "/" + path
