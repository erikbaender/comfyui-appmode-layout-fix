import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "appmode.layout.fix",

    async setup() {
        const id = "appmode-layout-fix";

        if (document.getElementById(id)) {
            return;
        }

        const style = document.createElement("style");
        style.id = id;
        style.textContent = `
            nav.side-tool-bar-container + .p-splitter {
                min-width: 0 !important;
            }
        `;

        document.head.appendChild(style);
    },
});
