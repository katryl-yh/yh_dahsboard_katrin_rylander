"""
UI helper functions for Taipy GUI components.
Provides common utilities used across multiple dashboard pages.
"""

import logging

def safe_refresh(state, *var_names):
    """
    Safely refresh multiple state variables in Taipy.
    
    Parameters:
        state: Taipy state object
        var_names: Variable names to refresh
    """
    if hasattr(state, "refresh"):
        for v in var_names:
            try:
                state.refresh(v)
            except Exception as e:
                logging.warning("refresh(%s) failed: %s", v, e)

def create_filter_change_callback(filter_name, chart_name):
    """
    Create a generic callback function for filter changes.
    
    Parameters:
        filter_name: Name of the filter state variable
        chart_name: Name of the chart to update
        
    Returns:
        Function: Callback function for filter changes
    """
    def on_filter_change(state):
        # Update the chart based on the new filter value
        # Implement specific filter logic in each page
        safe_refresh(state, chart_name)
        return state
    
    return on_filter_change

def format_number(number, use_space_separator=True):
    """
    Format numbers with thousands separators.
    
    Parameters:
        number: Number to format
        use_space_separator: Use space instead of comma as thousands separator
        
    Returns:
        str: Formatted number string
    """
    try:
        if number is None:
            return "0"
            
        formatted = "{:,}".format(int(number))
        if use_space_separator:
            return formatted.replace(",", " ")
        return formatted
    except:
        return str(number)

def update_page_state(state, updates_dict):
    """
    Update multiple state variables at once.
    
    Parameters:
        state: Taipy state object
        updates_dict: Dictionary of {variable_name: new_value}
    """
    if not updates_dict:
        return
        
    variables_to_refresh = []
    
    for var_name, value in updates_dict.items():
        try:
            setattr(state, var_name, value)
            variables_to_refresh.append(var_name)
        except Exception as e:
            logging.warning(f"Failed to update state.{var_name}: {e}")
    
    # Refresh all successfully updated variables
    safe_refresh(state, *variables_to_refresh)