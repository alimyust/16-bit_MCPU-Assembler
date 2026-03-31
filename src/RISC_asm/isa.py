import yaml


class ISA:
    def __init__(self, path):
        with open(path) as f:
            self.spec = yaml.safe_load(f)

    def instruction(self, mnemonic):
        return self.spec["instructions"][mnemonic]

    def format_fields(self, fmt_name):
        return self.spec["formats"][fmt_name]["fields"]

    @property
    def register_names(self):
        return self.spec["registers"]["names"]

    @property
    def conditions(self):
        return self.spec.get("conditions", {})

    @property
    def word_size(self):
        return self.spec["word_size"]

    @property
    def register_fields(self):
        return [field for field in ("rd", "rn", "rm") if field in self._all_fields]

    def default_condition(self):
        if "AL" in self.conditions:
            return self.conditions["AL"]
        cond_width = self._all_fields.get("cond")
        if cond_width is None:
            return 0
        return (1 << cond_width) - 1

    @property
    def _all_fields(self):
        fields = {}
        for fmt in self.spec["formats"].values():
            fields.update(fmt["fields"])
        return fields
