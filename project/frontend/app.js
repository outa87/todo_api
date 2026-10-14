// ====================
// JWTトークン
// ====================

let token = localStorage.getItem("token") || "";


// ====================
// ページネーション
// ====================

let currentPage = 1;

const limit = 10;


// ====================
// 新規登録
// ====================

async function register() {

    const username =
        document.getElementById("register-username").value;

    const password =
        document.getElementById("register-password").value;


    const res = await fetch("/register", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            username,
            password
        })
    });


    const data = await res.json();


    if (res.ok) {

        alert("登録成功");

    } else {

        alert(data.detail);

    }
}


// ====================
// ログイン
// ====================

async function login() {

    const username =
        document.getElementById("username").value;

    const password =
        document.getElementById("password").value;


    const res = await fetch("/login", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            username,
            password
        })
    });


    const data = await res.json();


    if (!res.ok) {

        alert(data.detail);

        return;
    }


    token = data.access_token;

    localStorage.setItem("token", data.access_token);


    alert("ログイン成功");

    currentPage = 1;

    getTodos();
}


// ====================
// Todo追加
// ====================

async function addTodo() {

    if (!token) {

        alert("ログインしてください");

        return;
    }

    const task =
        document.getElementById("task").value;

    const dueDate =
        document.getElementById("due-date").value;

    const priority =
        document.getElementById("priority").value;


    const todoData = {

        task: task,

        due_date: dueDate
            ? new Date(dueDate).toISOString()
            : null,

        priority: priority
            ? Number(priority)
            : 1
    };


    const res = await fetch("/todos", {

        method: "POST",

        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        },

        body: JSON.stringify(todoData)
    });


    const data = await res.json();


    if (!res.ok) {

        alert(data.detail || "Todoの追加に失敗しました");

        return;
    }


    alert("Todoを追加しました");


    document.getElementById("task").value = "";
    document.getElementById("due-date").value = "";
    document.getElementById("priority").value = "";

    currentPage = 1;

    getTodos();
}


// ====================
// Todo一覧取得
// ====================

function resetPageAndGetTodos(){

    currentPage = 1;
    
    getTodos();
}

async function getTodos() {

    if (!token) {

        alert("ログインしてください");

        return;
    }


    const done =
        document.getElementById("done-filter").value;

    const priority =
        document.getElementById("priority-filter").value;

    const sortBy =
        document.getElementById("sort-by").value;

    
    // ====================
    // skipを計算
    // ====================

    const skip = (currentPage - 1) * limit;


    // ====================
    // URLパラメータを作る
    // ====================

    const params = new URLSearchParams();


    if (done !== "") {

        params.append("done", done);
    }


    if (priority !== "") {

        params.append("priority", priority);
    }


    if (sortBy !== "") {

        params.append("sort_by", sortBy);
    }


    params.append("skip", skip);

    // 次のページが存在するか確認するため
    // 表示件数より1件多く取得する

    params.append("limit", limit + 1);


    const query =
        params.toString();


    const url = "/todos?" + query;


    const res = await fetch(url, {

        headers: {
            "Authorization": "Bearer " + token
        }
    });


    const data = await res.json();


    if (!res.ok) {

        alert(data.detail || "Todoの取得に失敗しました");

        return;
    }


    // ====================
    // 次のページがあるか確認
    // ====================

    const hasNextPage = data.length > limit;


    // 画面に表示するのは最大10件
    
    const todosToDisplay = data.slice(0, limit);


    // ====================
    // Todo一覧を表示
    // ====================

    const list =
        document.getElementById("todo-list");


    list.innerHTML = "";


    todosToDisplay.forEach(todo => {

        const li =
            document.createElement("li");


        // ====================
        // Todo情報
        // ====================

        const taskText =
            document.createElement("span");


        taskText.innerText =
            todo.task
            + " / done: "
            + todo.done
            + " / priority: "
            + todo.priority;


        li.appendChild(taskText);


        // ====================
        // 期限表示
        // ====================

        if (todo.due_date) {

            const dueText =
                document.createElement("span");


            const date =
                new Date(todo.due_date);


            dueText.innerText =
                " / due: "
                + date.toLocaleString();


            li.appendChild(dueText);
        }


        // ====================
        // 完了・未完了ボタン
        // ====================

        const updateButton =
            document.createElement("button");


        updateButton.innerText =
            todo.done
                ? "未完了に戻す"
                : "完了にする";


        updateButton.onclick =
            function () {

                updateTodo(
                    todo.id,
                    !todo.done
                );

            };


        li.appendChild(updateButton);


        // ====================
        // 削除ボタン
        // ====================

        const deleteButton =
            document.createElement("button");


        deleteButton.innerText =
            "削除";


        deleteButton.onclick =
            function () {

                deleteTodo(todo.id);

            };


        li.appendChild(deleteButton);


        // ====================
        // Todoを画面に追加
        // ====================

        list.appendChild(li);

    });


    // ====================
    // ページ番号を表示
    // ====================

    document.getElementById("page-number").innerText =
        currentPage;


    // ====================
    // 次のページボタン
    // ====================

    const nextButton =
        document.querySelector(
            'button[onclick="nextPage()"]'
        );

    
    nextButton.disabled = !hasNextPage;


    // ====================
    // 前のページボタン
    // ====================

    const previousButton =
        document.querySelector(
            'button[onclick="previousPage()"]'
        );


    previousButton.disabled = currentPage === 1;
}


// ====================
// 次のページ
// ====================

function nextPage() {

    currentPage++;

    getTodos();
}


// ====================
// 前のページ
// ====================

function previousPage() {

    if (currentPage === 1) {

        return;
    }


    currentPage--;

    getTodos();
}


// ====================
// Todo更新
// ====================

async function updateTodo(todoId, done) {

    const res = await fetch(
        "/todos/" + todoId + "?done=" + done,
        {
            method: "PATCH",

            headers: {
                "Authorization": "Bearer " + token
            }
        }
    );

    
    if (!res.ok) {
        
        const data = await res.json();

        alert(data.detail || "Todoの更新に失敗しました");

        return;
    }


    getTodos();
}


// ====================
// Todo削除
// ====================

async function deleteTodo(todoId) {

    const res = await fetch(
        "/todos/" + todoId,
        {
            method: "DELETE",

            headers: {
                "Authorization": "Bearer " + token
            }
        }
    );

    
    if (!res.ok) {
        
        const data = await res.json();
        
        alert(data.detail || "Todoの削除に失敗しました");
        
        return;
    }
    
    
    getTodos();
}