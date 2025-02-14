///////////////////////////////////////////////////////////////////////////////
// csrf token
///////////////////////////////////////////////////////////////////////////////

window.getCsrfTokenCookie = function () {
    const name = "csrftoken";
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue ?? "";
}

function addCsrfTokenHeader(event) {
    event.detail.headers['X-CSRFToken'] = getCsrfTokenCookie();
}

document.body.addEventListener('htmx:configRequest', addCsrfTokenHeader);
document.body.addEventListener("fetch:beforeRequest", addCsrfTokenHeader);


///////////////////////////////////////////////////////////////////////////////
// preserve_on_outer_swap
///////////////////////////////////////////////////////////////////////////////

let requests = new Map()

function beforeSwap(event) {
    // console.log(event.type);
    let target = event.detail.target;
    let keeps = Array.from(target.querySelectorAll("[hp-preserve-on-outer-swap=enable]"));
    // console.log("keeps", keeps);
    requests.set(event.detail.xhr, keeps);
}

function afterSwap(event) {
    // console.log(event.type);
    let keeps = requests.get(event.detail.xhr);
    if (keeps) {
        let swappedIn = event.detail.elt;
        for (let p of keeps) {
            let toReplace = swappedIn.querySelector("[id=" + p.id + "]");
            if (toReplace) {
                let hpAttr = toReplace.attributes["hp-preserve-on-outer-swap"];
                if (hpAttr && hpAttr.value === "close") {
                    continue;
                }
                // console.log("replacing", toReplace, "\n__WITH__\n", p);
                toReplace.after(p);
                toReplace.remove();
            }
        }
    }
    requests.delete(event.detail.xhr);
}

document.body.addEventListener("htmx:beforeSwap", beforeSwap);
document.body.addEventListener("htmx:afterSwap", afterSwap);
document.body.addEventListener("htmx:oobBeforeSwap", beforeSwap);
document.body.addEventListener("htmx:oobAfterSwap", afterSwap);


///////////////////////////////////////////////////////////////////////////////
// client state
///////////////////////////////////////////////////////////////////////////////

document.body.addEventListener('htmx:configRequest', function (evt) {
    if (evt.detail.verb === "get") {
        return;
    }

    let els = document.querySelectorAll("[__hyperpony_client_state__]");
    els.forEach(function (el) {
        let id = el.getAttribute("__hyperpony_client_state__");
        let data = Alpine.$data(el);
        let client_state = data["client_state"];
        let client_to_server_includes = data["client_to_server_includes"];

        let filtered_client_state = {};
        Object.keys(client_state).forEach(function (key) {
            if (client_to_server_includes.includes(key)) {
                filtered_client_state[key] = client_state[key];
            }
        });

        evt.detail.parameters["__hyperpony_cs__" + id] = filtered_client_state;
    });
});

