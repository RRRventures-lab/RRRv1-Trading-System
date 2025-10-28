#!/bin/bash

################################################################################
# RRRv1 Database Restore Script
# Safely restore trading database from backup
#
# Usage:
#   bash scripts/restore_database.sh <backup_file>
#   bash scripts/restore_database.sh --list          # List available backups
#   bash scripts/restore_database.sh --latest       # Restore from latest backup
#
# Examples:
#   bash scripts/restore_database.sh backups/trading_data_backup_20241028_120000.db.gz
#   bash scripts/restore_database.sh --latest
################################################################################

set -e  # Exit on error

# Configuration
BACKUP_DIR="backups"
DB_PATH="logs/trading_data.db"
LOG_FILE="logs/restore.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Ensure directories exist
mkdir -p "$(dirname "$LOG_FILE")"

# Logging function
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] ${level}: ${message}" | tee -a "$LOG_FILE"
}

log_info() {
    log "${GREEN}INFO${NC}" "$@"
}

log_error() {
    log "${RED}ERROR${NC}" "$@"
}

log_warn() {
    log "${YELLOW}WARN${NC}" "$@"
}

log_action() {
    log "${BLUE}ACTION${NC}" "$@"
}

# List available backups
list_backups() {
    log_info "Available backups:"

    if [ ! -d "$BACKUP_DIR" ]; then
        log_error "Backup directory not found: $BACKUP_DIR"
        return 1
    fi

    local count=0
    find "$BACKUP_DIR" -name "trading_data_backup_*.db.gz" -type f 2>/dev/null | \
        sort -r | while read backup; do
        count=$((count + 1))
        local size=$(du -h "$backup" | cut -f1)
        local date=$(basename "$backup" | sed 's/trading_data_backup_//; s/.db.gz//')
        printf "  %2d. %-20s %s\n" "$count" "$date" "$size"
    done

    if [ $count -eq 0 ]; then
        log_error "No backups found in $BACKUP_DIR"
        return 1
    fi
}

# Get latest backup
get_latest_backup() {
    local latest=$(find "$BACKUP_DIR" -name "trading_data_backup_*.db.gz" -type f 2>/dev/null | \
        sort -r | head -1)

    if [ -z "$latest" ]; then
        log_error "No backups found in $BACKUP_DIR"
        return 1
    fi

    echo "$latest"
}

# Verify backup file
verify_backup_file() {
    local backup_file=$1

    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi

    # Check if file is gzipped
    if ! file "$backup_file" | grep -q "gzip"; then
        log_warn "File does not appear to be gzip compressed"
    fi

    # Try to decompress and check integrity
    local temp_db="/tmp/verify_restore_$$.db"
    if ! gunzip -c "$backup_file" > "$temp_db" 2>/dev/null; then
        log_error "Failed to decompress backup file"
        rm -f "$temp_db"
        return 1
    fi

    # Check SQLite integrity
    if ! sqlite3 "$temp_db" "PRAGMA integrity_check;" 2>/dev/null | grep -q "ok"; then
        log_error "Backup file integrity check failed"
        rm -f "$temp_db"
        return 1
    fi

    rm -f "$temp_db"
    log_info "✓ Backup file verification passed"
    return 0
}

# Create safety backup before restore
create_safety_backup() {
    if [ ! -f "$DB_PATH" ]; then
        log_warn "Current database not found - nothing to backup"
        return 0
    fi

    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local safety_backup="${BACKUP_DIR}/pre_restore_backup_${timestamp}.db.gz"

    log_action "Creating safety backup of current database..."
    mkdir -p "$BACKUP_DIR"

    if command -v sqlite3 &> /dev/null; then
        sqlite3 "$DB_PATH" ".backup '${safety_backup%.gz}'"
    else
        cp "$DB_PATH" "${safety_backup%.gz}"
    fi

    gzip "${safety_backup%.gz}" 2>/dev/null
    log_info "Safety backup created: $safety_backup"
}

# Perform restore
restore_from_backup() {
    local backup_file=$1

    log_action "WARNING: This will overwrite the current database!"
    log_action "Press Ctrl+C to cancel, or enter 'yes' to continue:"
    read -p "Continue? (yes/no): " -r confirmation

    if [ "$confirmation" != "yes" ]; then
        log_info "Restore cancelled by user"
        return 1
    fi

    # Create safety backup
    create_safety_backup

    log_action "Restoring database from: $backup_file"

    # Decompress backup
    local temp_db="/tmp/restore_$$.db"
    if ! gunzip -c "$backup_file" > "$temp_db" 2>/dev/null; then
        log_error "Failed to decompress backup file"
        rm -f "$temp_db"
        return 1
    fi

    # Verify decompressed database
    if ! sqlite3 "$temp_db" "PRAGMA integrity_check;" 2>/dev/null | grep -q "ok"; then
        log_error "Decompressed database integrity check failed"
        rm -f "$temp_db"
        return 1
    fi

    # Stop any running processes using the database
    log_warn "Stopping any processes that may be using the database..."

    # Create backup directory for database
    mkdir -p "$(dirname "$DB_PATH")"

    # Restore database
    mv "$temp_db" "$DB_PATH"

    # Verify restored database
    if ! sqlite3 "$DB_PATH" "PRAGMA integrity_check;" 2>/dev/null | grep -q "ok"; then
        log_error "Restored database integrity check failed"
        log_error "This is critical - attempting to restore from safety backup"

        # Try to restore safety backup
        local safety_backups=$(find "$BACKUP_DIR" -name "pre_restore_backup_*.db.gz" -type f | sort -r | head -1)
        if [ ! -z "$safety_backups" ]; then
            log_action "Restoring from safety backup..."
            gunzip -c "$safety_backups" > "$DB_PATH"
            log_info "Recovery successful - database restored to pre-restore state"
        fi

        return 1
    fi

    log_info "✓ Database restore completed successfully!"
    log_info "Restored from: $backup_file"
    log_info "Database location: $DB_PATH"

    return 0
}

# Show usage
show_usage() {
    cat << EOF
${BLUE}RRRv1 Database Restore Script${NC}

Usage:
  bash scripts/restore_database.sh <backup_file>
  bash scripts/restore_database.sh --list
  bash scripts/restore_database.sh --latest
  bash scripts/restore_database.sh --help

Options:
  <backup_file>    Restore from specific backup file
  --list           List all available backups
  --latest         Restore from most recent backup
  --help           Show this help message

Examples:
  bash scripts/restore_database.sh backups/trading_data_backup_20241028_120000.db.gz
  bash scripts/restore_database.sh --latest
  bash scripts/restore_database.sh --list

${YELLOW}WARNING:${NC} Restore will overwrite the current database.
A safety backup will be created before restore.

EOF
}

# Main logic
main() {
    case "${1:-}" in
        --help|-h)
            show_usage
            ;;
        --list|-l)
            list_backups
            ;;
        --latest)
            log_info "Restoring from latest backup..."
            local latest=$(get_latest_backup) || exit 1
            log_info "Latest backup: $latest"
            verify_backup_file "$latest" || exit 1
            restore_from_backup "$latest"
            ;;
        *)
            if [ -z "${1:-}" ]; then
                log_error "Backup file not specified"
                show_usage
                exit 1
            fi

            local backup_file="$1"
            verify_backup_file "$backup_file" || exit 1
            restore_from_backup "$backup_file"
            ;;
    esac
}

# Run main
main "$@"
