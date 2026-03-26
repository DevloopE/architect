const { app, BrowserWindow } = require('electron')
const { spawn } = require('child_process')
const path = require('path')
const http = require('http')

// Enable WebGPU (required — editor uses WebGPU renderer)
app.commandLine.appendSwitch('enable-unsafe-webgpu')
app.commandLine.appendSwitch('enable-webgpu-developer-features')
app.commandLine.appendSwitch('enable-features', 'Vulkan,WebGPU,UseSkiaGraphite')

// Force high-performance GPU
app.commandLine.appendSwitch('ignore-gpu-blocklist')
app.commandLine.appendSwitch('enable-gpu-rasterization')
app.commandLine.appendSwitch('enable-zero-copy')
app.commandLine.appendSwitch('force_high_performance_gpu')

// Use the installed editor (not the submodule — submodule may not have deps installed)
const EDITOR_DIR = process.env.EDITOR_DIR || path.resolve(require('os').homedir(), 'Desktop', 'editor')
const RELAY_PATH = path.join(EDITOR_DIR, 'apps', 'editor', 'bridge-relay.mjs')
const EDITOR_URL = 'http://localhost:3002'
const RELAY_PORT = 3100

let relay = null
let editorProcess = null
let mainWindow = null

function startRelay() {
  relay = spawn('node', ['--experimental-vm-modules', RELAY_PATH], { cwd: path.dirname(RELAY_PATH), stdio: 'pipe' })
  relay.stdout.on('data', (d) => process.stdout.write(`[relay] ${d}`))
  relay.stderr.on('data', (d) => process.stderr.write(`[relay] ${d}`))
  relay.on('exit', (code) => console.log(`[relay] exited ${code}`))
}

function startEditor() {
  const isWin = process.platform === 'win32'
  const bunPath = isWin ? 'bun.exe' : 'bun'
  editorProcess = spawn(bunPath, ['dev'], { cwd: EDITOR_DIR, stdio: 'pipe', shell: true })
  editorProcess.stdout.on('data', (d) => process.stdout.write(`[editor] ${d}`))
  editorProcess.stderr.on('data', (d) => process.stderr.write(`[editor] ${d}`))
  editorProcess.on('exit', (code) => console.log(`[editor] exited ${code}`))
}

function waitForEditor(timeout = 60000) {
  return new Promise((resolve, reject) => {
    const start = Date.now()
    const check = () => {
      http.get(EDITOR_URL, (res) => {
        if (res.statusCode === 200) resolve()
        else if (Date.now() - start > timeout) reject(new Error('Editor timeout'))
        else setTimeout(check, 1000)
      }).on('error', () => {
        if (Date.now() - start > timeout) reject(new Error('Editor timeout'))
        else setTimeout(check, 1000)
      })
    }
    check()
  })
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1600,
    height: 1000,
    title: 'Architect — Pascal Editor',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webgl: true,
      experimentalFeatures: true,
      webgpu: true,
    },
    backgroundColor: '#0a0a0f',
    show: false,
  })

  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
    mainWindow.maximize()
  })

  mainWindow.loadURL(EDITOR_URL)
  mainWindow.on('closed', () => { mainWindow = null })
}

app.whenReady().then(async () => {
  // Kill orphaned processes from previous runs
  const { execSync } = require('child_process')
  for (const port of [3002, 3100]) {
    try {
      if (process.platform === 'win32') {
        const out = execSync(`netstat -ano | findstr ":${port}" | findstr "LISTENING"`, { encoding: 'utf8' })
        const pids = [...new Set(out.split('\n').map(l => l.trim().split(/\s+/).pop()).filter(Boolean))]
        for (const pid of pids) { try { execSync(`taskkill /PID ${pid} /F`, { stdio: 'ignore' }) } catch {} }
      } else {
        execSync(`lsof -ti:${port} | xargs kill -9 2>/dev/null`, { shell: true, stdio: 'ignore' })
      }
    } catch {}
  }
  await new Promise(r => setTimeout(r, 1000))

  console.log('[Architect] Starting relay...')
  startRelay()

  console.log('[Architect] Starting editor...')
  startEditor()

  console.log('[Architect] Waiting for editor to be ready...')
  try {
    await waitForEditor()
    console.log('[Architect] Editor ready, opening window...')
    await createWindow()
  } catch (e) {
    console.error('[Architect] Failed to start:', e.message)
    app.quit()
  }
})

app.on('window-all-closed', () => {
  if (relay) relay.kill()
  if (editorProcess) editorProcess.kill()
  app.quit()
})

app.on('before-quit', () => {
  if (relay) relay.kill()
  if (editorProcess) editorProcess.kill()
})
