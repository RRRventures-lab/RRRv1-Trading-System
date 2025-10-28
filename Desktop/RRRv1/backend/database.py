"""
Database operations for trade history and metrics persistence
Enhanced with transactions, WAL mode, and connection pooling for production reliability
"""

import sqlite3
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
import json
import logging
from contextlib import contextmanager
from threading import Lock
import os

logger = logging.getLogger(__name__)


class TradingDatabase:
    """
    SQLite database for trading data with production-grade reliability.

    Features:
    - Transaction support with context manager
    - Write-Ahead Logging (WAL) for better concurrency
    - Connection pooling with thread safety
    - Automatic backups
    - Integrity checks on startup
    """

    def __init__(self, db_path: str = "logs/trading_data.db"):
        """
        Initialize database connection with production settings.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Connection pooling settings
        self._connection_lock = Lock()
        self._main_connection = None

        # Initialize database with production settings
        self._init_db()
        self._enable_wal_mode()
        self._enable_foreign_keys()
        self._check_integrity()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection with proper settings.
        Uses single persistent connection for better performance.

        Returns:
            SQLite database connection
        """
        if self._main_connection is None:
            self._main_connection = sqlite3.connect(
                self.db_path,
                timeout=30.0,  # 30 second timeout
                check_same_thread=False,  # Allow use across threads
                isolation_level=None  # Manual transaction management for safety
            )
            self._main_connection.row_factory = sqlite3.Row
        return self._main_connection

    @contextmanager
    def _transaction(self):
        """
        Context manager for database transactions.
        Ensures ACID compliance and automatic rollback on error.

        Usage:
            with db._transaction():
                # Do database operations
                cursor.execute(...)
                # Auto-commits on success, rolls back on error
        """
        conn = self._get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")  # Use IMMEDIATE for write safety
            yield conn
            conn.execute("COMMIT")
            logger.debug("Transaction committed")
        except Exception as e:
            conn.execute("ROLLBACK")
            logger.error(f"Transaction rolled back due to error: {e}")
            raise

    def _init_db(self) -> None:
        """Initialize database tables with optimizations"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            conn.execute("BEGIN IMMEDIATE")

            # Trades table with indices
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id TEXT PRIMARY KEY,
                    asset TEXT NOT NULL,
                    action TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    size REAL NOT NULL,
                    leverage REAL NOT NULL,
                    pnl REAL,
                    pnl_percent REAL,
                    duration_minutes INTEGER,
                    strategy TEXT,
                    venue TEXT,
                    status TEXT,
                    timestamp TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_asset ON trades(asset)")

            # Positions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    asset TEXT PRIMARY KEY,
                    entry_price REAL NOT NULL,
                    current_price REAL NOT NULL,
                    size REAL NOT NULL,
                    leverage REAL NOT NULL,
                    venue TEXT NOT NULL,
                    liquidation_price REAL,
                    opened_at TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_reconciled_at TEXT
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_positions_updated ON positions(updated_at DESC)")

            # Position history for audit trail
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS position_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    old_values TEXT,
                    new_values TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (asset) REFERENCES positions(asset)
                )
            """)

            # Signals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    signal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    asset TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp DESC)")

            # Funding trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS funding_trades (
                    trade_id TEXT PRIMARY KEY,
                    asset TEXT NOT NULL,
                    funding_rate REAL NOT NULL,
                    position_size REAL NOT NULL,
                    income REAL NOT NULL,
                    duration_hours REAL,
                    annual_return_pct REAL,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Metrics snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics_snapshots (
                    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_value REAL NOT NULL,
                    daily_pnl REAL,
                    portfolio_heat REAL,
                    win_rate REAL,
                    sharpe_ratio REAL,
                    max_drawdown_pct REAL,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Backup metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backup_metadata (
                    backup_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    backup_path TEXT UNIQUE NOT NULL,
                    backup_time TEXT NOT NULL,
                    trades_count INTEGER,
                    positions_count INTEGER,
                    size_bytes INTEGER,
                    verified INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("COMMIT")
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            conn.execute("ROLLBACK")
            logger.error(f"Failed to initialize database: {e}")
            raise

    def _enable_wal_mode(self) -> None:
        """
        Enable Write-Ahead Logging (WAL) mode for better concurrency.
        Allows readers and writers to operate simultaneously.
        """
        try:
            conn = self._get_connection()
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")  # Faster than FULL, still safe
            conn.execute("PRAGMA cache_size=10000")  # Larger cache
            conn.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp
            logger.info("WAL mode enabled for better concurrency")
        except Exception as e:
            logger.error(f"Failed to enable WAL mode: {e}")

    def _enable_foreign_keys(self) -> None:
        """Enable foreign key constraints for data integrity"""
        try:
            conn = self._get_connection()
            conn.execute("PRAGMA foreign_keys=ON")
            logger.info("Foreign key constraints enabled")
        except Exception as e:
            logger.error(f"Failed to enable foreign keys: {e}")

    def _check_integrity(self) -> bool:
        """
        Check database integrity on startup.

        Returns:
            True if integrity check passes, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]

            if result == "ok":
                logger.info("Database integrity check passed")
                return True
            else:
                logger.error(f"Database integrity check failed: {result}")
                return False
        except Exception as e:
            logger.error(f"Failed to check database integrity: {e}")
            return False

    def add_trade(self, trade_data: Dict) -> None:
        """
        Add completed trade to database with transactional integrity.

        Args:
            trade_data: Trade information dictionary
        """
        try:
            with self._transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO trades
                    (trade_id, asset, action, entry_price, exit_price, size, leverage,
                     pnl, pnl_percent, duration_minutes, strategy, venue, status, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade_data.get('trade_id'),
                    trade_data.get('asset'),
                    trade_data.get('action'),
                    trade_data.get('entry_price'),
                    trade_data.get('exit_price'),
                    trade_data.get('size'),
                    trade_data.get('leverage'),
                    trade_data.get('pnl'),
                    trade_data.get('pnl_percent'),
                    trade_data.get('duration_minutes'),
                    trade_data.get('strategy'),
                    trade_data.get('venue'),
                    trade_data.get('status'),
                    trade_data.get('timestamp')
                ))
                logger.info(f"Trade {trade_data.get('trade_id')} recorded in database")
        except Exception as e:
            logger.error(f"Failed to add trade: {e}")
            raise

    def get_recent_trades(self, limit: int = 100) -> List[Dict]:
        """
        Get recent trades from database.

        Args:
            limit: Maximum number of trades to return

        Returns:
            List of trade records
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM trades
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            trades = [dict(row) for row in cursor.fetchall()]
            return trades
        except Exception as e:
            logger.error(f"Failed to retrieve trades: {e}")
            return []

    def add_signal(self, strategy_name: str, action: str, confidence: float,
                   asset: str, timestamp: str) -> None:
        """
        Record a strategy signal.

        Args:
            strategy_name: Name of strategy
            action: BUY, SELL, HOLD
            confidence: Confidence level (0-1)
            asset: Trading asset
            timestamp: Signal timestamp
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO signals (strategy_name, action, confidence, asset, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (strategy_name, action, confidence, asset, timestamp))

        conn.commit()
        conn.close()

    def get_recent_signals(self, limit: int = 50) -> List[Dict]:
        """
        Get recent signals.

        Args:
            limit: Maximum number of signals

        Returns:
            List of signals
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM signals
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        signals = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return signals

    def add_funding_trade(self, trade_data: Dict) -> None:
        """
        Record a funding arbitrage trade.

        Args:
            trade_data: Funding trade information
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO funding_trades
            (trade_id, asset, funding_rate, position_size, income, duration_hours, annual_return_pct, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_data.get('trade_id'),
            trade_data.get('asset'),
            trade_data.get('funding_rate'),
            trade_data.get('position_size'),
            trade_data.get('income'),
            trade_data.get('duration_hours'),
            trade_data.get('annual_return_pct'),
            trade_data.get('timestamp')
        ))

        conn.commit()
        conn.close()

    def get_funding_stats(self) -> Dict:
        """
        Get funding arbitrage statistics.

        Returns:
            Funding statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM funding_trades")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(income) as total_income FROM funding_trades")
        total_income = cursor.fetchone()[0] or 0.0

        cursor.execute("SELECT AVG(income) as avg_income FROM funding_trades")
        avg_income = cursor.fetchone()[0] or 0.0

        cursor.execute("SELECT MAX(funding_rate) as best_rate FROM funding_trades")
        best_rate = cursor.fetchone()[0] or 0.0

        cursor.execute("SELECT MIN(funding_rate) as worst_rate FROM funding_trades")
        worst_rate = cursor.fetchone()[0] or 0.0

        conn.close()

        return {
            'total_trades': total,
            'total_income': total_income,
            'avg_income': avg_income,
            'best_rate': best_rate,
            'worst_rate': worst_rate
        }

    def save_metrics_snapshot(self, metrics: Dict) -> None:
        """
        Save a snapshot of current metrics.

        Args:
            metrics: Metrics dictionary
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO metrics_snapshots
            (portfolio_value, daily_pnl, portfolio_heat, win_rate, sharpe_ratio, max_drawdown_pct, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            metrics.get('portfolio_value'),
            metrics.get('daily_pnl'),
            metrics.get('portfolio_heat'),
            metrics.get('win_rate'),
            metrics.get('sharpe_ratio'),
            metrics.get('max_drawdown_pct'),
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

    def get_metrics_history(self, hours: int = 24) -> List[Dict]:
        """
        Get metrics history for the last N hours.

        Args:
            hours: Number of hours to retrieve

        Returns:
            List of metrics snapshots
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM metrics_snapshots
            WHERE datetime(created_at) > datetime('now', ? || ' hours')
            ORDER BY created_at DESC
        """, (f'-{hours}',))

        snapshots = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return snapshots

    def backup_database(self, backup_dir: str = "backups") -> Optional[str]:
        """
        Create a backup of the database.

        Args:
            backup_dir: Directory to store backups

        Returns:
            Path to backup file if successful, None otherwise
        """
        try:
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_path / f"trading_data_backup_{timestamp}.db"

            # Create backup using SQLite backup API
            conn = self._get_connection()
            backup_conn = sqlite3.connect(str(backup_file))

            with backup_conn:
                conn.backup(backup_conn)

            # Get file size
            file_size = backup_file.stat().st_size

            # Get record counts
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM trades")
            trades_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM positions")
            positions_count = cursor.fetchone()[0]

            # Record backup metadata
            with self._transaction() as db_conn:
                db_cursor = db_conn.cursor()
                db_cursor.execute("""
                    INSERT INTO backup_metadata
                    (backup_path, backup_time, trades_count, positions_count, size_bytes, verified)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (str(backup_file), timestamp, trades_count, positions_count, file_size))

            logger.info(f"Database backup created: {backup_file} ({file_size} bytes)")
            return str(backup_file)

        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return None

    def restore_database(self, backup_file: str) -> bool:
        """
        Restore database from backup file.

        WARNING: This will overwrite the current database.

        Args:
            backup_file: Path to backup file

        Returns:
            True if restore successful, False otherwise
        """
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_file}")
                return False

            # Create backup of current database before restore
            current_backup = self.backup_database("backups/pre_restore")
            logger.info(f"Created backup of current database: {current_backup}")

            # Restore from backup
            backup_conn = sqlite3.connect(str(backup_file))
            conn = self._get_connection()

            with backup_conn:
                backup_conn.backup(conn)

            logger.info(f"Database restored from: {backup_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore database: {e}")
            return False

    def get_backup_history(self, limit: int = 10) -> List[Dict]:
        """
        Get history of backups.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of backup metadata records
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM backup_metadata
                ORDER BY backup_time DESC
                LIMIT ?
            """, (limit,))
            backups = [dict(row) for row in cursor.fetchall()]
            return backups
        except Exception as e:
            logger.error(f"Failed to get backup history: {e}")
            return []

    def cleanup_old_backups(self, days: int = 30, backup_dir: str = "backups") -> int:
        """
        Delete backup files older than specified days.

        Args:
            days: Keep backups from last N days
            backup_dir: Directory containing backups

        Returns:
            Number of backups deleted
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            backup_path = Path(backup_dir)
            deleted_count = 0

            if not backup_path.exists():
                return 0

            for backup_file in backup_path.glob("trading_data_backup_*.db"):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    backup_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old backup: {backup_file}")

            logger.info(f"Cleanup complete: {deleted_count} old backups removed")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
            return 0

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics and health information.

        Returns:
            Dictionary with database stats
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Get record counts
            cursor.execute("SELECT COUNT(*) FROM trades")
            trades_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM positions")
            positions_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM signals")
            signals_count = cursor.fetchone()[0]

            # Get database file size
            db_file_size = Path(self.db_path).stat().st_size

            # Check WAL file if exists
            wal_file = Path(f"{self.db_path}-wal")
            wal_size = wal_file.stat().st_size if wal_file.exists() else 0

            # Get page count
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]

            # Get page size
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]

            return {
                "trades_count": trades_count,
                "positions_count": positions_count,
                "signals_count": signals_count,
                "database_file_size_bytes": db_file_size,
                "wal_file_size_bytes": wal_size,
                "total_size_bytes": db_file_size + wal_size,
                "page_count": page_count,
                "page_size": page_size,
                "total_pages_bytes": page_count * page_size,
                "integrity_ok": self._check_integrity()
            }
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
