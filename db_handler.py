import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Any
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, INDICATORS, DIMENSIONS

class DBHandler:
    def __init__(self):
        self.params = {"host": DB_HOST, "port": DB_PORT, "dbname": DB_NAME, "user": DB_USER, "password": DB_PASSWORD}

    def execute_analytics(self, intent: Dict[str, Any], user_lgd: str) -> Dict[str, Any]:
        ind_meta = INDICATORS[intent["indicator"]]
        dim_key = intent["dimension"]
        dim_meta = DIMENSIONS.get(dim_key)

        table = ind_meta["table"]
        val_col = ind_meta["column"]
        
        try:
            conn = psycopg2.connect(**self.params, cursor_factory=RealDictCursor)
            cur = conn.cursor()

            # 1. Validation: Check if columns exist
            cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'")
            existing_cols = [r['column_name'] for r in cur.fetchall()]

            actual_dim = dim_meta['column'] if dim_meta and dim_meta['column'] in existing_cols else None
            label_col = actual_dim if actual_dim else "'Total'"
            group_clause = f"GROUP BY {label_col}" if actual_dim else ""
            
            sql = f"SELECT {label_col} as label, SUM({val_col}) as value FROM {table} WHERE state_lgd_code = '{user_lgd}' {group_clause} ORDER BY value DESC"
            
            cur.execute(sql)
            rows = cur.fetchall()
            cur.close()
            conn.close()

            res = {
                "title": f"{ind_meta['title']} by {dim_meta['title']}" if actual_dim else ind_meta["title"],
                "unit": ind_meta["unit"],
                "labels": [str(r['label']) for r in rows],
                "values": [float(r['value'] or 0) for r in rows],
                "chart_type": "bar" if actual_dim else "kpi",
                "sql_query": sql
            }

            if dim_meta and not actual_dim:
                res["note"] = f"Dimension '{dim_meta['title']}' is currently not available in our {table} records."
            
            return res

        except Exception as e:
            raise Exception(f"Query Execution Error: {str(e)}")
