
"""
This is an implementation of a generic "javascript proxy" Jupyter notebook widget.
The idea is that for many purposes this widget will make it easy to use javascript
components without having to implement the "javascript view" side of the widget.

For example to create a jqueryui dialog we don't need any javascript support
because jqueryui is already loaded as part of Jupyter and the proxy widget
supplies access to the needed methods from Python:

     from jp_gene_viz import js_proxy
     from IPython.display import display
     js_proxy.load_javascript_support()
     dialog = js_proxy.ProxyWidget()
     command = dialog.element().html("Hello from jqueryui").dialog()
     display(dialog)
     dialog.send(command)

The strategy is to pass a sequence of encoded javascript "commands" as a JSON
object to the generic widget proxy and have the proxy execute javascript actions
in response to the commands.  Commands can be chained using "chaining".

(object.method1(...).
    method2(...).
    method3(...)
    )

Results for the last command of the chain are passed back to the
Python widget controller object (to a restricted recursive depth)
except that non-JSON permitted values are mapped to None.

Here are notes on the encoding function E for the JSON commands and their interpretation
as javascript actions:

WIDGET INTERFACE: widget.element()
JSON ENCODING: ["element"]
JAVASCRIPT ACTION: get the this.$el element for the widget.
JAVASCRIPT RESULT: this.$el
PASSED TO PYTHON: This should never be the end of the chain!

WIDGET INTERFACE: widget.window()
JSON ENCODING: ["window"]
JAVASCRIPT ACTION: get the global namespace (window object)
JAVASCRIPT RESULT: window object
PASSED TO PYTHON: This should never be the end of the chain!

WIDGET INTERFACE: <target>.method(<arg0>, <arg1>, ..., <argn>)
  or for non-python names <target>.__getattr___("$method")(<arg0>...)
JSON ENCODING: ["method", target, method_name, arg0, ..., argn]
JAVASCRIPT ACTION: E(target).method_name(E(arg0), E(arg1), ..., E(argn))
JAVASCRIPT RESULT: Result of method call.
PASSED TO PYTHON: Result of method call in JSON translation.

WIDGET INTERFACE: (this is not exposed to the widget directly)
JSON ENCODING: ["id", X]
JAVASCRIPT ACTION/RESULT: X -- untranslated JSON object.
PASSED TO PYTHON: X (but it should never be the last in the chain)

WIDGET INTERFACE: (not exposed)
JSON ENCODING: ["list", x0, x1, ..., xn]
JAVASCRIPT ACTION/RESULT: [E[x0], E[x1], ..., E[xn]]  -- recursively translated list.
PASSED TO PYTHON: should never be returned.

WIDGET INTERFACE: (not exposed)
JSON ENCODING: ["dict", {k0: v0, ..., kn: vn}]
JAVASCRIPT ACTION/RESULT: {k0: E(v0), ..., kn: E(vn)} -- recursively translated mapping.
PASSED TO PYTHON: should never be returned.

WIDGET INTERFACE: widget.callback(function, untranslated_data)
JSON ENCODING: ["callback", numerical_identifier, untranslated_data]
JAVASCRIPT ACTION: create a javascript callback function which triggers 
   a python call to function(js_parameters, untranslated_data)
PASSED TO PYTHON: should never be returned.

WIDGET INTERFACE: target.attribute_name
   or for non-python names <target>.__getattr___("$attr")
JSON ENCODING: ["get", target, attribute_name]
JAVASCRIPT ACTION/RESULT: E(target).attribute_name
PASSED TO PYTHON: The value of the javascript property

WIDGET INTERFACE: <target>._set(attribute_name, <value>)
JSON ENCODING: ["set", target, attribute_name, value]
JAVASCRIPT ACTION: E(target).attribute_name = E(value)
JAVASCRIPT RESULT: E(target) for chaining.
PASSED TO PYTHON: E(target) translated to JSON (probably should never be last in chain)

WIDGET INTERFACE: not directly exposed.
JSON ENCODING: not_a_list
JAVASCRIPT ACTION: not_a_list -- other values are not translated
PASSED TO PYTHON: This should not be the end of the chain.

"""

import types
import ipywidgets as widgets
import traitlets
import js_context


def load_javascript_support(verbose=False):
    js_context.load_if_not_loaded(["js_proxy.js"])


class ProxyWidget(widgets.DOMWidget):

    """
    Proxy connection to an arbitrary javascript component.
    """

    _view_name = traitlets.Unicode("JSProxyView", sync=True)

    # traitlet port to use for sending commends to javascript
    commands = traitlets.List([], sync=True)

    # traitlet port to receive results of commands from javascript
    results = traitlets.List([], sync=True)

    # traitlet port to receive results of callbacks from javascript
    callback_results = traitlets.List([], sync=True)

    verbose = False

    def __init__(self, *pargs, **kwargs):
        super(ProxyWidget, self).__init__(*pargs, **kwargs)
        self.counter = 0
        self.count_to_results_callback = {}
        self.default_event_callback = None
        self.identifier_to_callback = {}
        #self.callback_to_identifier = {}
        self.on_trait_change(self.handle_callback_results, "callback_results")
        self.on_trait_change(self.handle_results, "results")

    def handle_results(self, att_name, old, new):
        if self.verbose:
            print ("got results", new)
        [identifier, json_value] = new
        i2c = self.identifier_to_callback
        results_callback = i2c.get(identifier)
        if results_callback is not None:
            del i2c[identifier]
            results_callback(json_value)

    def handle_callback_results(self, att_name, old, new):
        if self.verbose:
            print ("got callback results", new)
        [identifier, json_value, arguments] = new
        i2c = self.identifier_to_callback
        results_callback = i2c.get(identifier)
        if results_callback is not None:
            results_callback(json_value, arguments)

    def send(self, command, results_callback=None):
        return self.send_commands([command], results_callback)

    def send_commands(self, commands_iter, results_callback=None):
        count = self.counter
        self.counter = count + 1
        commands = validate_commands(list(commands_iter))
        payload = [count, commands]
        if results_callback is not None:
            self.identifier_to_callback[count] = results_callback
        # send the command using the commands traitlet which is mirrored to javascript.
        self.commands = payload
        return payload

    def callback(self, callback_function, data):
        count = self.counter
        self.counter = count + 1
        # no need for a wrapper here -- this should never chain.
        command = ["callback", count, data]
        self.identifier_to_callback[count] = callback_function
        return command

    def element(self):
        return CommandMaker("element")

    def window(self):
        return CommandMaker("window")


def validate_commands(commands, top=True):
    """
    Validate a command sequence (and convert to list formate if needed.)
    """
    return [validate_command(c, top) for c in commands]


def validate_command(command, top=True):
    # convert CommandMaker to list format.
    if isinstance(command, CommandMaker):
        command = command._cmd()
    ty = type(command)
    if ty is types.ListType:
        indicator = command[0]
        remainder = command[1:]
        if indicator == "element" or indicator == "window":
            assert len(remainder) == 0
        elif indicator == "method":
            target = remainder[0]
            name = remainder[1]
            args = remainder[2:]
            target = validate_command(target, top=True)
            assert type(name) is types.StringType, "method name must be a string " + repr(name)
            args = validate_commands(args, top=False)
            remainder = [target, name] + args
        elif indicator == "id":
            assert len(remainder) == 1, "id takes one argument only " + repr(remainder)
        elif indicator == "list":
            remainder = validate_commands(remainder, top=False)
        elif indicator == "dict":
            [d] = remainder
            d = dict((k, validate_command(d[k], top=False)) for k in d)
        elif indicator == "callback":
            [numerical_identifier, untranslated_data] = remainder
            assert type(numerical_identifier) is types.IntType, \
                "must be integer " + repr(numerical_identifier)
        elif indicator == "get":
            [target, name] = remainder
            target = validate_command(target, top=True)
            name = validate_command(name, top=False)
            remainder = [target, name]
        elif indicator == "set":
            [target, name, value] = remainder
            target = validate_command(target, top=True)
            name = validate_command(name, top=False)
            value = validate_command(value, top=False)
            remainder = [target, name, value]
        else:
            raise ValueError("bad indicator " + repr(indicator))
        command = [indicator] + remainder
    elif top:
        raise ValueError("top level command must be a list " + repr(command))
    # Non-lists are untranslated (but should be JSON compatible).
    return command


class CommandMaker(object):

    """
    Superclass for command proxy objects.
    Directly implements top level objects like "window" and "element".
    """

    top_level_names = "window element".split()

    def __init__(self, name="window"):
        assert name in self.top_level_names
        self.name = name
    
    def _cmd(self):
        return [self.name]

    def __getattr__(self, name):
        return MethodMaker(self, name)

    def _set(self, name, value):
        return SetMaker(self, name, value)

    def __call__(self, *args):
        raise ValueError("top level object cannot be called.")


class SetMaker(CommandMaker):

    def __init__(self, target, name, value):
        self.target = target
        self.name = name
        self.value = value

    def _cmd(self):
        #target = validate_command(self.target, False)
        #@value = validate_command(self.value, False)
        target = self.target
        value = self.value
        return ["set", target, self.name, value]

class MethodMaker(CommandMaker):

    def __init__(self, target, name):
        self.target = target
        self.name = name

    def _cmd(self):
        #target = validate_command(self.target, False)
        target = self.target
        return ["get", target, self.name]

    def __call__(self, *args):
        return CallMaker("method", self.target, self.name, *args)


class CallMaker(CommandMaker):

    def __init__(self, kind, *args):
        self.kind = kind
        self.args = quoteLists(args)

    def _cmd(self):
        return [self.kind] + validate_commands(self.args, False)

class LiteralMaker(CommandMaker):

    indicators = {types.DictType: "dict", types.ListType: "list"}

    def __init__(self, thing):
        self.thing = thing

    def _cmd(self):
        thing = self.thing
        ty = type(thing)
        indicator = self.indicators.get(type(thing))
        if indicator:
            if ty is types.ListType:
                thing_cmd = validate_commands(thing, False)
            elif ty is types.DictType:
                thing_cmd = {}
                for key in thing:
                    thing_cmd[key] = validate_command(thing[key], False)
            else:
                raise ValueError, "can't translate " + repr(ty)
            return [indicator, thing_cmd]
        return thing


def quoteLists(args):
    result = []
    for x in args:
        if type(x) is LiteralMaker.indicators:
            x = LiteralMaker(x)
        result.append(x)
    return result
