 console.log("App.js loaded successfully");

const chatlog = document.getElementById("chatlog");
 const qInput = document.getElementById("question");
 const sendBtn = document.getElementById("sendBtn");
 const ingestBtn = document.getElementById("ingestBtn");
 const chips = document.querySelectorAll(".chip");
 
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
 
 const consultForm = document.getElementById("consultForm");
const consultResult = document.getElementById("consultResult");
const downloadBtn = document.getElementById("downloadBtn");

async function submitConsultation(e) {
  e.preventDefault();
  const btn = document.getElementById("consultBtn");
  const originalText = btn.innerText;
  
  btn.disabled = true;
  btn.innerText = "Analyzing... (this may take 10-20s)";
  consultResult.innerHTML = "<div class='msg bot'>Analyzing your health data... please wait.</div>";
  
  const payload = {
    name: document.getElementById("c_name").value,
    age: document.getElementById("c_age").value,
    gender: document.getElementById("c_gender").value,
    severity: document.querySelector('input[name="severity"]:checked').value,
    symptoms: document.getElementById("c_symptoms").value,
    duration: document.getElementById("c_duration").value,
    disease: document.getElementById("c_disease").value
  };

  try {
    const r = await fetch("/consult", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    
    if (!r.ok) {
        throw new Error(`Server error: ${r.status}`);
    }
    
    const data = await r.json();
    if (data.error) {
      consultResult.innerHTML = `<div class="msg bot" style="color:red">Error: ${data.error}</div>`;
    } else {
      const sevClass = `severity-${payload.severity}`;
      const html = `
      <div class="result-card">
        <div class="result-header">
          <div class="result-title">Doctor's Assessment</div>
          <span class="badge ${sevClass}">${payload.severity}</span>
        </div>
        <div class="grid2">
          <div class="block">
            <div class="label">Patient</div>
            <div class="value">${payload.name}, ${payload.age}, ${payload.gender}</div>
            <div class="label" style="margin-top:8px">Symptoms</div>
            <div class="value">${payload.symptoms || "-"}</div>
            <div class="label" style="margin-top:8px">Duration</div>
            <div class="value">${payload.duration || "-"}</div>
          </div>
          <div class="block">
            <div class="label">Disease</div>
            <div class="value">${data.reply.disease || "-"}</div>
            <div class="label" style="margin-top:8px">Medicine</div>
            <div class="value">${data.reply.medicine || "-"}</div>
            <div class="label" style="margin-top:8px">Dose</div>
            <div class="value">${data.reply.dose || "-"}</div>
            <div class="label" style="margin-top:8px">Recommended Tests</div>
            <div class="value">${data.reply.tests || "-"}</div>
            <div class="label" style="margin-top:8px">Home Care</div>
            <div class="value">${data.reply.home_remedy || "-"}</div>
          </div>
        </div>
        ${data.reply.warning ? `<div class="warn-box">WARNING: ${data.reply.warning}</div>` : ""}
      </div>`;
      consultResult.innerHTML = html;
      downloadBtn.style.display = "inline-block";
      downloadBtn.onclick = () => window.location.href = "/download-report";
      consultResult.scrollIntoView({behavior: "smooth"});
      if (data.pdf && !data.pdf.startsWith("Error")) {
          downloadBtn.style.display = "inline-block";
          downloadBtn.onclick = () => window.location.href = "/download-report";
      } else {
          downloadBtn.style.display = "none";
      }
    }
  } catch (err) {
    consultResult.innerHTML = `<div class="msg bot" style="color:red">Network or Server Error. Please ensure the app is running. Details: ${err.message}</div>`;
    console.error(err);
  } finally {
    btn.disabled = false;
    btn.innerText = originalText;
  }
}

if (consultForm) {
    consultForm.addEventListener("submit", submitConsultation);
}

sendBtn.addEventListener("click", send);
 qInput.addEventListener("keypress", (e) => { if (e.key === "Enter") send(); });
 ingestBtn.addEventListener("click", buildIndex);
 chips.forEach(c => c.addEventListener("click", () => { qInput.value = c.dataset.q; qInput.focus(); }));
