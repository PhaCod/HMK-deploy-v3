# -*- coding: utf-8 -*-
"""
Helper Functions for Dashboard v6.0
====================================
Common utility functions used across tabs.
"""
import pandas as pd
import numpy as np
from typing import Union, Optional


def safe_percentage(numerator: Union[int, float], denominator: Union[int, float]) -> float:
    """
    Calculate percentage safely.
    
    Args:
        numerator: Top number
        denominator: Bottom number
        
    Returns:
        Percentage value (0-100) or 0 if division by zero
    """
    if denominator == 0:
        return 0.0
    return (numerator / denominator) * 100


def safe_float(value, default: float = 0.0) -> float:
    """
    Safely convert value to float, handling numpy arrays and NaN.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Float value
    """
    try:
        if value is None:
            return default
        val = float(value)
        if np.isnan(val):
            return default
        return val
    except (TypeError, ValueError):
        return default


def safe_int(value, default: int = 0) -> int:
    """
    Safely convert value to int, handling numpy arrays and NaN.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Integer value
    """
    try:
        if value is None:
            return default
        val = float(value)
        if np.isnan(val):
            return default
        return int(val)
    except (TypeError, ValueError):
        return default


def format_currency(value, currency: str = "VND") -> str:
    """
    Format number as currency.
    
    Args:
        value: Numeric value
        currency: Currency symbol
        
    Returns:
        Formatted string
    """
    if pd.isna(value):
        return "N/A"
    return f"{value:,.0f} {currency}"


def get_delta_indicator(current: float, previous: float) -> Optional[str]:
    """
    Get delta indicator for metrics comparison.
    
    Args:
        current: Current value
        previous: Previous value
        
    Returns:
        Delta string like "+10.5%" or None
    """
    if previous == 0:
        return None
    delta = ((current - previous) / previous) * 100
    return f"{delta:+.1f}%"


def parse_list_column(series: pd.Series) -> pd.Series:
    """
    Parse column that may contain list strings like "['a', 'b']" or single values.
    
    Args:
        series: Pandas Series with potential list strings
        
    Returns:
        Exploded Series with individual values
    """
    all_values = []
    for val in series.dropna():
        val_str = str(val).strip()
        # Skip empty/unknown values
        if val_str in ['', 'unknown', 'Unknown', 'none', 'None', '[]', 'null']:
            continue
        # Try to parse as list
        if val_str.startswith('[') and val_str.endswith(']'):
            try:
                import ast
                parsed = ast.literal_eval(val_str)
                if isinstance(parsed, list):
                    all_values.extend([str(v).strip() for v in parsed if v])
                    continue
            except:
                pass
        # Single value
        all_values.append(val_str)
    return pd.Series(all_values) if all_values else pd.Series(dtype=str)


def format_large_number(value: Union[int, float]) -> str:
    """
    Format large numbers with K/M/B suffixes.
    
    Args:
        value: Numeric value
        
    Returns:
        Formatted string like "1.5K" or "2.3M"
    """
    if value is None or pd.isna(value):
        return "N/A"
    
    value = float(value)
    if value >= 1_000_000_000:
        return f"{value/1_000_000_000:.1f}B"
    elif value >= 1_000_000:
        return f"{value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"{value/1_000:.1f}K"
    else:
        return f"{value:.0f}"
