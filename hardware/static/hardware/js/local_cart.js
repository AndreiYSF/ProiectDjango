const LOCAL_CART_KEY = "local_cart";

function getLocalCart() {
    try {
        return JSON.parse(localStorage.getItem(LOCAL_CART_KEY) || "{}");
    } catch (err) {
        return {};
    }
}

function saveLocalCart(cart) {
    localStorage.setItem(LOCAL_CART_KEY, JSON.stringify(cart));
}

function updateLocalCart(action, data) {
    const cart = getLocalCart();
    const id = String(data.id || "");
    if (!id) {
        return;
    }
    const current = cart[id] || {
        id,
        name: data.name || "",
        price: Number(data.price || 0),
        qty: 0,
    };

    if (action === "add") {
        current.qty += data.qty;
    } else if (action === "inc") {
        current.qty += 1;
    } else if (action === "dec") {
        current.qty -= 1;
    } else if (action === "set") {
        current.qty = data.qty;
    } else if (action === "remove") {
        delete cart[id];
        saveLocalCart(cart);
        return;
    }

    if (current.qty <= 0) {
        delete cart[id];
    } else {
        cart[id] = current;
    }
    saveLocalCart(cart);
}

function parseQty(form) {
    const input = form.querySelector("input[name='qty']");
    if (!input) {
        return 1;
    }
    const value = parseInt(input.value, 10);
    if (Number.isNaN(value) || value <= 0) {
        return 1;
    }
    return value;
}

function bindCartForms() {
    document.querySelectorAll("form[data-cart-action]").forEach((form) => {
        form.addEventListener("submit", () => {
            const action = form.dataset.cartAction;
            const data = {
                id: form.dataset.productId,
                name: form.dataset.productName,
                price: parseFloat(form.dataset.productPrice || "0"),
                qty: parseQty(form),
            };
            updateLocalCart(action, data);
        });
    });
}

function renderLocalCart(sortBy = "name") {
    const body = document.getElementById("local-cart-body");
    if (!body) {
        return;
    }
    const cart = getLocalCart();
    const items = Object.values(cart);
    if (!items.length) {
        body.innerHTML = "<tr><td colspan=\"4\">Coșul local este gol.</td></tr>";
    }
    if (sortBy === "price") {
        items.sort((a, b) => a.price - b.price);
    } else {
        items.sort((a, b) => a.name.localeCompare(b.name));
    }
    if (items.length) {
        body.innerHTML = "";
    }
    let total = 0;
    let count = 0;
    items.forEach((item) => {
        const subtotal = item.price * item.qty;
        total += subtotal;
        count += item.qty;
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${item.name}</td>
            <td>${item.price.toFixed(2)} lei</td>
            <td>${item.qty}</td>
            <td>${subtotal.toFixed(2)} lei</td>
        `;
        body.appendChild(row);
    });

    const totalEl = document.getElementById("local-cart-total");
    const countEl = document.getElementById("local-cart-count");
    if (totalEl) {
        totalEl.textContent = `${total.toFixed(2)} lei`;
    }
    if (countEl) {
        countEl.textContent = `${count} produse`;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    bindCartForms();
    const buttons = document.querySelectorAll("[data-sort]");
    if (buttons.length) {
        buttons.forEach((btn) => {
            btn.addEventListener("click", () => {
                renderLocalCart(btn.dataset.sort);
            });
        });
        renderLocalCart("name");
    }
});
