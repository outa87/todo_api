class Person:
    planet = "Earth"
    @classmethod
    def change_planet(cls, new_planet): # 全体
        cls.planet = new_planet

    def __init__(self, name, age): # 個人
        self.name = name
        self.age = age

    def __str__(self): # 文字列にする
        return f"{self.name} ({self.age}歳)"

    def introduce(self):
        print(f"僕は{self.name}、 {self.age}歳です")
        
    @staticmethod
    def is_adult(age): # 補助関数
        return age >= 18
    
p1 = Person("Taro", 16)
p1.introduce()

p2 = Person("Outa", 17)
p2.introduce()

print(p1)

