import yaml

class ISA:
    def __init__(self, path):
        with open(path) as f:
            self.spec = yaml.safe_load(f)

    def instruction(self, mnemonic):
        return self.spec["instructions"][mnemonic]
