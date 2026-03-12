class Task:

    def __init__(self, title):
        self.title = title
        self.done = False

def load_tasks(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            tasks = []
            
            for line in f:
                title, done = line.strip().sprit(",")
                tasks.append(Task(title, done == "True"))
            return tasks
    
    except FileNotFoundError:
        return []
    
def add_task(tasks, title):
    task = Task(title)
    tasks.append(task)
    print(f"タスク{title} を追加しました。")

def show_tasks(tasks):
    if not tasks:
        print("タスクはありません。")
    
    for i, task in enumerate(tasks, 1):
        status = "完了" if task.done else "未完成"
        print(f"{i}, {task.title} [{status}]")

def comlete_task(tasks, index):
    if 0 <= index < len(tasks):
        tasks[index].done = True
        print(f"タスク「{tasks[index].title}」を完了にしました。")
    
    else:
        print("無効な番号です。")

def delete_task(tasks, index):
    if 0 <= index < len(tasks):
        removed = tasks.pop(index)
        print(f"タスク「{removed.title}」を削除しました。")
    
    else:
        print("無効な番号です。")

def save_tasks(tasks, filename):
    with open(filename, "w", encoding="utf-8") as f:
        for task in tasks:
            f.write(f"{task.title}, {task.done}\n")
    
    print("タスクを保存しました。")

def menu(tasks, filename):
    while True:
        print("\n--- メニュー ---")
        print("1: タスク追加")
        print("2: タスク表示")
        print("3: タスク完了")
        print("4: タスク削除")
        print("5: 保存して終了")

        choice = input("番号を入力してください: ")

        if choice == "1":
            title = input("タスクを入力: ")
            add_task(tasks, title)
        
        elif choice == "2":
            show_tasks(tasks)

        elif choice == "3":
            show_tasks(tasks)
            index = int(input("完了するタスク番号: ")) - 1
            comlete_task(tasks, index)

        elif choice == "4":
            show_tasks(tasks)
            index = int(input("削除するタスク番号: "))
            delete_task(tasks, index)

        elif choice == "5":
            save_tasks(tasks, filename)
            print("終了します。")
            break
        
        else:
            print("無効な入力です。")

filename = "tasks.txt"
tasks = load_tasks(filename)
menu(tasks, filename)
#  Git練習