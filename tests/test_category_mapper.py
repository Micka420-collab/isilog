from pathlib import Path

from app.core.category_mapper import CategoryMapper


def test_category_mapping() -> None:
    mapper = CategoryMapper(Path("config/categories.json"))
    assert mapper.resolve_label("bdd_dump").endswith("Demande de dump")
    assert mapper.resolve_label("unknown") == "support_2i"
