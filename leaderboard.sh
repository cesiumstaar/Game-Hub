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
echo "============================================================"
echo "                    LEADERBOARD"
echo "============================================================"
echo ""

# Extract unique players from both Winner and Loser columns (skip draws)
PLAYERS=$(tail -n +2 "$HISTORY_FILE" | awk -F',' '{
    if ($1 != "draw") print $1;
    if ($2 != "draw") print $2;
}' | sort -u)

# Extract unique game names
GAMES=$(tail -n +2 "$HISTORY_FILE" | awk -F',' '{print $4}' | sort -u)

# Print header
printf "%-15s" "Player"
for game in $GAMES; do
    printf "| %-12s %-12s %-10s" "${game}-W" "${game}-L" "${game}-R"
done
printf "| %-8s %-8s %-8s\n" "Total-W" "Total-L" "Total-R"

# Print separator line
SEP_LEN=$((15 + $(echo "$GAMES" | wc -w | tr -d ' ') * 37 + 27))
printf '%*s\n' "$SEP_LEN" '' | tr ' ' '-'

# Temporary file for sorting
TEMP_FILE=$(mktemp)

# Calculate stats for each player
for player in $PLAYERS; do
    TOTAL_WINS=0
    TOTAL_LOSSES=0
    LINE=""

    for game in $GAMES; do
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

        LINE="${LINE}$(printf "| %-12s %-12s %-10s" "$WINS" "$LOSSES" "$RATIO")"
        TOTAL_WINS=$((TOTAL_WINS + WINS))
        TOTAL_LOSSES=$((TOTAL_LOSSES + LOSSES))
    done

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

    TOTAL_PART=$(printf "| %-8s %-8s %-8s" "$TOTAL_WINS" "$TOTAL_LOSSES" "$TOTAL_RATIO")

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

    echo "${SORT_KEY}|$(printf "%-15s" "$player")${LINE}${TOTAL_PART}" >> "$TEMP_FILE"
done

# Sort and display (descending order)
sort -t'|' -k1 -rn "$TEMP_FILE" | while IFS='|' read -r key rest; do
    echo "$rest"
done

# Cleanup
rm -f "$TEMP_FILE"

echo ""
echo "------------------------------------------------------------"
echo "  Sorted by: $SORT_METRIC | Total games played: $TOTAL_GAMES"
echo "============================================================"
echo ""
