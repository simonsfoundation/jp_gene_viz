"""
This is a simple key/value file based archive for JSON convertible values.

It is intended to archive interactive state in IPython notebooks.

When a widget is created, assign it a key in the addenda which the
widget may use to persist its state.

    # To load addenda
    addenda.load()

    # To archive object state
    addenda.set("key_for_object", object)
    # persist the addenda
    addenda.save()

    # To resote object state (after load)
    addenda.reset(object, "key_for_object", "default_key_for_object")

    # To snap shot state for all registered Objects
    addenda.snapshot_all()

The default key can be used to initialize the object from another representation
if the object has not been archived yet.

Objects are converted to and from JSON using the json_mixin protocol.

    json_value = object.to_json_value()  # convert to JSON 
    object.from_json_value(json_value)   # load from JSON

"""

import os
import json

class Addenda(object):

    indent = 4

    def __init__(self, path):
        self.path = path
        self.load()

    def reset(self, object0, key, default_key=None):
        "Reset object state to stored state."
        json_values = self.json_values
        default_value = None
        if default_key:
            default_value = json_values.get(default_key)
        json_value = json_values.get(key, default_value)
        if json_value is not None:
            object0.from_json_value(json_value)
            self.set(key, object0, json_value)

    def forget(key):
        if key in self.json_values:
            del self.json_values[key]
        if key in self.object_values:
            del self.object_values[key]

    def set(self, key, object0, json_value=None):
        "Store object state."
        if json_value is None:
            json_value = object0.to_json_value()
        self.json_values[key] = json_value
        self.object_values[key] = object0

    def save(self):
        s = json.dumps(self.json_values, indent=self.indent, sort_keys=True)
        f = open(self.path, "w")
        f.write(s)
        f.close()

    def load(self):
        self.json_values = {}
        self.object_values = {}
        path = self.path
        if os.path.exists(path):
            s = open(path).read()
            self.json_values = json.loads(s)

    def reset_all(self):
        "Reset object states for all stored objects."
        object_values = self.object_values
        keys = list(object_values.keys())
        for key in keys:
            val = object_values[key]
            self.reset(val, key)

    def snapshot_all(self):
        "Capture all state for stored objects and save."
        object_values = self.object_values
        keys = list(object_values.keys())
        for key in keys:
            val = object_values[key]
            self.set(key, value)
        self.save()
