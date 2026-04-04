#!/bin/bash
# main.sh - Entry point for Mini Game Hub
# Handles user authentication (login/register) for two players
# Passwords are hashed with SHA-256 before storage in users.tsv

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USERS_FILE="$SCRIPT_DIR/users.tsv"

# Create users.tsv with header if it doesn't exist
if [ ! -f "$USERS_FILE" ]; then
    printf "username\tpassword_hash\n" > "$USERS_FILE"
fi

# Function to compute SHA-256 hash of a string
hash_password() {
    # Use shasum on macOS, sha256sum on Linux
    if command -v sha256sum &> /dev/null; then
        echo -n "$1" | sha256sum | awk '{print $1}'
    elif command -v shasum &> /dev/null; then
        echo -n "$1" | shasum -a 256 | awk '{print $1}'
    else
        echo "Error: No SHA-256 hashing tool found." >&2
        exit 1
    fi
}

# Function to check if a username exists in users.tsv
user_exists() {
    local username="$1"
    # Skip header line, check first column
    awk -F'\t' -v user="$username" 'NR>1 && $1==user {found=1} END {exit !found}' "$USERS_FILE"
}

# Function to get stored password hash for a username
get_stored_hash() {
    local username="$1"
    awk -F'\t' -v user="$username" 'NR>1 && $1==user {print $2}' "$USERS_FILE"
}

# Function to register a new user
register_user() {
    local username="$1"
    local password="$2"
    local hashed
    hashed=$(hash_password "$password")
    printf "%s\t%s\n" "$username" "$hashed" >> "$USERS_FILE"
    echo "User '$username' registered successfully!"
}

# Function to authenticate a single player
authenticate_player() {
    local player_num="$1"
    local other_username="$2"
    local username password hashed stored_hash

    echo "========================================="
    echo "  Player $player_num Authentication"
    echo "========================================="

    while true; do
        read -p "Enter username for Player $player_num: " username

        # Validate username is not empty
        if [ -z "$username" ]; then
            echo "Username cannot be empty. Try again."
            continue
        fi

        # Ensure Player 2 has a different username than Player 1
        if [ -n "$other_username" ] && [ "$username" = "$other_username" ]; then
            echo "This username is already logged in as Player 1. Please use a different username."
            continue
        fi

        if user_exists "$username"; then
            # User exists - prompt for password and verify
            while true; do
                read -sp "Enter password: " password
                echo
                hashed=$(hash_password "$password")
                stored_hash=$(get_stored_hash "$username")

                if [ "$hashed" = "$stored_hash" ]; then
                    echo "Login successful! Welcome back, $username."
                    echo "$username"
                    return 0
                else
                    echo "Incorrect password. Please try again."
                fi
            done
        else
            # User doesn't exist - offer registration
            read -p "Username '$username' not found. Register? (y/n): " choice
            if [ "$choice" = "y" ] || [ "$choice" = "Y" ]; then
                read -sp "Create a password: " password
                echo
                if [ -z "$password" ]; then
                    echo "Password cannot be empty. Try again."
                    continue
                fi
                register_user "$username" "$password"
                echo "$username"
                return 0
            else
                echo "Let's try again."
            fi
        fi
    done
}

# ---- Main Flow ----
echo "============================================"
echo "     Welcome to the Mini Game Hub!"
echo "============================================"
echo ""

# Authenticate Player 1
player1=$(authenticate_player 1 "")
echo ""

# Authenticate Player 2 (must be different from Player 1)
player2=$(authenticate_player 2 "$player1")
echo ""

echo "============================================"
echo "  Both players authenticated successfully!"
echo "  Player 1: $player1"
echo "  Player 2: $player2"
echo "============================================"
echo ""

# Launch the Python game engine with both usernames
python3 "$SCRIPT_DIR/game.py" "$player1" "$player2"
