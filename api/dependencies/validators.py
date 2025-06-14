from fastapi import HTTPException
from src.components.avatar_theme import ThemeStyle
from src.components.image_edit_mask import EditSection

def validate_theme(theme: str) -> ThemeStyle:
    """Validate and convert theme string to ThemeStyle enum."""
    try:
        return ThemeStyle(theme.lower())
    except ValueError:
        valid_themes = [t.value for t in ThemeStyle]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid theme. Must be one of: {valid_themes}"
        )

def validate_edit_section(section: str) -> EditSection:
    """Validate and convert section string to EditSection enum."""
    try:
        return EditSection(section.lower())
    except ValueError:
        valid_sections = [s.value for s in EditSection]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid section. Must be one of: {valid_sections}"
        ) 