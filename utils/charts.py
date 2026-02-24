# -*- coding: utf-8 -*-
"""
Chart Utilities for Dashboard v7.0
===================================
Common chart configurations, color schemes, and interactive helpers.

Production-ready with drill-down support.
"""
from typing import Dict, Any, Optional

# ============================================
# COLOR SCHEMES
# ============================================
CHART_COLORS = {
    "primary": ["#667eea", "#764ba2", "#f77f00", "#00b09b", "#4cc9f0"],
    "sentiment": {
        "positive": "#00b09b",
        "neutral": "#ffd166",
        "negative": "#ef476f"
    },
    "disc": {
        "D": "#ef476f",
        "I": "#ffd166",
        "S": "#00b09b",
        "C": "#4cc9f0"
    },
    "funnel": ["#667eea", "#764ba2", "#f77f00", "#00b09b", "#ef476f"],
    "heatmap": "RdYlGn",
    "sequential": "Purples",
    "trust": {
        "high": "#2ecc71", "medium": "#f39c12", "low": "#e74c3c",
        "very_high": "#27ae60", "very_low": "#c0392b"
    },
    "urgency": {
        "high": "#e74c3c", "medium": "#f39c12", "low": "#2ecc71",
        "urgent": "#c0392b", "immediate": "#e74c3c"
    },
}


def create_chart_layout(title: str = None, interactive: bool = False) -> Dict[str, Any]:
    """
    Standard chart layout for dark mode.
    
    Args:
        title: Optional chart title
        interactive: If True, add click-mode hints
        
    Returns:
        Dictionary with layout configuration
    """
    layout = {
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'font_color': 'white',
        'margin': dict(l=20, r=20, t=40, b=20),
        'hovermode': 'closest',
    }
    if title:
        suffix = "  *(click to drill-down)*" if interactive else ""
        layout['title'] = {
            'text': f"{title}{suffix}",
            'font': {'size': 16, 'color': 'white'}
        }
    return layout


def create_axis_config(show_grid: bool = True) -> Dict[str, Any]:
    """
    Create axis configuration for charts.
    
    Args:
        show_grid: Whether to show grid lines
        
    Returns:
        Axis configuration dictionary
    """
    return {
        'showgrid': show_grid,
        'gridcolor': 'rgba(255, 255, 255, 0.1)',
        'tickfont': {'color': 'rgba(255, 255, 255, 0.7)'},
        'title_font': {'color': 'white'}
    }


def get_color_for_value(value: float, thresholds: tuple = (0.3, 0.7)) -> str:
    """
    Get color based on value (for gauges, progress bars).
    
    Args:
        value: Value between 0 and 1
        thresholds: Tuple of (low, high) thresholds
        
    Returns:
        Color hex code
    """
    low, high = thresholds
    if value < low:
        return "#ef476f"  # Red/danger
    elif value < high:
        return "#ffd166"  # Yellow/warning
    else:
        return "#00b09b"  # Green/success


def create_gauge_chart_config(value: float, max_val: float = 100, title: str = "") -> Dict[str, Any]:
    """
    Create gauge chart configuration.
    
    Args:
        value: Current value
        max_val: Maximum value
        title: Chart title
        
    Returns:
        Plotly gauge configuration
    """
    return {
        'mode': "gauge+number",
        'value': value,
        'title': {'text': title, 'font': {'color': 'white'}},
        'gauge': {
            'axis': {'range': [0, max_val], 'tickcolor': 'white'},
            'bar': {'color': get_color_for_value(value / max_val)},
            'bgcolor': "rgba(255,255,255,0.1)",
            'borderwidth': 0,
            'steps': [
                {'range': [0, max_val * 0.3], 'color': "rgba(239, 71, 111, 0.3)"},
                {'range': [max_val * 0.3, max_val * 0.7], 'color': "rgba(255, 209, 102, 0.3)"},
                {'range': [max_val * 0.7, max_val], 'color': "rgba(0, 176, 155, 0.3)"}
            ]
        }
    }
