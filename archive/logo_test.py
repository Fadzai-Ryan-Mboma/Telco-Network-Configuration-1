#!/usr/bin/env python3
"""
Logo Display Test - Minimal UI test for logo functionality
"""

import streamlit as st
from pathlib import Path

def test_logo_display():
    """Test logo display functionality"""
    st.title("🧪 Logo Display Test")
    
    assets_path = Path("assets/logos")
    
    st.header("Logo Asset Status")
    
    logo_files = ["logo.svg", "logo-icon.svg", "logo-dark.svg", "logo-light.svg"]
    
    for logo_file in logo_files:
        logo_path = assets_path / logo_file
        if logo_path.exists():
            st.success(f"✅ {logo_file} found")
            with st.expander(f"Preview {logo_file}"):
                if "icon" in logo_file:
                    st.image(str(logo_path), width=64)
                else:
                    st.image(str(logo_path), width=300)
        else:
            st.error(f"❌ {logo_file} not found")
    
    st.header("Logo Integration Test")
    
    # Test main logo
    if (assets_path / "logo.svg").exists():
        st.subheader("Main Logo")
        st.image(str(assets_path / "logo.svg"), width=300)
    
    # Test icon
    if (assets_path / "logo-icon.svg").exists():
        st.subheader("Icon Logo")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.image(str(assets_path / "logo-icon.svg"), width=64)
    
    # Test theme variants
    st.subheader("Theme Variants")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Light Theme**")
        if (assets_path / "logo-light.svg").exists():
            st.image(str(assets_path / "logo-light.svg"), width=250)
    
    with col2:
        st.write("**Dark Theme**")
        if (assets_path / "logo-dark.svg").exists():
            st.image(str(assets_path / "logo-dark.svg"), width=250)

if __name__ == "__main__":
    st.set_page_config(
        page_title="Logo Test",
        page_icon="🧪",
        layout="wide"
    )
    test_logo_display()