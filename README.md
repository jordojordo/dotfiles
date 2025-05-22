# My Dotfiles

Welcome to my dotfiles repository, my personal collection of configurations and tweaks that make my system uniquely mine. Inspired by [Holman’s approach](https://github.com/holman/dotfiles), these dotfiles are organized by topic for a modular and maintainable setup.

## Overview

This repository houses all my system configurations, organized into topic areas that cover everything from shell customizations to application settings. I've extended the original concept to include:

**Cross-platform Package Installation**:

Whether you're on macOS or an Arch-based system, the installation scripts automatically handle package installation.

- **macOS**: Uses a `Brewfile` to manage packages via Homebrew.
- **Arch Linux and Derivatives**: Uses a dedicated `packages.arch.list` file, installing packages with either `yay` (if available) or `pacman`.
- **Fedora**: Uses `dnf` to install packages listed in `packages.fedora.list`.

**Manageable Package List**:
All desired packages are listed in a dedicated `packages.*.list` file, making updates and customization straightforward.

## Directory Structure

- **bin/**:
Contains scripts added to your `$PATH` (e.g., the `dot` command for installing dependencies).
- **topics/**:
Each file ending in `.zsh` is sourced into your shell:
  - `topics/path.zsh` sets up your system path.
  - `topics/completion.zsh` loads shell completions.
- **\*.symlink**:
Files with this extension are symlinked into your home directory (e.g., `zshrc.symlink` becomes `~/.zshrc`).
- **packages.list**:
A plain text file listing all the packages you want to install. Lines starting with `#` are treated as comments.

## Installation

Clone the repository and run the bootstrap script to set up your environment:

```sh
git clone https://github.com/jordojordo/dotfiles ~/.dotfiles
cd ~/.dotfiles
scripts/bootstrap
```

The bootstrap script creates symlinks for your dotfiles and performs initial configuration.

## Package Installation

This repository uses a smart package installer that reads from the packages.list file. It works as follows:

- **macOS**:
Uses Homebrew with `brew bundle` to install packages listed in the `Brewfile`.
- **Arch Linux and Derivatives**:
Checks for an Arch-based system (by verifying `/etc/arch-release`) and then:
  - Uses `yay` if available (which supports AUR packages).
  - Falls back to `pacman` if `yay` isn’t installed.

Simply update the `packages.list` file to include the packages you need—one per line. Comments (lines beginning with `#`) are supported for clarity.

## Customization

- **Adding Topics**:
Create new topic directories or files (e.g., `topics/python.zsh`) to extend your configuration.
- **Modifying Scripts**:
Tweak scripts in `bin/` (or add new ones) to automate your workflow.

## Troubleshooting

- **Symlink Issues**:
Verify that symlinks in your home directory correctly point to files in `~/.dotfiles`.
- **Package Manager Errors**:
Make sure your package manager (`homebrew`, `pacman`, or `yay`) is installed and up-to-date.
- **Script Errors**:
Review output messages from the installation scripts for any errors, and adjust the configuration accordingly.

## Contributions

Feel free to fork this repository and make it your own. If you have suggestions, improvements, or find bugs, please open an issue or submit a pull request.
