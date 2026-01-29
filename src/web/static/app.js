 const chatlog = document.getElementById("chatlog");
 const qInput = document.getElementById("question");
 const sendBtn = document.getElementById("sendBtn");
 const ingestBtn = document.getElementById("ingestBtn");
 const chips = document.querySelectorAll(".chip");
const consultForm = document.getElementById("consultForm");
const consultBtn = document.getElementById("consultBtn");
const downloadBtn = document.getElementById("downloadBtn");
const consultResult = document.getElementById("consultResult");
 
 function addMsg(text, cls) {
   const d = document.createElement("div");
   d.className = `msg ${cls}`;
   d.innerText = text;
   chatlog.appendChild(d);
   chatlog.scrollTop = chatlog.scrollHeight;
 }
 
 async function send() {
   const q = qInput.value.trim();
   if (!q) return;
   addMsg(q, "user");
   sendBtn.disabled = true;
   const spin = document.createElement("div");
   spin.className = "spinner";
   sendBtn.after(spin);
   try {
     const r = await fetch("/get_answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q })
    });
     const data = await r.json();
     addMsg(data.answer, "bot");
   } catch (e) {
     addMsg("Error contacting server.", "bot");
   } finally {
     sendBtn.disabled = false;
     spin.remove();
     qInput.value = "";
     qInput.focus();
   }
 }
 
 async function buildIndex() {
   ingestBtn.disabled = true;
   const spin = document.createElement("div");
   spin.className = "spinner";
   ingestBtn.after(spin);
   try {
     const r = await fetch("/ingest", { method: "POST" });
     await r.json();
     addMsg("Index built from PDFs.", "bot");
   } catch (e) {
     addMsg("Index build failed.", "bot");
   } finally {
     ingestBtn.disabled = false;
     spin.remove();
   }
 }
 
function renderConsultOutput(payload) {
  const { reply, pdf } = payload;
  const patientName = document.getElementById("c_name").value.trim();
  const patientAge = document.getElementById("c_age").value.trim();
  const severity = document.querySelector("input[name='severity']:checked").value;
  const splitList = (s) => (s || "").split(/[,;]+/).map(x => x.trim()).filter(Boolean);
  const redFlagYesNo = ((reply.warning || "").trim().length > 0) ? "Yes" : "No";
  consultResult.innerHTML = `
    <div class="card">
      <h3>Patient Summary</h3>
      <p>Name: ${patientName}</p>
      <p>Age: ${patientAge}</p>
      <p>Severity: ${severity}</p>
    </div>
    <div class="card">
      <h3>Probable Condition</h3>
      <p>${reply.disease || "Unknown"}</p>
    </div>
    <div class="card">
      <h3>Medicines</h3>
      <ul>
        ${splitList(reply.medicine).map(m => `<li>${m}</li>`).join("")}
      </ul>
    </div>
    <div class="card">
      <h3>Recommended Tests</h3>
      <ul>
        ${splitList(reply.tests).map(t => `<li>${t}</li>`).join("")}
      </ul>
    </div>
    <div class="card">
      <h3>Home Care</h3>
      <ul>
        ${splitList(reply.home_remedy).map(h => `<li>${h}</li>`).join("")}
      </ul>
    </div>
    <div class="card">
      <h3>Red Flags</h3>
      <p>${redFlagYesNo}</p>
      <ul>
        ${splitList(reply.warning).map(w => `<li>${w}</li>`).join("")}
      </ul>
    </div>
  `;
  downloadBtn.style.display = "inline-block";
  downloadBtn.onclick = async () => {
    try {
      const res = await fetch("/download-report");
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "health_report.pdf";
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      }
    } catch (e) {
      alert("Unable to download report.");
    }
  };
}

async function submitConsult(e) {
  e.preventDefault();
  consultBtn.disabled = true;
  consultResult.innerHTML = "";
  try {
    const payload = {
      name: document.getElementById("c_name").value.trim(),
      age: document.getElementById("c_age").value.trim(),
      gender: document.getElementById("c_gender").value.trim(),
      severity: document.querySelector("input[name='severity']:checked").value,
      symptoms: document.getElementById("c_symptoms").value.trim(),
      duration: document.getElementById("c_duration").value.trim(),
      disease: document.getElementById("c_disease").value.trim(),
    };
    const r = await fetch("/consult", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      consultResult.innerHTML = `<p>${err.error || "Server error"}</p>`;
      return;
    }
    const data = await r.json();
    renderConsultOutput(data);
  } catch (e) {
    consultResult.innerHTML = "<p>Error contacting server.</p>";
  } finally {
    consultBtn.disabled = false;
  }
}

 sendBtn.addEventListener("click", send);
 qInput.addEventListener("keypress", (e) => { if (e.key === "Enter") send(); });
 ingestBtn.addEventListener("click", buildIndex);
 chips.forEach(c => c.addEventListener("click", () => { qInput.value = c.dataset.q; qInput.focus(); }));
consultForm.addEventListener("submit", submitConsult);
