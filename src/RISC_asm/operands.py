

class Register:
    def __init__(self, name: str):
        self.index = int(name[1:])

class Immediate:
    def __init__(self, value: str):
        self.value =int(value, base = 2)

class Label:
    def __init__(self, name):
        self.name = name
        self.address = None
