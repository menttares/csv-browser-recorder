
(() => {
    "use strict";

    const ROOT_ID = "custom-cursor-root";
    const STYLE_ID = "custom-cursor-style";

    let cursorRoot = null;
    let cursorArrow = null;
    let cursorHighlight = null;

    
    function initializeCursor() {
        if (!document.documentElement) {
            return false;
        }

        
        if (document.getElementById(ROOT_ID)) {
            return true;
        }

        // Внедряем CSS
        const style = document.createElement("style");
        style.id = STYLE_ID;
        style.textContent = window.__CURSOR_CSS__ || "";

        (document.head || document.documentElement).appendChild(style);

        // Создаём контейнер
        cursorRoot = document.createElement("div");
        cursorRoot.id = ROOT_ID;

        // Жёлтая подсветка
        cursorHighlight = document.createElement("div");
        cursorHighlight.className = "custom-cursor-highlight";

        // SVG-стрелка
        cursorArrow = document.createElement("div");
        cursorArrow.className = "custom-cursor-arrow";

        cursorArrow.innerHTML = `
            <svg
                width="32"
                height="32"
                viewBox="0 0 32 32"
                xmlns="http://www.w3.org/2000/svg"
            >
                <path
                    d="M2 1 L2 27 L9 20 L14 30 L19 28 L14 18 L25 18 Z"
                    fill="white"
                    stroke="black"
                    stroke-width="1.7"
                    stroke-linejoin="round"
                />
            </svg>
        `;

        cursorRoot.appendChild(cursorHighlight);
        cursorRoot.appendChild(cursorArrow);

        document.documentElement.appendChild(cursorRoot);

        return true;
    }

    // Обновление положения курсора
    function moveCursor(x, y) {
        if (!cursorRoot) return;

        cursorArrow.style.transform =
            `translate3d(${x}px, ${y}px, 0)`;

        cursorHighlight.style.transform =
            `translate3d(${x - 32}px, ${y - 32}px, 0)`;
    }

    // Анимация клика
    function showRipple(x, y) {
        if (!cursorRoot) return;

        const ripple = document.createElement("div");

        ripple.className = "cursor-ripple";
        ripple.style.left = `${x}px`;
        ripple.style.top = `${y}px`;

        ripple.addEventListener("animationend", () => {
            ripple.remove();
        }, { once: true });

        cursorRoot.appendChild(ripple);
    }

    // Инициализация даже до создания DOM
    if (!initializeCursor()) {
        const observer = new MutationObserver(() => {
            if (initializeCursor()) {
                observer.disconnect();
            }
        });

        observer.observe(document, {
            childList: true,
            subtree: true
        });
    }

    // Отслеживание движения мыши
    document.addEventListener("pointermove", (event) => {
        if (!cursorRoot) {
            initializeCursor();
        }

        moveCursor(event.clientX, event.clientY);

    }, { passive: true });

    // при нажатии
    document.addEventListener("click", (event) => {
        showRipple(event.clientX, event.clientY);

    }, true);

})();
