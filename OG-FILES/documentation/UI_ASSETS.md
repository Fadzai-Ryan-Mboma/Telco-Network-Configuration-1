# UI Assets

## Logo Files

### SVG Logos (Vector - Scalable)
- `logo.svg` - Main logo for UI header (300x100px)
- `logo-icon.svg` - Icon version for sidebars/favicons (64x64px)
- `logo-dark.svg` - Dark theme variant
- `logo-light.svg` - Light theme variant

### Usage in Streamlit
```python
import streamlit as st

# Main logo in header
st.image("assets/logos/logo.svg", width=300)

# Icon in sidebar
with st.sidebar:
    st.image("assets/logos/logo-icon.svg", width=64)

# Theme-aware logo
theme = st.get_option("theme.base")
if theme == "dark":
    st.image("assets/logos/logo-dark.svg")
else:
    st.image("assets/logos/logo-light.svg")
```

## Adding Your Own Logos

Replace the placeholder SVG files with your actual Liquid Zimbabwe branding:

1. **Main Logo:** 300x100px SVG with company branding
2. **Icon:** 64x64px square icon for compact spaces
3. **Theme Variants:** Dark and light versions for theme compatibility

## File Format Guidelines

- **Primary:** SVG (vector, scalable, small file size)
- **Fallback:** PNG at 300 DPI for compatibility
- **Colors:** Use brand-consistent color schemes
- **Transparency:** Ensure logos work on various backgrounds