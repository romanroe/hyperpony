document.body.addEventListener('htmx:configRequest', function (evt) {
    let els = document.querySelectorAll("[__hyperpony_client_state__]");
    els.forEach(function (el) {
        let id = el.getAttribute("__hyperpony_client_state__");
        let data = Alpine.$data(el);
        let client_state = data["client_state"];
        let client_to_server_excludes = data["client_to_server_excludes"];

        let filtered_client_state = {};
        Object.keys(client_state).forEach(function (key) {
            if (!client_to_server_excludes.includes(key)) {
                filtered_client_state[key] = client_state[key];
            }
        });

        evt.detail.parameters["__hyperpony_cs__" + id] = filtered_client_state;
    });
});
