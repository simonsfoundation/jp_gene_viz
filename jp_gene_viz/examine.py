"""
Widget implementation to examine a value in Jupiter/IPython notebook.
"""

# XXX The current implementation leaks memory on the JS side
# by not cleaning up the DISPLAYS mapping when objects are no
# longer in use.

from jp_gene_viz import js_proxy
from IPython.display import display
#import types
import collections
import cgi

arrow_right = u"\u25b6 &nbsp;"
arrow_down = u"\u25bc &nbsp;"

def examine(thing, component_limit=100):
    od = ObjectDisplay(thing)
    od.component_limit = component_limit
    od.show()

class ObjectDisplay(object):

    # Stop iterating over components when this limit is reached
    component_limit = 100

    def __init__(self, target):
        self.target = target
        w = self.widget = js_proxy.ProxyWidget()
        e = self.element = w.element()
        # Create JS/python parallel mapping for finding elements.
        self.displays = {}
        self.expanded = {}
        w(e._set("DISPLAYS", {}))
        self.displays_reference = e.DISPLAYS
        self.jQuery = w.window().jQuery
        self.display_object(None, target, expanded=True, top=True)

    def display_object(self, parent_id, target, expanded=False, top=False):
        identifier = self.add_object_display(parent_id, target)
        if expanded:
            return self.expand_object(identifier, top=top)
        else:
            return self.unexpand_object(identifier, top=top)

    def click_callback(self, identifier):
        return self.widget.callback(self.click_object, data=identifier)

    def click_object(self, identifier, arguments):
        if identifier in self.expanded:
            self.unexpand_object(identifier, arguments, top=True)
        else:
            self.expand_object(identifier, arguments, top=True)

    def unexpand_object(self, identifier, arguments=None, top=False):
        if identifier in self.expanded:
            del self.expanded[identifier]
        target = self.displays[identifier]
        self.clear_object_display(identifier)
        self.add_text(identifier, arrow_right, onclick=self.click_callback(identifier))
        self.add_text(identifier, self.short_descriptor(target))
        if top:
            self.widget.flush()

    def short_descriptor(self, target, limit=80):
        ty = type(target)
        rep = repr(repr(target))
        if len(rep) > limit:
            rep = rep[:limit] + "..."
        return self.quote(ty.__name__ + " " + rep)

    def clear_object_display(self, identifier):
        ref = self.displays_reference._get(identifier)
        self.widget(ref.empty())

    def quote(self, s):
        return cgi.escape(s).encode("ascii", "xmlcharrefreplace").decode("utf8")

    def expand_object(self, identifier, arguments=None, top=False):
        limit = self.component_limit
        target = self.displays[identifier]
        self.expanded[identifier] = target
        target = self.displays[identifier]
        self.clear_object_display(identifier)
        self.add_text(identifier, arrow_down, onclick=self.click_callback(identifier))
        self.add_text(identifier, self.short_descriptor(target))
        ty = type(target)
        expanded = False
        if ty is dict:
            expanded = True
            self.add_text(identifier, " len=" + repr(len(target)))
            for (count, (k, v)) in enumerate(sorted(target.items())):
                self.add_text(identifier, 
                    '&nbsp; <em style="color:blue">dict item %s</em>' % repr(count))
                k_id = self.display_object(identifier, k)
                v_id = self.display_object(identifier, v)
                if limit and count > limit:
                    self.add_text(identifier, '<b style="color:red">DICT TRUNCATED AT COMPONENT LIMIT.</b>')
                    break
        elif ty is str:
            expanded = True
            quoted = self.quote(target)
            self.add_text(identifier, 
                '<pre style="color:darkmagenta">' + quoted + "</pre>")
        else:
            try:
                target_iter = iter(target)
            except TypeError:
                # not iterable
                pass
            else:
                # Iterable
                expanded = True
                for (count, item) in enumerate(target_iter):
                    self.add_text(identifier, '&nbsp; <em style="color:green">item %s</em>' % repr(count))
                    self.display_object(identifier, item)
                    if limit and count > limit:
                        self.add_text(identifier, '<b style="color:red">ITERABLE TRUNCATED AT COMPONENT LIMIT.</b>')
                        break
            if getattr(target, "__doc__", None) is not None:
                expanded = True
                self.add_text(identifier, 
                    '<br><em style="color:orange">__doc__ string</em>')
                self.display_object(identifier, target.__doc__)
            if hasattr(target, "__dict__"):
                expanded = True
                under_dict = target.__dict__
                #self.add_text(identifier, "__dict__")
                #self.display_object(identifier, under_dict)
                self.add_text(identifier, 
                    ' <em style="color:blue">len(__dict__)= %s </em>' % repr(len(under_dict)))
                for (count, (k, v)) in enumerate(sorted(under_dict.items())):
                    self.add_text(identifier, 
                        '<br><b style="color:green"><em>%s</em></b> attribute:' % str(k))
                    self.display_object(identifier, v)
                    if limit and count > limit:
                        self.add_text(identifier, '<b style="color:red">ATTRIBUTES TRUNCATED AT COMPONENT LIMIT.</b>')
                        break
                trait_values = getattr(target, "_trait_values", None)
                if type(trait_values) is dict:
                    self.add_text(identifier, 
                        '<br><em style="color:blue">#traits=%s</em>' % repr(len(trait_values)))
                    for (count, (k, v)) in enumerate(sorted(trait_values.items())):
                        self.add_text(identifier, 
                            '<br><b style="color:green"><em>%s</em></b> trait:' % str(k))
                        self.display_object(identifier, v)
                        if limit and count > limit:
                            self.add_text(identifier, '<b style="color:red">TRAITS TRUNCATED AT COMPONENT LIMIT.</b>')
                            break
            
        if not expanded:
            self.add_text(identifier, '<em style="color:red">??? can\'t expand this object ???</em>')
        if top:
            self.widget.flush()

    def add_object_display(self, parent_id, target):
        child_id = id(target)
        e = self.element
        w = self.widget
        #debug = w.function(["e"], "debugger;")(e)
        d = self.displays_reference
        if parent_id is None:
            # root level
            parent_reference = e
        else:
            parent_reference = d._get(parent_id)
        # remember the4 object by id
        self.displays[child_id] = target
        # create a div for the object on JS side. save in mapping, and attach to parent
        new_div = self.jQuery('<div style="padding-left: 10px; border-style:solid; border-color:#ffffff #eeeecc"></div>')
        save_div = d._set(child_id, new_div)
        w(save_div)
        attach_div = parent_reference.append(d._get(child_id))
        w(attach_div)
        return child_id

    def add_child_span(self, parent_id, span_reference):
        w = self.widget
        d = self.displays_reference
        parent_reference = d._get(parent_id)
        attach_span = parent_reference.append(span_reference)
        w(attach_span)

    def add_text(self, parent_id, text, onclick=None):
        new_span = self.jQuery(u"<span></span>").html(text)
        if onclick is not None:
            new_span = new_span.click(onclick)
        self.add_child_span(parent_id, new_span)

    def show(self):
        js_proxy.load_javascript_support()
        #self.widget.flush()
        display(self.widget)

