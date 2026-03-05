/* doc-to-markdown web UI — Pyodide bootstrap, file handling, UI logic */

const PYODIDE_CDN = "https://cdn.jsdelivr.net/pyodide/v0.27.5/full/";
const ACCEPTED_EXTENSIONS = [".docx", ".html", ".htm"];
const MAX_FILES = 5;

// CLI module files to load into Pyodide's virtual filesystem
// Note: pdf_converter excluded — pdfplumber requires pypdfium2 (native C),
// which can't run in Pyodide. PDF conversion requires the CLI.
const CLI_MODULES = [
  "cli/__init__.py",
  "cli/convert.py",
  "cli/docx_converter.py",
  "cli/html_converter.py",
];

// ── DOM refs ────────────────────────────────────────────────────────
const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const status = document.getElementById("status");
const outputArea = document.getElementById("outputArea");
const output = document.getElementById("output");
const fileNav = document.getElementById("fileNav");
const activeFilename = document.getElementById("activeFilename");
const copyBtn = document.getElementById("copyBtn");
const downloadBtn = document.getElementById("downloadBtn");
const clearBtn = document.getElementById("clearBtn");

let pyodide = null;
let pyodideReady = false;

// ── Multi-file state ─────────────────────────────────────────────────
let conversions = []; // [{name, markdown, error}]
let activeIndex = 0;

// ── Status helpers ──────────────────────────────────────────────────
function setStatus(msg, type) {
  status.style.display = "";  // Clear inline override so CSS class controls visibility
  status.textContent = msg;
  status.className = type; // "loading", "success", "error"
}

function setStatusHTML(html, type) {
  status.style.display = "";
  status.innerHTML = html;
  status.className = type;
}

// ── Pyodide init ────────────────────────────────────────────────────
async function initPyodide() {
  try {
    setStatusHTML('<span class="spinner"></span>Loading Python runtime...', "loading");

    pyodide = await loadPyodide({ indexURL: PYODIDE_CDN });

    setStatusHTML('<span class="spinner"></span>Installing packages...', "loading");

    await pyodide.loadPackage("micropip");
    const micropip = pyodide.pyimport("micropip");
    await micropip.install(["python-docx", "beautifulsoup4"]);

    setStatusHTML('<span class="spinner"></span>Loading converters...', "loading");

    // Create cli/ directory in Pyodide VFS
    pyodide.FS.mkdir("/home/pyodide/cli");

    // Resolve base URL (works on GitHub Pages and local server)
    const base = new URL(".", window.location.href).href;

    // Fetch each CLI module from docs/cli/ (bundled copy for GitHub Pages)
    for (const modPath of CLI_MODULES) {
      const resp = await fetch(base + modPath);
      if (!resp.ok) throw new Error(`Failed to load ${modPath}`);
      const text = await resp.text();
      pyodide.FS.writeFile("/home/pyodide/" + modPath, text);
    }

    // Load the converter bridge
    const bridgeResp = await fetch(base + "converter.py");
    if (!bridgeResp.ok) throw new Error("Failed to load converter.py");
    const bridgeCode = await bridgeResp.text();
    pyodide.FS.writeFile("/home/pyodide/converter.py", bridgeCode);

    // Add VFS root to Python path and import converter
    await pyodide.runPythonAsync(`
import sys
sys.path.insert(0, "/home/pyodide")
import converter
`);

    pyodideReady = true;
    status.className = "";  // Removes class, CSS default is display:none
  } catch (err) {
    console.error("Pyodide init failed:", err);
    setStatus("Failed to load Python runtime: " + (err.message || err), "error");
  }
}

// ── File handling ───────────────────────────────────────────────────
function getExtension(filename) {
  const dot = filename.lastIndexOf(".");
  return dot === -1 ? "" : filename.substring(dot).toLowerCase();
}

function isAccepted(filename) {
  return ACCEPTED_EXTENSIONS.includes(getExtension(filename));
}

async function convertFile(file) {
  const arrayBuf = await file.arrayBuffer();
  const uint8 = new Uint8Array(arrayBuf);

  pyodide.globals.set("_file_bytes", pyodide.toPy(uint8));
  pyodide.globals.set("_file_name", file.name);

  return await pyodide.runPythonAsync(`
from converter import convert_file as _convert
_convert(_file_name, bytes(_file_bytes))
`);
}

async function handleFiles(fileList) {
  const files = Array.from(fileList);

  const remaining = MAX_FILES - conversions.length;
  if (remaining <= 0) {
    setStatus(`Maximum of ${MAX_FILES} files already loaded. Clear all to start over.`, "error");
    return;
  }

  if (files.length > remaining) {
    setStatus(`Only ${remaining} slot(s) remaining. First ${remaining} file(s) will be processed.`, "error");
  }

  const toProcess = files.slice(0, remaining);

  if (!pyodideReady) {
    setStatus("Python runtime is still loading. Please wait...", "loading");
    return;
  }

  for (const file of toProcess) {
    if (!isAccepted(file.name)) {
      const ext = getExtension(file.name);
      let errorMsg;
      if (ext === ".pdf") {
        errorMsg = "PDF not supported in browser. Use the CLI: python -m cli input.pdf -o output.md";
      } else {
        errorMsg = `Unsupported file type: ${ext || "(no extension)"}`;
      }
      conversions.push({ name: file.name, markdown: null, error: errorMsg });
      renderFileNav();
      showFile(conversions.length - 1);
      continue;
    }

    setStatusHTML(`<span class="spinner"></span>Converting ${file.name}...`, "loading");

    try {
      const markdown = await convertFile(file);
      conversions.push({ name: file.name, markdown, error: null });
      renderFileNav();
      showFile(conversions.length - 1);
      setStatus(`Converted ${file.name}`, "success");
    } catch (err) {
      const msg = err.message || String(err);
      const pyErr = msg.includes("PythonError") ? msg.split("\n").pop() : msg;
      conversions.push({ name: file.name, markdown: null, error: `Conversion failed: ${pyErr}` });
      renderFileNav();
      showFile(conversions.length - 1);
      setStatus(`Failed to convert ${file.name}: ${pyErr}`, "error");
    }
  }
}

// ── File nav ────────────────────────────────────────────────────────
function renderFileNav() {
  // Remove existing chips only (leave spacer + clear button in place)
  fileNav.querySelectorAll(".file-chip").forEach(el => el.remove());

  if (conversions.length === 0) {
    fileNav.style.display = "none";
    return;
  }

  fileNav.style.display = "flex";

  conversions.forEach((conv, i) => {
    const chip = document.createElement("button");
    chip.className = "file-chip" +
      (conv.error ? " error" : "") +
      (i === activeIndex ? " active" : "");
    chip.textContent = conv.name;
    chip.title = conv.name;
    chip.addEventListener("click", () => showFile(i));
    fileNav.appendChild(chip);
  });
}

function showFile(index) {
  activeIndex = index;
  const conv = conversions[index];

  output.value = conv.error ? conv.error : conv.markdown;
  activeFilename.textContent = conv.name;
  outputArea.classList.add("visible");

  if (conv.error) {
    setStatus(conv.error, "error");
  } else {
    setStatus(`Converted ${conv.name}`, "success");
  }

  renderFileNav();
}

// ── Drop zone events ────────────────────────────────────────────────
dropZone.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", (e) => {
  if (e.target.files.length) handleFiles(e.target.files);
  fileInput.value = "";  // Reset so the same file can be re-selected
});

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("drag-over");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("drag-over");
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("drag-over");
  if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files);
});

// ── Action buttons ──────────────────────────────────────────────────
copyBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(output.value);
    copyBtn.textContent = "Copied!";
    setTimeout(() => { copyBtn.textContent = "Copy"; }, 1500);
  } catch {
    // Fallback
    output.select();
    document.execCommand("copy");
    copyBtn.textContent = "Copied!";
    setTimeout(() => { copyBtn.textContent = "Copy"; }, 1500);
  }
});

downloadBtn.addEventListener("click", () => {
  const conv = conversions[activeIndex];
  if (!conv || conv.error) return;
  const mdName = conv.name.replace(/\.[^.]+$/, ".md");
  const blob = new Blob([conv.markdown], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = mdName;
  a.click();
  URL.revokeObjectURL(url);
});

clearBtn.addEventListener("click", () => {
  conversions = [];
  activeIndex = 0;
  output.value = "";
  activeFilename.textContent = "";
  outputArea.classList.remove("visible");
  status.className = "";
  renderFileNav();
});

// ── Boot ────────────────────────────────────────────────────────────
const pyodideScript = document.createElement("script");
pyodideScript.src = PYODIDE_CDN + "pyodide.js";
pyodideScript.onload = () => initPyodide();
document.head.appendChild(pyodideScript);
