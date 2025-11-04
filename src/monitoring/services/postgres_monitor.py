"""PostgreSQL monitor for collecting metrics."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from monitoring.base_monitor import BaseMonitor


class PostgresMonitor(BaseMonitor):
    """Monitor for PostgreSQL service."""
    
    def __init__(self, endpoint="localhost:5432", **kwargs):
        super().__init__(name="PostgresMonitor", **kwargs)
        # Parse endpoint
        if ':' in endpoint:
            self.host, port = endpoint.split(':')
            self.port = int(port)
        else:
            self.host = endpoint
            self.port = 5432
    
    def collect_service_metrics(self):
        """Collect PostgreSQL-specific metrics."""
        metrics = {}
        
        try:
            import psycopg2
            
            # Connection string
            conn_string = f"dbname=postgres user=postgres password=mysecretpassword host={self.host} port={self.port}"
            
            # Try to connect and get stats
            import time
            start = time.time()
            
            conn = psycopg2.connect(conn_string, connect_timeout=5)
            cur = conn.cursor()
            
            metrics["connection_time_ms"] = (time.time() - start) * 1000
            metrics["service_available"] = True
            
            # Get database size
            cur.execute("SELECT pg_database_size('postgres');")
            db_size = cur.fetchone()[0]
            metrics["database_size_bytes"] = db_size
            metrics["database_size_mb"] = round(db_size / (1024 * 1024), 2)
            
            # Get connection count
            cur.execute("SELECT count(*) FROM pg_stat_activity;")
            conn_count = cur.fetchone()[0]
            metrics["active_connections"] = conn_count
            
            # Get transaction stats
            cur.execute("""
                SELECT 
                    xact_commit, 
                    xact_rollback,
                    blks_read,
                    blks_hit
                FROM pg_stat_database 
                WHERE datname = 'postgres';
            """)
            stats = cur.fetchone()
            if stats:
                metrics["transactions_committed"] = stats[0]
                metrics["transactions_rolled_back"] = stats[1]
                metrics["blocks_read"] = stats[2]
                metrics["blocks_hit"] = stats[3]
                
                # Calculate cache hit ratio
                total_reads = stats[2] + stats[3]
                if total_reads > 0:
                    metrics["cache_hit_ratio"] = round((stats[3] / total_reads) * 100, 2)
            
            cur.close()
            conn.close()
            
        except ImportError:
            metrics["service_available"] = False
            metrics["error"] = "psycopg2 not installed"
        except Exception as e:
            metrics["service_available"] = False
            metrics["error"] = str(e)
        
        return metrics
