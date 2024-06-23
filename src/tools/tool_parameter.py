class ToolParameter:

    def __init__(self, name: str, description: str, type: str, required: bool = False, enum: list = None):
        self._name = name
        self._description = description
        self._type = type
        self._required = required
        self._enum = enum

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def type(self):
        return self._type

    @property
    def required(self):
        return self._required

    @property
    def enum(self):
        return self._enum

    @property
    def json_definition(self):
        definition = {
                "description": self.description,
                "type": self.type
        }
        if self.enum:
            definition["enum"] = self.enum
        return definition

