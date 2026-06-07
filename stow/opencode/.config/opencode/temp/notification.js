import { readFileSync } from "node:fs"
import { homedir } from "node:os"
import { join } from "node:path"

// ── dedup windows (ms) ──────────────────────────────────────────
const DEDUP = {
  idle: 5000,
  error: 3000,
  permission: 3000,
  question: 3000,
}

// ── default config ──────────────────────────────────────────────
const DEFAULTS = {
  enabled: true,
  focusEnabled: true,
  notifyChildSessions: false,
  quietHours: { enabled: false, start: "22:00", end: "08:00" },
  events: { idle: true, error: true, permission: true, question: true },
}

// ── helpers ─────────────────────────────────────────────────────

function loadConfig() {
  try {
    const path = join(homedir(), ".config", "opencode", "notification.json")
    return JSON.parse(readFileSync(path, "utf-8"))
  } catch {
    return {}
  }
}

function mergeConfig(user) {
  return {
    ...DEFAULTS,
    ...user,
    quietHours: { ...DEFAULTS.quietHours, ...user.quietHours },
    events: { ...DEFAULTS.events, ...user.events },
  }
}

function isQuietHours(cfg) {
  if (!cfg.quietHours.enabled) return false
  const now = new Date()
  const mins = now.getHours() * 60 + now.getMinutes()
  const [sh, sm] = cfg.quietHours.start.split(":").map(Number)
  const [eh, em] = cfg.quietHours.end.split(":").map(Number)
  const start = sh * 60 + sm
  const end = eh * 60 + em
  if (start > end) return mins >= start || mins < end
  return mins >= start && mins < end
}

function getSessionID(event) {
  if (!event?.properties) return null
  return event.properties.sessionID ?? event.properties.info?.id ?? null
}

function getPermissionType(event) {
  if (!event?.properties) return null
  return event.properties.type ?? event.properties.permission ?? null
}

function getQuestionText(event) {
  if (!event?.properties) return null
  return (event.properties.question ?? event.properties.message ?? null)
}

function truncate(str, max = 80) {
  if (!str) return ""
  const s = String(str)
  return s.length > max ? s.slice(0, max - 3) + "..." : s
}

function shouldDedup(map, key, windowMs) {
  const now = Date.now()
  for (const [k, t] of map) {
    if (now - t > windowMs) map.delete(k)
  }
  if (map.has(key) && now - map.get(key) < windowMs) return true
  map.set(key, now)
  return false
}

async function isParentSession(client, sessionID) {
  try {
    const session = await client.session.get({ path: { id: sessionID } })
    return !session.data?.parentID
  } catch {
    return true
  }
}

async function getSessionTitle(client, sessionID) {
  try {
    const session = await client.session.get({ path: { id: sessionID } })
    return session.data?.title || null
  } catch {
    return null
  }
}

// ── terminal window detection (niri on Wayland) ─────────────────

async function runNiri(args, timeoutMs = 3000) {
  const proc = Bun.spawn(["niri", "msg", ...args], {
    stdout: "pipe",
    stderr: "ignore",
  })
  const timer = new Promise((_, reject) =>
    setTimeout(() => { proc.kill(); reject(new Error("timeout")) }, timeoutMs),
  )
  const text = await Promise.race([new Response(proc.stdout).text(), timer]).catch(() => "")
  return text
}

async function detectTerminalWindow() {
  try {
    const result = await runNiri(["focused-window"])
    const match = result.match(/^Window ID (\d+):/)
    if (match) return parseInt(match[1])
  } catch {}
  return null
}

// ── notification senders ────────────────────────────────────────

function sendSimple({ title, message, urgency }) {
  Bun.spawn(["notify-send", "-u", urgency, "-a", "OpenCode", title, message], {
    stdout: "ignore",
    stderr: "ignore",
  })
}

function sendWithFocus({ title, message, urgency, terminalWindowID }) {
  const proc = Bun.spawn(
    ["notify-send", "-A", "focus=Focus", "-t", "10000", "-u", urgency, "-a", "OpenCode", title, message],
    { stdout: "pipe", stderr: "ignore" },
  )
  ;(async () => {
    try {
      const result = await new Response(proc.stdout).text()
      if (result.trim() === "focus") {
        Bun.spawn(["niri", "msg", "action", "focus-window", "--id", String(terminalWindowID)], {
          stdout: "ignore",
          stderr: "ignore",
        })
      }
    } catch {}
  })()
}

// ── plugin ──────────────────────────────────────────────────────

export const NotificationPlugin = async ({ project, client, $, directory, worktree }) => {
  const config = mergeConfig(loadConfig())
  if (!config.enabled) return {}

  const doFocus = config.focusEnabled !== false

  let terminalWindowID = null
  let terminalProbed = false
  const ensureWindowID = async () => {
    if (terminalProbed) return terminalWindowID
    terminalProbed = true
    if (doFocus) terminalWindowID = await detectTerminalWindow()
    return terminalWindowID
  }

  const dedupIdle = new Map()
  const dedupError = new Map()
  const dedupPermission = new Map()
  const dedupQuestion = new Map()

  return {
    event: async ({ event }) => {
      if (!event?.type) return
      if (isQuietHours(config)) return

      const sid = getSessionID(event)

      switch (event.type) {
        // ── session idle ──────────────────────────────────
        case "session.idle": {
          if (!config.events.idle || !sid) return
          if (shouldDedup(dedupIdle, sid, DEDUP.idle)) return
          if (!config.notifyChildSessions && !(await isParentSession(client, sid))) return

          const title = await getSessionTitle(client, sid)
          const payload = {
            title: "OpenCode",
            message: title ? `Completed: ${title}` : "Task completed",
            urgency: "normal",
          }
          const wid = await ensureWindowID()
          if (wid) {
            sendWithFocus({ ...payload, terminalWindowID: wid })
          } else {
            sendSimple(payload)
          }
          break
        }

        // ── session error ─────────────────────────────────
        case "session.error": {
          if (!config.events.error || !sid) return
          if (shouldDedup(dedupError, sid, DEDUP.error)) return
          if (!config.notifyChildSessions && !(await isParentSession(client, sid))) return

          const err = event.properties?.error ?? "Unknown error"
          const payload = {
            title: "OpenCode Error",
            message: truncate(String(err), 100),
            urgency: "critical",
          }
          const wid = await ensureWindowID()
          if (wid) {
            sendWithFocus({ ...payload, terminalWindowID: wid })
          } else {
            sendSimple(payload)
          }
          break
        }

        // ── permission ────────────────────────────────────
        case "permission.asked": {
          if (!config.events.permission) return

          const perm = getPermissionType(event) ?? "unknown"
          const key = sid ? `${sid}:${perm}` : perm
          if (shouldDedup(dedupPermission, key, DEDUP.permission)) return

          sendSimple({
            title: "OpenCode",
            message: `Waiting for permission: ${perm}`,
            urgency: "critical",
          })
          break
        }

        // ── question ──────────────────────────────────────
        case "question.asked": {
          if (!config.events.question) return

          const text = getQuestionText(event)
          const key = sid ?? String(Date.now())
          if (shouldDedup(dedupQuestion, key, DEDUP.question)) return

          sendSimple({
            title: "OpenCode Question",
            message: text ? `Q: ${text}` : "OpenCode needs your input",
            urgency: "critical",
          })
          break
        }
      }
    },
  }
}
