class Person:
    planet = "Earth"

    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def __str__(self):
        return f"{self.name} ({self.age})"

    def introduce(self):
        print (f"僕は{self.name}、 {self.age}歳 ")
    
    def is_adult(self):
        return self.age >= 18
    
people = []

people.append(Person("Taro", 16))
people.append(Person("Jiro", 20))
people.append(Person("Hanako", 18))

for person in people:
    status = "成人" if person.is_adult() else "未成年"
    print(f"{person} → {status}")


    

        