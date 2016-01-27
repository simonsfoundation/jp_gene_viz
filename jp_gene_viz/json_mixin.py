
"""
Helper mixin to allow controlled serialization/deserialization
of objects t/from json.
"""

import json


class JsonMixin(object):

    # sequence of json compatible atts to encode
    json_atts = []

    # dictionary of json convertible object to encode mapped to constructors.
    json_objects = {}

    def to_json_value(self):
        "Encode object as json compatible value."
        result = {}
        # store json compatible values specified
        for att in self.json_atts:
            result[att] = getattr(self, att)
        # encode specified objects
        for att in self.json_objects:
            obj = getattr(self, att)
            klass = self.json_objects[att]
            result[att] = None
            if obj is not None:
                result[att] = klass.to_json_value(obj)
        return result

    def from_json_value(self, json_value):
        "Load object attributes from json compatible value"
        for att in self.json_atts:
            json_encoding = json_value.get(att)
            if json_encoding is not None:
                setattr(self, att, json_value.get(att))
        for att in self.json_objects:
            klass = self.json_objects[att]
            inst = klass()
            json_encoding = json_value.get(att)
            if json_encoding is not None:
                inst = inst.from_json_value(json_encoding)
                setattr(self, att, inst)
        return self

    def as_json(self):
        "Convert to json string."
        return json.dumps(self.to_json_value())

    def load_json(self, json_text):
        "Load from json string."
        self.from_json_value(json.loads(json_text))
