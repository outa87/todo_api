// ====================
// 設定・状態
// ====================

const PAGE_SIZE = 10;
const TOKEN_KEY = "token";

let token = localStorage.getItem(TOKEN_KEY) || "";
let currentPage = 1;


// ====================
// ヘルパー
// ====================

const $ = (id) => document.getElementById(id);


// FastAPIの detail は文字列のことも、422のときは配列のこともある
function formatError(detail, fallback) {
    if (typeof detail === "string") {
        return detail;
    }

    if (Array.isArray(detail)) {
        return detail.map((e) => e.msg).join("\n");
    }

    return fallback;
}


// サーバーは日時をタイムゾーンなし(UTC)で返すので、UTCとして解釈する
function parseServerDate(value) {
    const hasTimezone = /([zZ]|[+-]\d{2}:?\d{2})$/.test(value);

    return new Date(hasTimezone ? value : value + "Z");
}


async function apiFetch(path, { method = "GET", body, auth = true } = {}) {
    const headers = {};

    if (body !== undefined) {
        headers["Content-Type"] = "application/json";
    }

    if (auth) {
        headers["Authorization"] = "Bearer " + token;
    }

    const res = await fetch(path, {
        method,
        headers,
        body: body !== undefined ? JSON.stringify(body) : undefined,
    });

    // 204 などボディがない場合に備える
    let data = null;
    try {
        data = await res.json();
    } catch {
        data = null;
    }

    // トークン切れ → ログアウト扱いにする
    if (auth && res.status === 401) {
        clearSession();
        alert("ログインの有効期限が切れました。もう一度ログインしてください");
    }

    return { ok: res.ok, status: res.status, data };
}


function requireLogin() {
    if (!token) {
        alert("ログインしてください");
        return false;
    }

    return true;
}


function setToken(newToken) {
    token = newToken;
    localStorage.setItem(TOKEN_KEY, newToken);
    updateAuthUi();
}


function clearSession() {
    token = "";
    localStorage.removeItem(TOKEN_KEY);
    currentPage = 1;
    $("todo-list").innerHTML = "";
    updateAuthUi();
}


function updateAuthUi() {
    $("logout-button").hidden = !token;
}


// ====================
// 新規登録・ログイン・ログアウト
// ====================

async function register() {
    const username = $("register-username").value;
    const password = $("register-password").value;

    const { ok, data } = await apiFetch("/register", {
        method: "POST",
        body: { username, password },
        auth: false,
    });

    if (!ok) {
        alert(formatError(data?.detail, "登録に失敗しました"));
        return;
    }

    $("register-username").value = "";
    $("register-password").value = "";

    alert("登録成功");
}


async function login() {
    const username = $("username").value;
    const password = $("password").value;

    const { ok, data } = await apiFetch("/login", {
        method: "POST",
        body: { username, password },
        auth: false,
    });

    if (!ok) {
        alert(formatError(data?.detail, "ログインに失敗しました"));
        return;
    }

    setToken(data.access_token);
    $("password").value = "";

    alert("ログイン成功");

    currentPage = 1;
    getTodos();
}


function logout() {
    clearSession();
}


// ====================
// Todo追加
// ====================

async function addTodo() {
    if (!requireLogin()) {
        return;
    }

    const task = $("task").value;
    const dueDate = $("due-date").value;
    const priority = $("priority").value;

    const { ok, data } = await apiFetch("/todos", {
        method: "POST",
        body: {
            task,
            due_date: dueDate ? new Date(dueDate).toISOString() : null,
            priority: priority ? Number(priority) : 1,
        },
    });

    if (!ok) {
        // 401は apiFetch 側で通知済み
        if (token) {
            alert(formatError(data?.detail, "Todoの追加に失敗しました"));
        }
        return;
    }

    alert("Todoを追加しました");

    $("task").value = "";
    $("due-date").value = "";
    $("priority").value = "";

    currentPage = 1;
    getTodos();
}


// ====================
// Todo一覧
// ====================

function resetPageAndGetTodos() {
    currentPage = 1;
    getTodos();
}


function buildTodoQuery() {
    const params = new URLSearchParams();

    const done = $("done-filter").value;
    const priority = $("priority-filter").value;
    const sortBy = $("sort-by").value;

    if (done !== "") {
        params.append("done", done);
    }

    if (priority !== "") {
        params.append("priority", priority);
    }

    if (sortBy !== "") {
        params.append("sort_by", sortBy);
    }

    params.append("skip", (currentPage - 1) * PAGE_SIZE);

    // 次のページがあるか判定するため、表示件数より1件多く取得する
    params.append("limit", PAGE_SIZE + 1);

    return params.toString();
}


function createTodoItem(todo) {
    const li = document.createElement("li");

    // Todo情報
    const taskText = document.createElement("span");
    taskText.innerText = `${todo.task} / done: ${todo.done} / priority: ${todo.priority}`;
    li.appendChild(taskText);

    // 期限
    if (todo.due_date) {
        const dueText = document.createElement("span");
        dueText.innerText = " / due: " + parseServerDate(todo.due_date).toLocaleString();
        li.appendChild(dueText);
    }

    // 完了・未完了ボタン
    const updateButton = document.createElement("button");
    updateButton.innerText = todo.done ? "未完了に戻す" : "完了にする";
    updateButton.onclick = () => updateTodo(todo.id, !todo.done);
    li.appendChild(updateButton);

    // 削除ボタン
    const deleteButton = document.createElement("button");
    deleteButton.innerText = "削除";
    deleteButton.onclick = () => deleteTodo(todo.id);
    li.appendChild(deleteButton);

    return li;
}


async function getTodos() {
    if (!requireLogin()) {
        return;
    }

    const { ok, data } = await apiFetch("/todos?" + buildTodoQuery());

    if (!ok) {
        if (token) {
            alert(formatError(data?.detail, "Todoの取得に失敗しました"));
        }
        return;
    }

    // 最後のページの最後の1件を消した場合などは、ひとつ前のページに戻る
    if (data.length === 0 && currentPage > 1) {
        currentPage--;
        getTodos();
        return;
    }

    const hasNextPage = data.length > PAGE_SIZE;
    const todosToDisplay = data.slice(0, PAGE_SIZE);

    const list = $("todo-list");
    list.innerHTML = "";
    todosToDisplay.forEach((todo) => list.appendChild(createTodoItem(todo)));

    $("page-number").innerText = currentPage;
    $("next-button").disabled = !hasNextPage;
    $("prev-button").disabled = currentPage === 1;
}


// ====================
// ページ移動
// ====================

function nextPage() {
    currentPage++;
    getTodos();
}


function previousPage() {
    if (currentPage === 1) {
        return;
    }

    currentPage--;
    getTodos();
}


// ====================
// Todo更新・削除
// ====================

async function updateTodo(todoId, done) {
    const { ok, data } = await apiFetch(`/todos/${todoId}?done=${done}`, {
        method: "PATCH",
    });

    if (!ok) {
        if (token) {
            alert(formatError(data?.detail, "Todoの更新に失敗しました"));
        }
        return;
    }

    getTodos();
}


async function deleteTodo(todoId) {
    const { ok, data } = await apiFetch(`/todos/${todoId}`, {
        method: "DELETE",
    });

    if (!ok) {
        if (token) {
            alert(formatError(data?.detail, "Todoの削除に失敗しました"));
        }
        return;
    }

    getTodos();
}


// ====================
// 初期表示
// ====================

updateAuthUi();

// ログイン済み（トークンが残っている）ならそのまま一覧を表示
if (token) {
    getTodos();
}
