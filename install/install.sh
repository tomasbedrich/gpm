#!/bin/bash
# wget -O - https://raw.githubusercontent.com/tomasbedrich/gpm/refs/heads/main/install/install.sh | bash -

# based on https://github.com/hacs/get

function run() {
    set -e

    RED_COLOR='\033[0;31m'
    GREEN_COLOR='\033[0;32m'
    GREEN_YELLOW='\033[1;33m'
    NO_COLOR='\033[0m'

    declare haPath
    declare -a paths=(
        "$PWD"
        "$PWD/config"
        "/config"
        "/homeassistant"
        "$HOME/.homeassistant"
        "/usr/share/hassio/homeassistant"
    )

    function info () { echo -e "${GREEN_COLOR}INFO: $1${NO_COLOR}";}
    function warn () { echo -e "${GREEN_YELLOW}WARN: $1${NO_COLOR}";}
    function error () { echo -e "${RED_COLOR}ERROR: $1${NO_COLOR}"; if [ "$2" != "false" ]; then exit 1;fi; }

    function checkRequirement () {
        if [ -z "$(command -v "$1")" ]; then
            error "'$1' is not installed"
        fi
    }

    checkRequirement "git"

    info "Trying to find the correct directory..."
    for path in "${paths[@]}"; do
        if [ -n "$haPath" ]; then
            break
        fi

        if [ -f "$path/.HA_VERSION" ]; then
            haPath="$path"
        fi
    done

    if [ -n "$haPath" ]; then
        info "Found Home Assistant configuration directory at '$haPath'"
        cd "$haPath" || error "Could not access '$haPath'"

        if [ ! -d "$haPath/gpm" ]; then
            info "Creating '$haPath/gpm' directory..."
            mkdir "$haPath/gpm"
        fi
        cd "$haPath/gpm" || error "Could not access '$haPath/gpm'"

        if [ ! -d "$haPath/custom_components" ]; then
            info "Creating '$haPath/custom_components' directory..."
            mkdir "$haPath/custom_components"
        fi
        cd "$haPath/custom_components" || error "Could not access '$haPath/custom_components'"

        if [ -d "$haPath/gpm/github_com.tomasbedrich.gpm" ]; then
            warn "GPM repository is already cloned, cleaning up..."
            rm -rf "$haPath/gpm/github_com.tomasbedrich.gpm"
        fi

        if [ -L "$haPath/custom_components/gpm" ]; then
            warn "GPM custom_component already exist, cleaning up..."
            rm -rf "$haPath/custom_components/gpm"
        fi

        info "Cloning GPM..."
        git clone --quiet "https://github.com/tomasbedrich/gpm" "$haPath/gpm/github_com.tomasbedrich.gpm"

        info "Installing GPM as custom_component..."
        ln -s "../gpm/github_com.tomasbedrich.gpm/custom_components/gpm/" "$haPath/custom_components/gpm"

        info "Installation complete."
        info "Restart Home Assistant to start using GPM."

    else
        echo
        error "Could not find the directory for Home Assistant" false
        echo "Manually change the directory to the root of your Home Assistant configuration"
        echo "With the user that is running Home Assistant"
        echo "and run the script again"
        exit 1
    fi
}

run
