# Setting up Orbit (instructions for Claude)

Someone asked you to set up Orbit on their computer: a crew of AI employees that runs on this computer
through Claude Code. Claude Code can use Claude's configured connection — the owner's
own Claude account, an organization setup, or another supported configuration. Orbit only needs the
client installed; it never signs in, checks or changes that connection. It works on a Mac, on Windows
(natively, or through WSL2 as the fallback) and on Linux. They may not be technical. Do every step
yourself. Before each step, say in one plain sentence what it does and why; after it, say what
happened. Keep it calm and short.

**Never ask for, read, copy or print a password, a token or a Claude login** in this chat. Bot tokens
and the Apify token are typed into the control panel, a page on this computer, never here. Don't use
`sudo` and don't run anything as administrator yourself, don't change system settings, and when a step
needs their password or an administrator window, tell them exactly what to type and where, then wait.
If a step fails twice, stop and tell them plainly what failed and what you'd try next.

Claude's connection belongs to the owner. Do not sign in to Claude for them, ask them to sign in as a
setup step, or run account commands for them. The readiness check is only that the installed client
runs (`claude --version`). If they already use Claude Code on this computer, leave its configuration
alone; ordinary work will use it. If they want to change how Claude connects, that is Claude Code's own
setup, outside Orbit's install.

## 1. Which computer
- `uname -s` says `Darwin`: a Mac. Follow **Mac** below.
- `uname -s` says `Linux`: follow **Linux** below.
- Otherwise (`MINGW…`/`MSYS…`, or PowerShell where `$env:OS` is `Windows_NT`): Windows. Follow **Windows**
  below (native first; if the machine is Windows 10, or the doctor says the MXC runtime can't run here,
  the same machine can run the crew through WSL — **Windows through WSL** further down).

## Mac
1. `python3 --version` and `git --version`. If either is missing, macOS offers to install its developer
   tools in a dialog: tell them to click **Install**, wait for it to finish (a few minutes), then go on.
2. Get the kit. If `~/orbit` is already a checkout of this repository: `git -C ~/orbit pull --ff-only`.
   Otherwise: `git clone https://github.com/BasemTarekkamal/orbit ~/orbit`.
3. Claude Code for the employees. The employees run on the `claude` command-line tool. It is
   Anthropic's own program; Orbit never sees or stores its connection details, and it does not need
   the owner's account details here.
   - `claude --version` (also try `~/.local/bin/claude --version`). If it isn't there, install it with
     Anthropic's official installer: `curl -fsSL https://claude.ai/install.sh | bash`, then check
     `claude --version` again. That is the whole readiness check: an installed client that runs.
   - Leave Claude's existing configuration alone. If the owner already uses Claude Code on this
     computer, ordinary work will use that connection. If they ask how to configure it, point them to
     Claude Code's own setup; don't run account commands for them.
   - For unattended work (routines, reports, or messages while no Terminal window is open), that
     connection must stay available to the background service after this window closes. Normally that
     means Claude's persistent sign-in, Claude user/managed settings, or the environment of the OS
     service — not a temporary export typed in this shell. Ask them to configure it once in Claude Code
     if it isn't already.
4. Install: `~/orbit/install.sh --yes`. It installs a few Python packages for this user only, the
   headless browser the employees research with (about 150 MB), and the `orbit` command, then starts
   the team's background service and opens the control panel in their browser. Two to five minutes.
   If it reports a problem, run `~/orbit/orbit doctor` and fix what it lists, one item at a time.
5. Hand over (below).

## Windows
On Windows 11 24H2 with current updates or newer, native Windows is the primary path: no WSL, no Linux
shell, no restarts. You run commands from here (Claude, PowerShell or Terminal) as themselves. The
installer/doctor sends older or unsupported builds to the WSL2 fallback below.
1. Get the kit. If the folder (say `C:\Users\them\orbit`) is already a checkout: `git -C <kit> pull --ff-only`.
   Otherwise: `git clone https://github.com/BasemTarekkamal/orbit <kit>`.
2. Claude Code for the employees. `claude --version`; if it's missing, have them install Claude Code
   for Windows (https://claude.com/claude-code), then check `claude --version` again. Leave their
   existing Claude configuration alone — Orbit uses it as-is and never sees the connection details.
   If they ask to change it, point them to Claude Code's own setup; don't run account commands for
   them. Unattended routines need that configuration to persist for the background service, normally
   through Claude's own persistent sign-in or user/managed settings, not a one-off shell setting.
3. `powershell -ExecutionPolicy Bypass -File <kit>\setup-windows.ps1` (add `-Yes` to skip the optional
   voice-notes prompts). It checks the Windows build, installs Python, git, ffmpeg and tesseract with
   winget, installs the signed MXC sandbox runtime into the kit's `vendor\mxc` (checksum and Microsoft
   signature verified), and the
   Python packages, your user only. Two to five minutes. It's safe to run again.
4. Starting the crew: `python <kit>\orbit setup` (it asks their business and bot token in the panel;
   the checks gate it). If a check fails, `python <kit>\orbit doctor` and fix what it lists, one item
   at a time — every fix names a Windows command.
5. Hand over (below).

## Windows through WSL (the fallback)
For Windows 10, or Windows 11 machines where the doctor says the MXC runtime can't run. Orbit runs
inside WSL 2 there. Its bubblewrap sandbox is optional and off by default; `orbit sandbox on` enables
it. You run each Linux command from here with `wsl -d <distro> -- bash -lc "<command>"` (the distro name
comes from step 1; usually `Ubuntu`). Quote the command so the Windows shell passes it through whole.
1. `wsl -l -v`. If it lists no distro, or says WSL isn't installed, tell them: "Windows needs its Linux
   part turned on, once. Click Start, type **PowerShell**, right-click it and choose **Run as
   administrator**, then type `wsl --install` and press Enter. Restart when it asks. After the restart
   an **Ubuntu** window opens: choose a username and a password (only for this Linux; you'll type it
   once more in a minute). Tell me when you see the Ubuntu prompt." Wait for them. If the VERSION
   column says 1: `wsl --set-version <distro> 2` (a few minutes).
2. Get the kit: `wsl -d <distro> -- bash -lc "git -C ~/orbit pull --ff-only 2>/dev/null || git clone
   https://github.com/BasemTarekkamal/orbit ~/orbit"`. If git is missing, step 3 installs it: do step 3
   first, then this.
3. System packages (voice, OCR, the browser's libraries, and the optional sandbox's helpers) need their Ubuntu password. Ask
   them to type this in the Ubuntu window and wait until it prints Done:
   `sudo sh ~/orbit/setup-linux.sh`
   (if ~/orbit isn't there yet: `sudo apt-get update && sudo apt-get install -y git`, then step 2, then this).
4. Claude Code inside Ubuntu (the employees run on this copy):
   `wsl -d <distro> -- bash -lc "~/.local/bin/claude --version || curl -fsSL https://claude.ai/install.sh | bash"`.
   Then check `wsl -d <distro> -- bash -lc "~/.local/bin/claude --version"` again. Use the same Claude
   configuration they already use: Orbit doesn't sign them in or inspect the account. If it needs
   configuring for unattended routines, do it once in Claude Code itself, so it persists for the
   background service.
5. Install: `wsl -d <distro> -- bash -lc "~/orbit/install.sh --yes"`. It starts the team from the
   Windows side (it keeps running after the Ubuntu window closes, and starts again at every Windows
   login) and opens Mission Control in their Windows browser. If it reports a problem:
   `wsl -d <distro> -- bash -lc "~/orbit/orbit doctor"` and fix what it lists.
6. Hand over (below).

## Linux
1. `~/orbit/install.sh` needs a few system packages first. If `bwrap`, `socat`, `git` or pip is missing
   (`command -v bwrap socat git; python3 -m pip --version`), get the kit if you can
   (`git clone https://github.com/BasemTarekkamal/orbit ~/orbit`), then ask them to run in their own
   terminal, where it asks their password: `sudo sh ~/orbit/setup-linux.sh`. Wait until it prints Done.
2. Claude Code: as in **Mac** step 3 (`curl -fsSL https://claude.ai/install.sh | bash`, then
   `claude --version`). Keep the connection they already use; don't change or inspect it.
3. Install: `~/orbit/install.sh --yes`. If it reports a problem, run `~/orbit/orbit doctor`.
4. Hand over (below).

## Hand over
Tell them, in your own words, short:
- "Your control panel is open in your browser. It asks your name and what your business does, then you
  pick a job; your Claude asks a few questions about it and writes their card. When you launch them,
  they start right away with a real first task." If the page
  didn't open: `~/orbit/orbit panel` (on Windows: `python <kit>\orbit panel`; through the WSL fallback,
  `wsl -d <distro> -- bash -lc "~/orbit/orbit panel"`).
- How they'll talk to their crew, all three ways, since they won't think to ask:
  1. **In the control panel:** open the crew member and type; the answer appears right under it.
  2. **On their phone** (recommended): Telegram, Slack or Discord, through a bot of their own. The panel's
     "Connect your phone" walks them through it in about two minutes. Then they message the crew from
     anywhere, send voice notes and files, and get the routine reports there.
   3. **In the Claude app** (best if they live in Claude, not in a browser tab): **Orbit's own control-plane chat**, opened
      with `~/orbit/orbit desk` or the panel's "Orbit in Claude" button. There they hire by talking (the same
      interview), ask who's doing what, read what the crew said, and change anyone. On Mac, Linux and WSL, each
      crew member also has **their own chat** (`~/orbit/orbit open <handle>`, or **Open in Claude** on their page):
      press Enter once the first time, and their standup, initiative, end of day and weekly review happen there,
      with the unread dot. Native-Windows employee Desktop chats remain disabled pending feature 003; use the
      contained `python <kit>\orbit chat <handle>` terminal conversation instead.
- What to expect: an answer in a minute or two (deep research takes longer), each with "How I did it".
  On their own, crew members only send the routines ticked in Manage (like a morning brief) and things
  that need the owner. They never post, buy, or message anyone but the owners.
Then run `~/orbit/orbit desk` so Orbit's chat is waiting for them in the Claude app (they press Enter once), and
offer to stay while they connect their phone. That's the whole setup.

## What Orbit trusts (say this plainly if they ask)
- **Their Claude configuration is theirs.** Ordinary local runs load the owner's Claude user and
  project settings, including hooks and plugins. Those are trusted configuration and may run; Orbit
  does not review, sandbox or vouch for them.
- **Ordinary runs pass the service environment through.** Claude receives the background service's
  complete inherited environment — Claude/provider values and any unrelated values present, including
  secrets. Orbit does not add credential isolation beyond Claude's own behavior.
- **Cloud Shift is separate and optional.** It needs a qualifying Claude plan account available on
  this computer and a fresh check before each cloud launch. If it isn't eligible, only cloud launches
  are blocked with an account-only explanation; ordinary local work keeps running. Turning Cloud
  Shift off never needs the account. Orbit cannot promise to revoke a remote schedule created while
  this computer was offline.
- **Diagnose Claude by Claude's own result.** If a run fails, verify the client's configured connection
  by running `claude` directly, then `orbit doctor`. Orbit reports Claude's own result and does not
  guess a provider, endpoint, locality or fallback.

## Extras, only when they ask
- **Voice notes and live calls** (transcribed on this computer):
  - Mac: needs Homebrew. If `brew --version` fails, explain that installing Homebrew asks for their Mac
    password, which they type themselves; with their yes, follow the command on https://brew.sh. Then
    `brew install ffmpeg whisper-cpp` and `~/orbit/orbit doctor --get-voice-model` (a 550 MB download).
  - Native Windows: `py` in PowerShell — `orbit doctor --get-whisper --get-voice-model` (builds the speech
    engine or walks them through winget installs if that's needed, a few minutes, and downloads the
    550 MB model). ffmpeg comes from `winget install Gyan.FFmpeg`; live calls need Python for Windows
    (setup-windows.ps1 installs it).
  - Windows through WSL and Linux: `~/orbit/orbit doctor --get-whisper --get-voice-model` (builds the
    speech engine, a few minutes, and downloads the 550 MB model). For live calls, Python for Windows is
    needed too: ask them to run in PowerShell `winget install Python.Python.3.12`, then
    `py -m pip install soundcard numpy`.
- **Change how Claude connects:** that is Claude Code's own setup, done once by the owner. After they
  change it, verify by running `claude` directly; Orbit uses it on the next run. Never sign them out.
  Cloud Shift, if they use it, shows its own account status in Settings.
- **Update Orbit:** `git -C ~/orbit pull --ff-only && ~/orbit/orbit restart`.
- **Something's wrong:** `~/orbit/orbit doctor`, then `~/orbit/orbit logs`.
- **Stop it:** `~/orbit/orbit stop`. Their team's folder (`~/Staff`) stays unless they ask you to
  delete it; confirm before you do, it holds everything their employees learned.
