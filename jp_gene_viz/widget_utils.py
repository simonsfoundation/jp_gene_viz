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

NO_OVERFLOW_JS = """
// prevent overflow scroll bars
debugger;
var div = element[0];
for (var count=0; count<10; count++) {
    if (div.style) {
        div.style.overflowX = "visible";
        div.style.overflow = "visible";
        div.style.height = "auto";
    }
    div = div.parentNode;
    if (!element) {
        break;
    }
}
"""

def no_overflow(js_proxy_widget):
    # prevent overflow scrollbars for widget and parent containers
    w = js_proxy_widget
    w.send(w.function(["element"], NO_OVERFLOW_JS)(w.element()))
