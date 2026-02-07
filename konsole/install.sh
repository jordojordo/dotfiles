#!/bin/sh
#
# Konsole Theme Switcher
#
# Installs Konsole profiles, colorschemes, and a daemon that automatically
# switches Konsole between light/dark profiles when KDE Plasma changes its
# color scheme.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

info () {
  printf "\r  [ \033[00;34m..\033[0m ] %s\n" "$1"
}

success () {
  printf "\r\033[2K  [ \033[00;32mOK\033[0m ] %s\n" "$1"
}

warn () {
  printf "\r\033[2K  [ \033[0;33m!!\033[0m ] %s\n" "$1"
}

# Check if running under KDE Plasma
is_kde() {
  # Check XDG_CURRENT_DESKTOP
  case "${XDG_CURRENT_DESKTOP:-}" in
    *KDE*|*Plasma*) return 0 ;;
  esac

  # Check for KDE session
  if [ "${KDE_SESSION_VERSION:-}" ]; then
    return 0
  fi

  # Check if kreadconfig6 exists and works
  if command -v kreadconfig6 >/dev/null 2>&1; then
    return 0
  fi

  return 1
}

# Check if pyinotify is available
has_pyinotify() {
  python3 -c "import pyinotify" 2>/dev/null
}

# Create directory and symlink a file
symlink_file() {
  src="$1"
  dst="$2"

  # Create parent directory if needed
  mkdir -p "$(dirname "$dst")"

  # Remove existing file/symlink if present
  if [ -L "$dst" ] || [ -e "$dst" ]; then
    rm -f "$dst"
  fi

  ln -s "$src" "$dst"
  success "linked $src -> $dst"
}

# Main installation
main() {
  info "Konsole Theme Switcher installer"

  # Skip if not KDE
  if ! is_kde; then
    info "Not running KDE Plasma, skipping Konsole theme switcher installation"
    exit 0
  fi

  # Check for pyinotify
  if ! has_pyinotify; then
    warn "pyinotify not found. Install python3-inotify (Fedora) or python-pyinotify (Arch)"
    warn "Skipping Konsole theme switcher installation"
    exit 0
  fi

  info "KDE Plasma detected, installing Konsole theme switcher..."

  # Symlink profiles
  for profile in "$SCRIPT_DIR"/profiles/*.profile; do
    [ -e "$profile" ] || continue
    name="$(basename "$profile")"
    symlink_file "$profile" "$HOME/.local/share/konsole/$name"
  done

  # Symlink colorschemes
  for colorscheme in "$SCRIPT_DIR"/colorschemes/*.colorscheme; do
    [ -e "$colorscheme" ] || continue
    name="$(basename "$colorscheme")"
    symlink_file "$colorscheme" "$HOME/.local/share/konsole/$name"
  done

  # Symlink daemon script
  symlink_file "$SCRIPT_DIR/konsole-theme-switcher.py" "$HOME/.local/bin/konsole-theme-switcher.py"
  chmod +x "$HOME/.local/bin/konsole-theme-switcher.py"

  # Symlink systemd service
  symlink_file "$SCRIPT_DIR/konsole-theme-switcher.service" "$HOME/.config/systemd/user/konsole-theme-switcher.service"

  # Reload systemd and enable service
  systemctl --user daemon-reload
  systemctl --user enable --now konsole-theme-switcher.service

  success "Konsole theme switcher installed and running"
}

main
