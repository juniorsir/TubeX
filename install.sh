#!/bin/bash

# =======================================================
#    TubeX - Advanced Dynamic Installer
#
#    Features:
#    - ASCII art welcome screen
#    - Dependency checks for git and pip
#    - Multi-stage animated progress bar
#    - Robust error handling with detailed logs
#    - Non-interactive git to prevent hanging
#    - Termux compatibility for log files
#    - Audio feedback on success
# =======================================================

# --- Configuration ---
# IMPORTANT: Replace this with your actual PUBLIC GitHub repository URL
REPO_URL="https://github.com/juniorsir/TubeX.git"

# --- UI Colors and Styles ---
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# --- Helper Functions ---
print_step() {
    echo -e "\n${BLUE}STEP: $1${NC}"
}

print_error() {
    echo -e "\n${RED}${BOLD}ERROR: $1${NC}"
}

# This function creates and updates a text-based progress bar
progress_bar() {
    local duration=$1
    local message="$2"
    local progress=0
    local width=40 # Width of the progress bar in characters

    while [ $progress -le $duration ]; do
        local percent=$((progress * 100 / duration))
        local num_chars=$((progress * width / duration))
        
        # Build the progress bar string
        local bar=""
        for ((i=0; i<num_chars; i++)); do bar+="="; done
        for ((i=num_chars; i<width; i++)); do bar+=" "; done
        
        # Print the bar and the dynamic message, clearing the rest of the line
        echo -ne "  [${bar}] ${percent}% - ${message}\033[0K\r"
        
        sleep 0.1
        progress=$((progress + 1))
    done
    echo "" # Newline at the end
}

# --- Core Logic Functions ---
check_dependencies() {
    print_step "Checking for required tools..."
    local missing=0
    
    if ! command -v git &> /dev/null; then
        print_error "'git' is not installed."
        echo -e "${YELLOW}Please install it with 'pkg install git' or 'sudo apt install git' and run this script again.${NC}"
        missing=1
    fi
    
    if ! command -v pip &> /dev/null; then
        print_error "'pip' is not installed."
        echo -e "${YELLOW}Please ensure Python and pip are installed, then run this script again.${NC}"
        missing=1
    fi

    if [ $missing -eq 1 ]; then
        exit 1
    fi
    
    echo -e "  ${GREEN}All dependencies found!${NC}"
}

install_tubex() {
    print_step "Installing TubeX..."
    
    # Use the user's home directory for a safe, writable log file path
    local log_file="$HOME/tubex_install.log"
    
    progress_bar 10 "Preparing installation..."
    
    # GIT_TERMINAL_PROMPT=0 tells git to never prompt for a username/password.
    # It will fail immediately if authentication is required (e.g., private repo).
    # Output is redirected to the safe log file path.
    GIT_TERMINAL_PROMPT=0 pip install git+$REPO_URL > "$log_file" 2>&1 &
    local pid=$!
    
    # While the real installation runs, we show a dynamic progress bar
    # with simulated status messages for a better user experience.
    progress_bar 20 "Downloading package from GitHub..."
    progress_bar 30 "Installing dependencies..."
    
    # Wait for the actual pip command to finish
    wait $pid
    local exit_code=$?
    
    progress_bar 10 "Finalizing installation..."

    if [ $exit_code -ne 0 ]; then
        echo "" # Newline for clean formatting
        print_error "Installation failed."
        echo -e "${YELLOW}This can happen if the GitHub repository is private or the URL is incorrect.${NC}"
        echo -e "${YELLOW}Please ensure the repository is public and the URL in the installer is correct.${NC}"
        echo -e "${YELLOW}The full installation log has been saved to: ${log_file}${NC}"
        exit 1
    fi
    
    # Clean up the log file on success
    rm -f "$log_file"
}

# --- ======================================================= ---
# ---                   SCRIPT EXECUTION                      ---
# --- ======================================================= ---

# 1. Display the ASCII art welcome message
clear
echo -e "${BLUE}"
cat << "EOF"
 _____     _         __   __
|_   _|   | |        \ \ / /
  | |_   _| |__   ___ \ V /
  | | | | | '_ \ / _ \/ \ \
  | | |_| | |_) |  __/ /^\ \
  \_/\__,_|_.__/ \___\/   \/

EOF
echo -e "${NC}"
echo -e "${BOLD}Welcome to the Advanced TubeX Installer!${NC}"
echo ""

# 2. Check for dependencies first
check_dependencies

# 3. If checks pass, run the installation
install_tubex

# 4. Play a success sound and show final instructions
echo -e "${GREEN}${BOLD}Installation Complete!${NC}"
echo -e '\a' # This prints the terminal "bell" sound

echo ""
echo -e "--------------------------------------------------"
echo -e "You can now run the application from anywhere by typing:"
echo -e "\n  ${GREEN}tubex${NC}\n"
echo -e "To run in developer mode, use:"
echo -e "\n  ${GREEN}tubex --debug${NC}\n"
echo -e "Enjoy TubeX!"
echo -e "--------------------------------------------------"
echo ""
