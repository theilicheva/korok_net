document.addEventListener("DOMContentLoaded", () => {
    const phoneInput = document.getElementById("id_phone_num");
    if (!phoneInput) {
        return;
    }

    const formatPhone = (value) => {
        let digits = value.replace(/\D/g, "");
        if (!digits.length) {
            return "";
        }

        if (digits[0] !== "8") {
            if (digits[0] === "7") {
                digits = `8${digits.slice(1)}`;
            } else {
                digits = `8${digits}`;
            }
        }

        digits = digits.slice(0, 11);

        let result = digits.slice(0, 1);
        if (digits.length > 1) {
            result += `(${digits.slice(1, 4)}`;
        }
        if (digits.length >= 4) {
            result += ")";
        }
        if (digits.length > 4) {
            result += digits.slice(4, 7);
        }
        if (digits.length > 7) {
            result += `-${digits.slice(7, 9)}`;
        }
        if (digits.length > 9) {
            result += `-${digits.slice(9, 11)}`;
        }

        return result;
    };

    phoneInput.addEventListener("input", (event) => {
        event.target.value = formatPhone(event.target.value);
    });

    phoneInput.addEventListener("keypress", (event) => {
        if (!/\d/.test(String.fromCharCode(event.which))) {
            event.preventDefault();
        }
    });

    phoneInput.addEventListener("blur", () => {
        phoneInput.value = formatPhone(phoneInput.value);
    });
});
