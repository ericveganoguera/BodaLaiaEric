const personesInput = document.getElementById("persones");
const container = document.getElementById("acompanyants");
const radioSi = document.getElementById("assistencia-si");
const radioNo = document.getElementById("assistencia-no");
const campsAssistencia = document.querySelector(".camps-assistencia");

function crearCampos(num) {
    container.innerHTML = "";

    const noAssistiran = radioNo.checked;

    num = Math.max(1, Math.min(8, num || 1));

    for (let i = 2; i <= num; i++) {
        const div = document.createElement("div");
        div.className = "acompanyant";

        let html = `
        <h4>Persona ${i}</h4>

        <div class="form-row" >
            <label>Nom i cognoms</label>
            <input type="text" name="NomiCognoms_${i}" required>
        </div>
        `;

        if (!noAssistiran) {
            html += `
            <div class="form-row">
            <label>Àpat del banquet</label>
            <select name="ApatBanquet_${i}" required>
                <option value="">Selecciona una opció</option>
                <option value="Menu general">Menú general</option>
                <option value="Menu vegetaria">Menú vegetarià</option>
                <option value="Menu vega">Menú vegà</option>
                <option value="Menu infantil">Menú infantil</option>
                <option value="Altres necessitats">Altres necessitats</option>
            </select>
            </div>

            <div class="form-row"> 
            <label>Al·lèrgies, intoleràncies i/o altres necessitats</label>
            <textarea name="Alergies_${i}" rows="2" placeholder="Expliqueu-nos qualsevol detall important"></textarea>
            </div>

            <div class="form-row">
              <label for="telefonalergies">En cas de tenir al·lèrgies, intoleràncies i/o altres necessitats, deixans un teléfon de contacte</label>
              <input id="telefonalergies" name="TelefonAlergies_${i}" type="text" placeholder="Telèfon">
            </div>

            <div class="form-row" style="margin-bottom: 30px;">
            <label>Quina cançó creus que no pot faltar?</label>
            <textarea name="Cancion_${i}" rows="1" placeholder="La teva cançó preferida"></textarea>
            </div>
        `;
        }

        div.innerHTML = html;
        container.appendChild(div);
    }
}

personesInput.addEventListener("input", () => {
    let num = parseInt(personesInput.value || 1);

    if (num < 1) num = 1;
    if (num > 8) num = 8;

    crearCampos(num);
});

document.querySelector("form").addEventListener("submit", function () {
    const name = document.getElementById("nom").value;
    document.getElementById("subject").value = "Nova confirmacio d'assistencia E&L - " + name;
});

function toggleAssistencia() {
    const noAssistiran = radioNo.checked;

    campsAssistencia.style.display = noAssistiran ? "none" : "block";

    // SOLO desactivar required cuando NO asisten
    campsAssistencia.querySelectorAll("[required]").forEach(el => {
        el.dataset.wasRequired = "1";
        if (noAssistiran) {
            el.removeAttribute("required");
        } else {
            el.setAttribute("required", "true");
        }
    });

    crearCampos(parseInt(personesInput.value || 1));
}

radioSi.addEventListener("change", toggleAssistencia);
radioNo.addEventListener("change", toggleAssistencia);