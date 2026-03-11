people = []

try:
    with open("peopel.txt", "r", encoding="utf-8") as f:
        people = f.readlines()
except FileNotFoundError:
    pass

while True:
    print("1: 追加")
    print("2: 一覧")
    print("3: 削除")
    print("4: 保存")
    print("5: 終了")

    choice = input("選択: ")

    if choice == "1":
        name = input("名前: ")

        try:
            age = int(input("年齢: "))
        except ValueError:
            print("年齢は数字で。 ")
            continue

        people.append(f"{name},{age}\n")

    elif choice == "2":
        for i, person in enumerate(people):
            print(i+1, person.strip())

    elif choice == 3:
        num = int(input("削除番号: "))
        del people[num-1]

    elif choice == "4":
        with open("people.txt", "w", encoding="uft-8") as f:
            f.writelines(people)
        print("保存しました。 ")

    elif choice == "5":
        break

