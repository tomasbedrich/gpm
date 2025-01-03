#!/bin/bash
# wget -O - https://raw.githubusercontent.com/tomasbedrich/gpm/refs/heads/main/install/uninstall.sh | bash -

# based on https://github.com/hacs/get

function uninstall_gpm() {
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

        if [ -d "$haPath/gpm/github_com.tomasbedrich.gpm" ]; then
            info "Removing GPM repository..."
            rm -rf "$haPath/gpm/github_com.tomasbedrich.gpm"
        else
            warn "GPM repository not found."
        fi

        if [ -L "$haPath/custom_components/gpm" ]; then
            info "Removing GPM custom_component..."
            rm -rf "$haPath/custom_components/gpm"
        else
            warn "GPM custom_component not found."
        fi

        if [ -d "$haPath/gpm" ]; then
            if [ -z "$(ls -A "$haPath/gpm")" ]; then
                info "Removing '$haPath/gpm'..."
                rmdir "$haPath/gpm"
            else
                warn "'$haPath/gpm' is not empty, skipping."
            fi
        else
            warn "'$haPath/gpm' directory not found."
        fi

        info "Uninstallation complete."
        info "Restart Home Assistant to finalize the removal of GPM."

    else
        echo
        error "Could not find the directory for Home Assistant" false
        echo "Manually change the directory to the root of your Home Assistant configuration"
        echo "With the user that is running Home Assistant"
        echo "and run the script again"
        exit 1
    fi
}

uninstall_gpm
