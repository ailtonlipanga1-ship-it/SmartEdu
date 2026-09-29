const sidebar = document.getElementById("sidebar");
const mobileMenu = document.getElementById("mobileMenu");
const sidebarBackdrop = document.getElementById("sidebarBackdrop");

const commandOverlay = document.getElementById("commandOverlay");
const commandInput = document.getElementById("commandInput");
const globalSearch = document.getElementById("globalSearch");

const sidebarCollapse = document.getElementById("sidebarCollapse");


function toggleSidebar() {
    if (!sidebar) {
        return;
    }

    sidebar.classList.toggle("open");
    sidebarBackdrop?.classList.toggle("active");
}


function closeSidebar() {
    sidebar?.classList.remove("open");
    sidebarBackdrop?.classList.remove("active");
}


mobileMenu?.addEventListener(
    "click",
    toggleSidebar
);


sidebarBackdrop?.addEventListener(
    "click",
    closeSidebar
);


sidebarCollapse?.addEventListener(
    "click",
    () => {
        document
            .getElementById("appShell")
            ?.classList.toggle("sidebar-collapsed");
    }
);


function openCommandPalette() {
    if (!commandOverlay) {
        return;
    }

    commandOverlay.classList.add("active");
    commandOverlay.setAttribute(
        "aria-hidden",
        "false"
    );

    setTimeout(
        () => commandInput?.focus(),
        50
    );
}


function closeCommandPalette() {
    if (!commandOverlay) {
        return;
    }

    commandOverlay.classList.remove("active");
    commandOverlay.setAttribute(
        "aria-hidden",
        "true"
    );

    if (commandInput) {
        commandInput.value = "";
    }
}


globalSearch?.addEventListener(
    "click",
    openCommandPalette
);


commandOverlay?.addEventListener(
    "click",
    (event) => {
        if (event.target === commandOverlay) {
            closeCommandPalette();
        }
    }
);


document.addEventListener(
    "keydown",
    (event) => {
        if (
            (event.ctrlKey || event.metaKey) &&
            event.key.toLowerCase() === "k"
        ) {
            event.preventDefault();
            openCommandPalette();
        }

        if (event.key === "Escape") {
            closeCommandPalette();
            closeSidebar();
        }
    }
);


document
    .querySelectorAll(".flash-close")
    .forEach(
        (button) => {
            button.addEventListener(
                "click",
                () => {
                    button
                        .closest(".flash")
                        ?.remove();
                }
            );
        }
    );


document
    .querySelectorAll(".command-item")
    .forEach(
        (item) => {
            item.addEventListener(
                "click",
                closeCommandPalette
            );
        }
    );


window.addEventListener(
    "resize",
    () => {
        if (window.innerWidth > 900) {
            closeSidebar();
        }
    }
);