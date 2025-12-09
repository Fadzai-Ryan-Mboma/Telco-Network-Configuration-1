"""
Site selection components for the Streamlit UI.

Provides site search, filtering, and selection functionality
with real-time data loading from the database.
"""

from typing import Any, Callable, Optional

import streamlit as st

from cassava_optimizer.ui.theme import COLORS, CASSAVA_GREEN, CASSAVA_NAVY


def render_site_selector(
    sites: list[dict[str, Any]],
    selected_site: Optional[str] = None,
    on_select: Optional[Callable[[str], None]] = None,
    key: str = "site_selector",
) -> Optional[str]:
    """
    Render a site selection dropdown with search.
    
    Args:
        sites: List of site dictionaries with 'name' and optional metadata
        selected_site: Currently selected site name
        on_select: Callback when site is selected
        key: Unique key for the component
        
    Returns:
        Selected site name or None
    """
    if not sites:
        st.warning("No sites available. Please check the database connection.")
        return None
    
    # Extract site names and create display format
    site_options = ["-- Select a site --"]
    site_map = {}
    
    for site in sites:
        name = site.get("name") or site.get("site_name", "Unknown")
        region = site.get("region", "")
        cell_count = site.get("cell_count", 0)
        status = site.get("status", "unknown")
        
        display_name = f"{name}"
        if region:
            display_name += f" ({region})"
        if cell_count:
            display_name += f" - {cell_count} cells"
        
        site_options.append(display_name)
        site_map[display_name] = name
    
    # Find current index
    current_index = 0
    if selected_site:
        for i, opt in enumerate(site_options):
            if site_map.get(opt) == selected_site or opt == selected_site:
                current_index = i
                break
    
    # Render selectbox
    selection = st.selectbox(
        "Select Site",
        options=site_options,
        index=current_index,
        key=key,
        help="Choose a site to analyze or optimize",
    )
    
    if selection and selection != "-- Select a site --":
        site_name = site_map.get(selection, selection)
        if on_select:
            on_select(site_name)
        return site_name
    
    return None


def render_site_search(
    sites: list[dict[str, Any]],
    on_select: Optional[Callable[[str], None]] = None,
    key: str = "site_search",
) -> Optional[str]:
    """
    Render a site search input with autocomplete-style filtering.
    
    Args:
        sites: List of site dictionaries
        on_select: Callback when site is selected
        key: Unique key for the component
        
    Returns:
        Selected site name or None
    """
    # Search input
    search_term = st.text_input(
        "🔍 Search Sites",
        placeholder="Enter site name...",
        key=f"{key}_input",
        help="Type to filter sites by name",
    )
    
    # Filter sites based on search
    if search_term:
        filtered_sites = [
            s for s in sites
            if search_term.lower() in (s.get("name") or s.get("site_name", "")).lower()
        ]
    else:
        filtered_sites = sites
    
    # Show filtered results
    if filtered_sites:
        site_names = [
            s.get("name") or s.get("site_name", "Unknown") 
            for s in filtered_sites[:10]  # Limit results
        ]
        
        selected = st.radio(
            "Matching Sites",
            options=site_names,
            key=f"{key}_results",
            label_visibility="collapsed",
        )
        
        if selected and on_select:
            on_select(selected)
        return selected
    elif search_term:
        st.info(f"No sites found matching '{search_term}'")
    
    return None


def render_site_card(
    site: dict[str, Any],
    is_selected: bool = False,
    on_click: Optional[Callable[[str], None]] = None,
) -> None:
    """
    Render a site as a clickable card.
    
    Args:
        site: Site dictionary with metadata
        is_selected: Whether this site is currently selected
        on_click: Callback when card is clicked
    """
    name = site.get("name") or site.get("site_name", "Unknown")
    region = site.get("region", "N/A")
    cell_count = site.get("cell_count", 0)
    status = site.get("status", "unknown")
    last_updated = site.get("last_updated", "N/A")
    
    # Status styling
    status_colors = {
        "online": CASSAVA_GREEN,
        "offline": COLORS["error"],
        "degraded": COLORS["warning"],
        "unknown": COLORS["text_secondary"],
    }
    status_color = status_colors.get(status.lower(), COLORS["text_secondary"])
    
    # Selection border
    border = f"2px solid {CASSAVA_GREEN}" if is_selected else f"1px solid {COLORS['border']}"
    
    st.markdown(
        f"""
        <div class="site-card" style="
            border: {border};
            background: {COLORS['card_bg']};
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            cursor: pointer;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-size: 1.1rem; font-weight: 600; color: {COLORS['text_primary']};">
                        {name}
                    </div>
                    <div style="font-size: 0.85rem; color: {COLORS['text_secondary']};">
                        {region} • {cell_count} cells
                    </div>
                </div>
                <div style="
                    background: {status_color}20;
                    color: {status_color};
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 0.8rem;
                    font-weight: 500;
                ">
                    {status.upper()}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Make entire card clickable
    if st.button(
        "Select",
        key=f"select_site_{name}",
        type="primary" if not is_selected else "secondary",
        use_container_width=True,
    ):
        if on_click:
            on_click(name)


def render_site_grid(
    sites: list[dict[str, Any]],
    selected_site: Optional[str] = None,
    columns: int = 3,
    on_select: Optional[Callable[[str], None]] = None,
) -> Optional[str]:
    """
    Render sites in a grid layout.
    
    Args:
        sites: List of site dictionaries
        selected_site: Currently selected site name
        columns: Number of columns in the grid
        on_select: Callback when site is selected
        
    Returns:
        Selected site name
    """
    if not sites:
        st.info("No sites available")
        return selected_site
    
    # Create column containers
    cols = st.columns(columns)
    
    for i, site in enumerate(sites):
        with cols[i % columns]:
            name = site.get("name") or site.get("site_name", "Unknown")
            is_selected = name == selected_site
            
            # Use a callback to handle selection
            def make_callback(site_name):
                def callback():
                    if on_select:
                        on_select(site_name)
                return callback
            
            render_site_card(
                site=site,
                is_selected=is_selected,
                on_click=on_select,
            )
    
    return selected_site


def render_site_info(
    site: dict[str, Any],
    show_details: bool = True,
) -> None:
    """
    Render detailed site information panel.
    
    Args:
        site: Site dictionary with full metadata
        show_details: Whether to show expanded details
    """
    if not site:
        return
    
    name = site.get("name") or site.get("site_name", "Unknown")
    
    st.markdown(
        f"""
        <div class="card">
            <div class="card-header">
                <span>📡</span>
                <span>Site Information: {name}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Basic info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Region",
            value=site.get("region", "N/A"),
        )
    with col2:
        st.metric(
            label="Cells",
            value=site.get("cell_count", 0),
        )
    with col3:
        status = site.get("status", "unknown")
        st.metric(
            label="Status",
            value=status.upper(),
        )
    
    if show_details:
        with st.expander("📋 Full Details", expanded=False):
            # Configuration details
            st.markdown("**Configuration:**")
            config = site.get("configuration", {})
            if config:
                for key, value in config.items():
                    st.markdown(f"- **{key}**: `{value}`")
            else:
                st.markdown("- No configuration data available")
            
            # Metadata
            st.markdown("---")
            st.markdown("**Metadata:**")
            st.markdown(f"- **Site ID**: `{site.get('id', 'N/A')}`")
            st.markdown(f"- **Last Updated**: {site.get('last_updated', 'N/A')}")
            st.markdown(f"- **Created**: {site.get('created_at', 'N/A')}")


def render_region_filter(
    regions: list[str],
    selected_regions: Optional[list[str]] = None,
    key: str = "region_filter",
) -> list[str]:
    """
    Render a multi-select filter for regions.
    
    Args:
        regions: Available region names
        selected_regions: Currently selected regions
        key: Unique key for the component
        
    Returns:
        List of selected region names
    """
    if not regions:
        return []
    
    selected = st.multiselect(
        "Filter by Region",
        options=regions,
        default=selected_regions or [],
        key=key,
        help="Select one or more regions to filter sites",
    )
    
    return selected


def render_status_filter(
    selected_statuses: Optional[list[str]] = None,
    key: str = "status_filter",
) -> list[str]:
    """
    Render a filter for site status.
    
    Args:
        selected_statuses: Currently selected statuses
        key: Unique key for the component
        
    Returns:
        List of selected status values
    """
    status_options = ["online", "offline", "degraded", "unknown"]
    
    selected = st.multiselect(
        "Filter by Status",
        options=status_options,
        default=selected_statuses or [],
        key=key,
        format_func=lambda x: x.title(),
        help="Select one or more statuses to filter sites",
    )
    
    return selected
