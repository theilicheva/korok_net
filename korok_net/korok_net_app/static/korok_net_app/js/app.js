document.addEventListener("DOMContentLoaded", () => {
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const menuToggle = document.querySelector("[data-menu-toggle]");
    const menuPanel = document.querySelector("[data-menu-panel]");

    if (menuToggle && menuPanel) {
        menuToggle.addEventListener("click", () => {
            const isOpen = menuPanel.classList.toggle("is-open");
            menuToggle.classList.toggle("is-open", isOpen);
            menuToggle.setAttribute("aria-expanded", String(isOpen));
        });

        menuPanel.querySelectorAll("a").forEach((link) => {
            link.addEventListener("click", () => {
                menuPanel.classList.remove("is-open");
                menuToggle.classList.remove("is-open");
                menuToggle.setAttribute("aria-expanded", "false");
            });
        });
    }

    document.querySelectorAll("[data-slider]").forEach((slider) => {
        const slides = Array.from(slider.querySelectorAll(".slide"));
        if (!slides.length) {
            return;
        }

        let index = slides.findIndex((slide) => slide.classList.contains("active"));
        if (index < 0) {
            index = 0;
            slides[0].classList.add("active");
        }

        const show = (nextIndex) => {
            slides[index].classList.remove("active");
            index = (nextIndex + slides.length) % slides.length;
            slides[index].classList.add("active");
        };

        slider.querySelector("[data-slider-prev]")?.addEventListener("click", () => {
            show(index - 1);
            reset();
        });

        slider.querySelector("[data-slider-next]")?.addEventListener("click", () => {
            show(index + 1);
            reset();
        });

        let timer = null;
        const stop = () => window.clearInterval(timer);
        const reset = () => {
            stop();
            if (!prefersReducedMotion && !document.hidden) {
                timer = window.setInterval(() => show(index + 1), 4000);
            }
        };

        reset();

        document.addEventListener("visibilitychange", () => {
            if (document.hidden) {
                stop();
            } else {
                reset();
            }
        });
    });

    document.querySelectorAll(".flash").forEach((item) => {
        window.setTimeout(() => {
            item.style.opacity = "0";
            item.style.transform = "translateY(-6px)";
            item.style.transition = "opacity 0.35s ease, transform 0.35s ease";
            window.setTimeout(() => item.remove(), 400);
        }, 4200);
    });
});
