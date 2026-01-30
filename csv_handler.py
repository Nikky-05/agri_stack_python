import pandas as pd
from typing import Dict, Any
from config import CSV_FILES, INDICATORS, DIMENSIONS

class CSVHandler:
    @staticmethod
    def execute_analytics(intent: Dict[str, Any], user_lgd: str) -> Dict[str, Any]:
        ind_meta = INDICATORS[intent["indicator"]]
        dim_key = intent["dimension"]
        dim_meta = DIMENSIONS.get(dim_key)

        # Determine file source based on requirement mapping
        file_map = {"crop_area_data": "crop_area", "aggregate_summary_data": "aggregate", "cultivated_summary_data": "cultivated"}
        csv_key = file_map[ind_meta["table"]]
        
        df = pd.read_csv(CSV_FILES[csv_key])
        df['state_lgd_code'] = df['state_lgd_code'].astype(str)
        df = df[df['state_lgd_code'] == str(user_lgd)]

        val_col = ind_meta["column"]

        if dim_meta:
            label_col = dim_meta["column"]
            # Ensure the column exists in the CSV
            if label_col in df.columns:
                result = df.groupby(label_col)[val_col].sum().sort_values(ascending=False)
                return {
                    "title": f"{ind_meta['title']} by {dim_meta['title']}",
                    "unit": ind_meta["unit"],
                    "labels": [str(i) for i in result.index],
                    "values": [float(v) for v in result.values],
                    "chart_type": "bar"
                }
            else:
                # Professional Fallback: Return a message indicating the dimension is unavailable
                return {
                    "title": ind_meta["title"],
                    "unit": ind_meta["unit"],
                    "labels": ["Total (Requested " + dim_meta['title'] + " Unavailable)"],
                    "values": [float(df[val_col].sum())],
                    "chart_type": "kpi",
                    "note": f"Dimension '{dim_meta['title']}' not found in dataset."
                }
        
        # Summary Case: No dimension requested
        total = float(df[val_col].sum())
        return {
            "title": ind_meta["title"],
            "unit": ind_meta["unit"],
            "labels": ["Total"],
            "values": [total],
            "chart_type": "kpi"
        }
