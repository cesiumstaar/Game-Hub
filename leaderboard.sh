#!/bin/bash
# leaderboard.sh - Reads history.csv and displays a formatted leaderboard table
# Usage: bash leaderboard.sh <history_file> <sort_metric>
# sort_metric: "wins", "losses", or "ratio"

HISTORY_FILE="${1:-history.csv}"
SORT_METRIC="${2:-wins}"

# Check if history file exists
if [ ! -f "$HISTORY_FILE" ]; then
    echo "No game history found."
    exit 0
fi

# Count total lines (excluding header)
TOTAL_GAMES=$(tail -n +2 "$HISTORY_FILE" | wc -l | tr -d ' ')
if [ "$TOTAL_GAMES" -eq 0 ]; then
    echo "No games played yet."
    exit 0
fi

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║               LEADERBOARD                       ║"
echo "╠══════════════════════════════════════════════════╣"
echo ""

# Extract unique players (skip "draw")
PLAYERS=$(tail -n +2 "$HISTORY_FILE" | awk -F',' '{
    if ($1 != "draw") print $1;
    if ($2 != "draw") print $2;
}' | sort -u)

# Extract unique game names (field 4 may contain spaces — read full field)
GAMES_FILE=$(mktemp)
tail -n +2 "$HISTORY_FILE" | awk -F',' '{print $4}' | sort -u > "$GAMES_FILE"

# Build header
printf "  %-14s" "Player"
while IFS= read -r game; do
    printf "│ %-6s %-6s %-6s " "W" "L" "W/L"
done < "$GAMES_FILE"
printf "│ %-6s %-6s %-6s\n" "Tot-W" "Tot-L" "Tot-R"

# Separator
printf "  "
printf '%.0s─' {1..14}
while IFS= read -r game; do
    printf "┼"
    printf '%.0s─' {1..22}
done < "$GAMES_FILE"
printf "┼"
printf '%.0s─' {1..22}
printf "\n"

# Temporary file for sorting
TEMP_FILE=$(mktemp)

# Calculate stats for each player
for player in $PLAYERS; do
    TOTAL_WINS=0
    TOTAL_LOSSES=0
    LINE=""

    while IFS= read -r game; do
        # Count wins for this player in this game
        WINS=$(tail -n +2 "$HISTORY_FILE" | awk -F',' -v p="$player" -v g="$game" \
            '$1==p && $4==g {count++} END {print count+0}')
        # Count losses for this player in this game
        LOSSES=$(tail -n +2 "$HISTORY_FILE" | awk -F',' -v p="$player" -v g="$game" \
            '$2==p && $4==g {count++} END {print count+0}')

        # Calculate ratio
        if [ "$LOSSES" -eq 0 ]; then
            if [ "$WINS" -gt 0 ]; then
                RATIO="inf"
            else
                RATIO="0.00"
            fi
        else
            RATIO=$(awk "BEGIN {printf \"%.2f\", $WINS/$LOSSES}")
        fi

        LINE="${LINE}$(printf "│ %-6s %-6s %-6s " "$WINS" "$LOSSES" "$RATIO")"
        TOTAL_WINS=$((TOTAL_WINS + WINS))
        TOTAL_LOSSES=$((TOTAL_LOSSES + LOSSES))
    done < "$GAMES_FILE"

    # Calculate total ratio
    if [ "$TOTAL_LOSSES" -eq 0 ]; then
        if [ "$TOTAL_WINS" -gt 0 ]; then
            TOTAL_RATIO="inf"
        else
            TOTAL_RATIO="0.00"
        fi
    else
        TOTAL_RATIO=$(awk "BEGIN {printf \"%.2f\", $TOTAL_WINS/$TOTAL_LOSSES}")
    fi

    TOTAL_PART=$(printf "│ %-6s %-6s %-6s" "$TOTAL_WINS" "$TOTAL_LOSSES" "$TOTAL_RATIO")

    # Store with sort key for later sorting
    case "$SORT_METRIC" in
        wins)
            SORT_KEY=$TOTAL_WINS
            ;;
        losses)
            SORT_KEY=$TOTAL_LOSSES
            ;;
        ratio)
            if [ "$TOTAL_RATIO" = "inf" ]; then
                SORT_KEY=999999
            else
                SORT_KEY=$TOTAL_RATIO
            fi
            ;;
        *)
            SORT_KEY=$TOTAL_WINS
            ;;
    esac

    echo "${SORT_KEY}|$(printf "  %-14s" "$player")${LINE}${TOTAL_PART}" >> "$TEMP_FILE"
done

# Print game name sub-header
printf "  %-14s" ""
while IFS= read -r game; do
    printf "│ %-20s " "$game"
done < "$GAMES_FILE"
printf "│ %-20s\n" "TOTAL"

# Separator
printf "  "
printf '%.0s─' {1..14}
while IFS= read -r game; do
    printf "┼"
    printf '%.0s─' {1..22}
done < "$GAMES_FILE"
printf "┼"
printf '%.0s─' {1..22}
printf "\n"

# Sort and display (descending order)
sort -t'|' -k1 -rn "$TEMP_FILE" | while IFS='|' read -r key rest; do
    echo "$rest"
done

# Cleanup
rm -f "$TEMP_FILE" "$GAMES_FILE"

echo ""
echo "╠══════════════════════════════════════════════════╣"
echo "  Sorted by: $SORT_METRIC | Total games played: $TOTAL_GAMES"
echo "╚══════════════════════════════════════════════════╝"
echo ""
