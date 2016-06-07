"""
Useful operations on generic widgets.
"""


def set_visibility(element, visible):
    # hack: store the old display -- we want to restore it to the same value later...
    old_display = element.layout.display
    if old_display != "none" and not hasattr(element, "save_display"):
        element.save_display = old_display
    display = "none"
    if visible:
        display = getattr(element, "save_display", "") # reset to previous value
    element.layout.display = display

def is_visible(element):
    return element.layout.display != "none"