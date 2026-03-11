import json

def menu():
    print("=== 人物管理アプリ ===")
    print("1: 人物追加")
    print("2: 一覧表示")
    print("3: 削除")
    print("4: 保存")
    print("5: 終了")

def add_person(people):
    name = input("名前を入力してください: ")
    
    while True:
        try:
            age = int(input("年齢を入力してください: "))
            break
        except ValueError:
            print("数字で入力してください")

    person = {"name": name, "age": age}
    people.append(person)
    print(f"{name} さんを追加しました")

def show_people(people):
    if not people:
        print("まだ人物が登録されていません")
        return
    
    for i, person in enumerate(people, start=1):
        status = "成人" if person["age"] >= 18 else "未成年"
        print(f"{i}, {person["name"]} ({person["age"]}) → {status}")

def delete_person(people):
    show_people(people)
    
    try:
        num = input("削除する番号を入力してください: ")

        if 1 <= num <= len(people):
            people.pop(num - 1)
            print("削除しました")
            
        else:   
            print("その番号は登録されていません")

    except ValueError:
        print("数字を入力してください")

def save_people(people):
    with open("people.json", "w", encoding="utf-8") as file:
        json.dump(people, file, ensure_asicc=False, indent=2)

def load_people():
    try:
        with open("people.json", "r", encoding="utf-8") as file:
            return json.load(file)

    except FileNotFoundError:
        return []

people = load_people()

while True:
    menu()
    choice = input("番号を入力してください: ")

    if choice == "1":
        add_person(people)

    elif choice == "2":
        show_people(people)

    elif choice == "3":
        delete_person(people)

    elif choice == "4":
        save_people(people)

    elif choice == "5":
        break

    else:
        print("無効な番号です")
    
save_people(people)
