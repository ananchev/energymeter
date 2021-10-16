
class Test():
    d1 = {}
    d2 = {}

    def __init__(self):
        self.d1 = self.exec_init()
        print("d2 in init:")
        print(self.d2)

    def exec_init(self):
        d1 = {"manual":{"name":"anton", "age":10, "likes":["peanuts", "banana", "honey"]},
              "autmatic":{"name":"ivan","age":20, "likes":["whiskey", "coke","soda"]}}
        self.d2 = {k:v for k,v in d1.items() if k in "manual"}
        print("d2 after compr:")
        print(self.d2)
        d1.update({"manual":{"name":"skott","age":30,"likes":list()}})
        print("d2 after d1 mods:")
        print(self.d2)
        return d1
    
    def run(self):
        print("d2 in run:")
        print(self.d2)

        print("d1 in run:")
        print(self.d1)

if __name__ == '__main__':
    t = Test()
    t.run()
