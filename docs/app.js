/* doc-to-markdown web UI — Pyodide bootstrap, file handling, UI logic */

const PYODIDE_CDN = "https://cdn.jsdelivr.net/pyodide/v0.27.5/full/";
const ACCEPTED_EXTENSIONS = [".docx", ".html", ".htm"];

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
const copyBtn = document.getElementById("copyBtn");
const downloadBtn = document.getElementById("downloadBtn");
const resetBtn = document.getElementById("resetBtn");

let pyodide = null;
let pyodideReady = false;
let currentFilename = "";

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

async function handleFile(file) {
  if (!file) return;

  if (!isAccepted(file.name)) {
    const ext = getExtension(file.name);
    if (ext === ".pdf") {
      setStatusHTML(
        'PDF is not supported in the browser. To convert PDFs, use the CLI: ' +
        '<code>python -m cli input.pdf -o output.md</code><br>' +
        'Select a .docx or .html file, or drag the file to the field above to continue converting to markdown.',
        "error"
      );
    } else {
      setStatusHTML(
        `Unsupported file type: <strong>${ext}</strong><br>` +
        'Select a .docx or .html file, or drag the file to the field above to continue converting to markdown.',
        "error"
      );
    }
    return;
  }

  if (!pyodideReady) {
    setStatus("Python runtime is still loading. Please wait...", "loading");
    return;
  }

  currentFilename = file.name;
  setStatusHTML('<span class="spinner"></span>Converting...', "loading");
  outputArea.classList.remove("visible");

  try {
    const arrayBuf = await file.arrayBuffer();
    const uint8 = new Uint8Array(arrayBuf);

    // Pass bytes to Python
    pyodide.globals.set("_file_bytes", pyodide.toPy(uint8));
    pyodide.globals.set("_file_name", file.name);

    const markdown = await pyodide.runPythonAsync(`
from converter import convert_file as _convert
_convert(_file_name, bytes(_file_bytes))
`);

    output.value = markdown;
    outputArea.classList.add("visible");
    setStatus(`Converted ${file.name}`, "success");
  } catch (err) {
    const msg = err.message || String(err);
    // Extract the Python error message if present
    const pyErr = msg.includes("PythonError") ? msg.split("\n").pop() : msg;
    setStatus(`Conversion failed: ${pyErr}`, "error");
  }
}

// ── Drop zone events ────────────────────────────────────────────────
dropZone.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", (e) => {
  if (e.target.files.length) handleFile(e.target.files[0]);
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
  if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});

// ── Action buttons ──────────────────────────────────────────────────
copyBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(output.value);
    copyBtn.textContent = "Copied!";
    setTimeout(() => { copyBtn.textContent = "Copy to Clipboard"; }, 1500);
  } catch {
    // Fallback
    output.select();
    document.execCommand("copy");
    copyBtn.textContent = "Copied!";
    setTimeout(() => { copyBtn.textContent = "Copy to Clipboard"; }, 1500);
  }
});

downloadBtn.addEventListener("click", () => {
  const mdName = currentFilename.replace(/\.[^.]+$/, ".md");
  const blob = new Blob([output.value], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = mdName;
  a.click();
  URL.revokeObjectURL(url);
});

resetBtn.addEventListener("click", () => {
  output.value = "";
  outputArea.classList.remove("visible");
  status.className = "";  // Removes class, CSS default is display:none
  currentFilename = "";
});

// ── Boot ────────────────────────────────────────────────────────────
const pyodideScript = document.createElement("script");
pyodideScript.src = PYODIDE_CDN + "pyodide.js";
pyodideScript.onload = () => initPyodide();
document.head.appendChild(pyodideScript);
