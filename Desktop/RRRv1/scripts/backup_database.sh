#!/bin/bash

################################################################################
# RRRv1 Database Backup Script
# Automated backup of trading database with compression and cleanup
#
# Usage:
#   bash scripts/backup_database.sh              # Create backup
#   bash scripts/backup_database.sh --cleanup    # Cleanup old backups
#   bash scripts/backup_database.sh --schedule   # Schedule via crontab
#
# Setup for automatic hourly backups via crontab:
#   0 * * * * cd /path/to/RRRv1 && bash scripts/backup_database.sh
################################################################################

set -e  # Exit on error

# Configuration
BACKUP_DIR="backups"
DB_PATH="logs/trading_data.db"
LOG_FILE="logs/backup.log"
RETENTION_DAYS=30
MAX_BACKUPS=100

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"
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

# Check if database exists
check_database_exists() {
    if [ ! -f "$DB_PATH" ]; then
        log_error "Database file not found: $DB_PATH"
        return 1
    fi
    return 0
}

# Create backup
backup_database() {
    log_info "Starting database backup..."

    if ! check_database_exists; then
        log_error "Cannot backup: database not found"
        return 1
    fi

    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="${BACKUP_DIR}/trading_data_backup_${timestamp}.db"
    local backup_file_gz="${backup_file}.gz"

    # Create backup using sqlite3
    if command -v sqlite3 &> /dev/null; then
        # Use sqlite3 if available
        sqlite3 "$DB_PATH" ".backup '$backup_file'"
    else
        # Fallback: simple file copy (less safe during writes)
        log_warn "sqlite3 command not found, using simple file copy"
        cp "$DB_PATH" "$backup_file"
    fi

    if [ -f "$backup_file" ]; then
        local size=$(du -h "$backup_file" | cut -f1)

        # Compress backup
        gzip "$backup_file"
        local compressed_size=$(du -h "$backup_file_gz" | cut -f1)

        log_info "Backup created successfully!"
        log_info "  Location: $backup_file_gz"
        log_info "  Original size: $size"
        log_info "  Compressed size: $compressed_size"

        return 0
    else
        log_error "Failed to create backup"
        return 1
    fi
}

# Cleanup old backups
cleanup_backups() {
    log_info "Cleaning up backups older than ${RETENTION_DAYS} days..."

    local count=0
    local deleted=0

    for backup_file in $(find "$BACKUP_DIR" -name "trading_data_backup_*.db.gz" -type f | sort); do
        count=$((count + 1))

        # Get file modification time
        local mod_time=$(stat -f %m "$backup_file" 2>/dev/null || stat -c %Y "$backup_file" 2>/dev/null)
        local current_time=$(date +%s)
        local file_age_days=$(( (current_time - mod_time) / 86400 ))

        if [ $file_age_days -gt $RETENTION_DAYS ]; then
            log_info "Deleting old backup: $(basename $backup_file) (${file_age_days} days old)"
            rm -f "$backup_file"
            deleted=$((deleted + 1))
        fi
    done

    # Keep only MAX_BACKUPS most recent backups
    local total=$(find "$BACKUP_DIR" -name "trading_data_backup_*.db.gz" -type f | wc -l)
    if [ $total -gt $MAX_BACKUPS ]; then
        log_warn "Found $total backups (max: $MAX_BACKUPS), removing oldest..."

        find "$BACKUP_DIR" -name "trading_data_backup_*.db.gz" -type f | \
            sort | head -n $((total - MAX_BACKUPS)) | while read old_backup; do
            log_info "Deleting oldest backup: $(basename $old_backup)"
            rm -f "$old_backup"
            deleted=$((deleted + 1))
        done
    fi

    log_info "Cleanup complete: deleted $deleted old backups, kept $((count - deleted)) backups"
}

# Verify backup integrity
verify_backup() {
    log_info "Verifying backup integrity..."

    local latest_backup=$(find "$BACKUP_DIR" -name "trading_data_backup_*.db.gz" -type f | sort | tail -1)

    if [ -z "$latest_backup" ]; then
        log_error "No backup found to verify"
        return 1
    fi

    # Decompress to temp file and check
    local temp_backup="/tmp/verify_backup_$$.db"
    gunzip -c "$latest_backup" > "$temp_backup"

    if sqlite3 "$temp_backup" "PRAGMA integrity_check;" | grep -q "ok"; then
        log_info "✓ Backup integrity verified: $latest_backup"
        rm -f "$temp_backup"
        return 0
    else
        log_error "✗ Backup integrity check failed: $latest_backup"
        rm -f "$temp_backup"
        return 1
    fi
}

# Show backup status
show_status() {
    log_info "Backup Status:"
    log_info "  Database: $DB_PATH"
    log_info "  Backup location: $BACKUP_DIR"
    log_info "  Retention period: ${RETENTION_DAYS} days"
    log_info "  Max backups: $MAX_BACKUPS"

    local count=$(find "$BACKUP_DIR" -name "trading_data_backup_*.db.gz" -type f 2>/dev/null | wc -l)
    log_info "  Backups stored: $count"

    if [ $count -gt 0 ]; then
        log_info ""
        log_info "Recent backups:"
        find "$BACKUP_DIR" -name "trading_data_backup_*.db.gz" -type f 2>/dev/null | \
            sort -r | head -5 | while read backup; do
            local size=$(du -h "$backup" | cut -f1)
            local date=$(basename "$backup" | sed 's/trading_data_backup_//; s/.db.gz//')
            printf "    %-20s %s\n" "$date" "$size"
        done
    fi
}

# Main logic
main() {
    case "${1:-}" in
        --cleanup)
            cleanup_backups
            ;;
        --verify)
            verify_backup
            ;;
        --status)
            show_status
            ;;
        --schedule)
            log_info "To schedule hourly backups, add this to your crontab:"
            log_info "  crontab -e"
            log_info "Then add:"
            log_info "  0 * * * * cd $(pwd) && bash scripts/backup_database.sh"
            ;;
        *)
            backup_database
            cleanup_backups
            verify_backup
            show_status
            ;;
    esac
}

# Run main
main "$@"
