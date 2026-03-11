with open("test.txt", "w", encoding="utf-8") as f:

    f.write("Taro,16\n")
    f.write("Jiro,20\n")
    f.write("Hanako,18\n")

with open("test.txt", "r", encoding="utf-8") as f:

    data = f.read()
    print(data)

with open("test.txt", "r", encoding="utf-8") as f:

    lines = f.readlines()

for line in lines:
    name, age = line.strip().split(",") # strip()は余計な改行や空白を消す　.split(",")は区切ってリストに分ける
    age = int(age)
    print(f"{name}は {age}歳です")


