const personesInput = document.getElementById("persones");
const container = document.getElementById("acompanyants");
const radioSi = document.getElementById("assistencia-si");
const radioNo = document.getElementById("assistencia-no");
const campsAssistencia = document.querySelector(".campsAssistencia");

function crearCampos(num) {
  container.innerHTML = "";

  const noAssistiran = radioNo.checked;

  num = Math.max(1, Math.min(8, num || 1));

  for (let i = 2; i <= num; i++) {
    const div = document.createElement("div");
    div.className = "acompanyant";

    let html = `
  <hr>
  <h4>Persona ${i}</h4>

  <div class="form-row" style="margin-bottom: 20px;">
    <label>Nom i cognoms</label>
    <input type="text" name="NomiCognoms_${i}" required>
  </div>
`;

    if (!noAssistiran) {
      html += `
    <div class="form-row" style="margin-bottom: 20px;">
      <label>Apat del banquet</label>
      <select name="ApatBanquet_${i}" required>
        <option value="">Selecciona una opcio</option>
        <option value="Menu general">Menu general</option>
        <option value="Menu vegetaria">Menu vegetaria</option>
        <option value="Menu infantil">Menu infantil</option>
        <option value="Altres necessitats">Altres necessitats</option>
      </select>
    </div>

    <div class="form-row" style="margin-bottom: 20px;"> 
      <label>Alergies o intolerancies</label>
      <textarea name="Alergies_${i}" rows="2"></textarea>
    </div>

    <div class="form-row" style="margin-bottom: 30px;">
      <label>Cançó que no pot faltar</label>
      <textarea name="Cancion_${i}" rows="1"></textarea>
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
  if (radioNo.checked) {
    campsAssistencia.style.display = "none";
  } else {
    campsAssistencia.style.display = "block";
  }

  crearCampos(parseInt(personesInput.value || 1));
}

radioSi.addEventListener("change", toggleAssistencia);
radioNo.addEventListener("change", toggleAssistencia);