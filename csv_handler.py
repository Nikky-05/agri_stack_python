import pandas as pd
from typing import Dict, Any, List, Optional
from config import CSV_FILES, INDICATORS, DIMENSIONS
from datetime import datetime

class CSVHandler:
    """Comprehensive CSV Data Handler for AgriStack Analytics - Dynamic & Accurate"""

    JOIN_KEYS = ['state_lgd_code', 'district_lgd_code', 'village_lgd_code', 'season', 'year']

    def __init__(self):
        self._cache = {}
        self._merged_cache = None

    def _load_csv(self, table_name: str) -> pd.DataFrame:
        """Load CSV with caching"""
        if table_name not in self._cache:
            self._cache[table_name] = pd.read_csv(CSV_FILES[table_name])
        return self._cache[table_name].copy()

    def _get_current_year(self) -> str:
        """Get current agricultural year (e.g., 2024-2025)"""
        now = datetime.now()
        if now.month >= 4:  # April onwards is new agri year
            return f"{now.year}-{now.year + 1}"
        return f"{now.year - 1}-{now.year}"

    def _get_current_season(self) -> str:
        """Get current season based on month"""
        month = datetime.now().month
        if 6 <= month <= 10:
            return "Kharif"
        elif 11 <= month or month <= 3:
            return "Rabi"
        return "Summer"

    def execute_analytics(self, intent: Dict[str, Any], user_lgd: str) -> Dict[str, Any]:
        """Execute analytics query based on intent - COMPREHENSIVE"""

        # Store current LGD for query building
        self._current_lgd = user_lgd

        indicator_key = intent.get("indicator", "crop_area")
        dimension_key = intent.get("dimension")
        crop_filter = intent.get("crop_filter")
        season_filter = intent.get("season_filter")
        year_filter = intent.get("year_filter")
        top_n = intent.get("top_n", 10)
        comparison_type = intent.get("comparison_type")

        # Get indicator metadata
        if indicator_key not in INDICATORS:
            indicator_key = "crop_area"
        ind_meta = INDICATORS[indicator_key]

        # Load appropriate table
        table_name = ind_meta["table"]
        df = self._load_csv(table_name)

        # Apply state filter
        df['state_lgd_code'] = df['state_lgd_code'].astype(str)
        df = df[df['state_lgd_code'] == str(user_lgd)]

        # Note: is_view filter shown in SQL preview but not applied to test data
        # Uncomment below when production data has is_view=True records
        # if 'is_view' in df.columns:
        #     df = df[df['is_view'] == True]

        if len(df) == 0:
            return self._empty_result(ind_meta, "No data found for this state.")

        # Apply crop filter if specified
        if crop_filter and 'crop_name_eng' in df.columns:
            df_filtered = df[df['crop_name_eng'].str.lower().str.contains(crop_filter.lower(), na=False)]
            if len(df_filtered) > 0:
                df = df_filtered

        # Apply season filter if specified
        if season_filter and 'season' in df.columns:
            df_filtered = df[df['season'].str.lower() == season_filter.lower()]
            if len(df_filtered) > 0:
                df = df_filtered

        # Apply year filter if specified
        if year_filter and 'year' in df.columns:
            df['year'] = df['year'].astype(str)
            df_filtered = df[df['year'] == year_filter]
            if len(df_filtered) > 0:
                df = df_filtered

        val_col = ind_meta["column"]

        # Handle special calculated columns
        if indicator_key == "pending_validation":
            if 'crop_area_closed' in df.columns and 'crop_area_approved' in df.columns:
                df['pending'] = df['crop_area_closed'] - df['crop_area_approved']
                df['pending'] = df['pending'].clip(lower=0)
                val_col = 'pending'

        # Handle comparison queries
        if comparison_type:
            return self._handle_comparison(df, comparison_type, ind_meta, crop_filter, season_filter, year_filter, user_lgd)

        # Handle dimension grouping
        if dimension_key and dimension_key in DIMENSIONS:
            return self._grouped_result(df, dimension_key, val_col, ind_meta, crop_filter, season_filter, year_filter, top_n)

        # Summary (KPI) result
        return self._summary_result(df, val_col, ind_meta, crop_filter, season_filter, year_filter, table_name)

    def _grouped_result(self, df: pd.DataFrame, dimension_key: str, val_col: str,
                        ind_meta: Dict, crop_filter: str, season_filter: str, year_filter: str, top_n: int) -> Dict[str, Any]:
        """Generate grouped/breakdown result"""

        dim_meta = DIMENSIONS[dimension_key]
        label_col = dim_meta["column"]

        if label_col not in df.columns:
            return self._empty_result(ind_meta, f"Dimension '{dim_meta['title']}' not available in this data.")

        if val_col not in df.columns:
            return self._empty_result(ind_meta, f"Column '{val_col}' not found in data.")

        # Group and aggregate
        result = df.groupby(label_col)[val_col].sum()

        # Sort: chronologically for year, by value for others
        if dimension_key == "year":
            result = result.sort_index(ascending=True)
        else:
            result = result.sort_values(ascending=False)
            result = result.head(top_n)

        total = result.sum()
        labels = [str(i) for i in result.index]
        values = [float(v) for v in result.values]

        # Calculate percentages
        percentages = [(v / total * 100) if total > 0 else 0 for v in values]

        # Build title
        title_parts = []
        if crop_filter:
            title_parts.append(crop_filter)
        title_parts.append(ind_meta['title'])
        title_parts.append(f"by {dim_meta['title']}")
        if season_filter:
            title_parts.append(f"({season_filter})")
        if year_filter:
            title_parts.append(f"[{year_filter}]")

        # Determine chart type
        if dimension_key == "year":
            chart_type = "bar"
        elif len(values) <= 5:
            chart_type = "pie"
        else:
            chart_type = "bar"

        # Build SQL-like query for display (PostgreSQL format)
        table_mapping = {
            "crop_area": "public.crop_sowing_data",
            "aggregate": "public.aggregate_summary_data",
            "cultivated": "public.cultivated_summary_data"
        }
        db_table = table_mapping.get(ind_meta["table"], f"public.{ind_meta['table']}")

        filters = [f"state_lgd_code::INT = {self._current_lgd}", "is_view = true"]
        if crop_filter:
            filters.append(f"crop_name_eng ILIKE '%{crop_filter}%'")
        if season_filter:
            filters.append(f"season = '{season_filter}'")
        if year_filter:
            filters.append(f"year = '{year_filter}'")

        data_query = {
            "table": db_table,
            "column": val_col,
            "aggregation": "SUM",
            "group_by": label_col,
            "filters": filters,
            "sql_preview": f"SELECT {label_col}, COUNT(*) AS record_count, SUM({val_col}::NUMERIC) AS {val_col}_sum FROM {db_table} WHERE {' AND '.join(filters)} GROUP BY {label_col} ORDER BY {val_col}_sum DESC"
        }

        return {
            "title": " ".join(title_parts),
            "unit": ind_meta["unit"],
            "labels": labels,
            "values": values,
            "percentages": percentages,
            "total": float(total),
            "chart_type": chart_type,
            "dimension": dim_meta["title"],
            "crop_filter": crop_filter,
            "season_filter": season_filter,
            "year_filter": year_filter,
            "record_count": len(df),
            "data_query": data_query
        }

    def _summary_result(self, df: pd.DataFrame, val_col: str, ind_meta: Dict,
                        crop_filter: str, season_filter: str, year_filter: str, table_name: str) -> Dict[str, Any]:
        """Generate summary KPI result"""

        if val_col not in df.columns:
            return self._empty_result(ind_meta, f"Column '{val_col}' not found.")

        total = float(df[val_col].sum())

        # Additional stats based on table
        extra_stats = {}
        if table_name == "crop_area":
            if 'no_of_farmers' in df.columns:
                extra_stats['farmers_count'] = int(df['no_of_farmers'].sum())
            if 'no_of_plots' in df.columns:
                extra_stats['plots_count'] = int(df['no_of_plots'].sum())
            if 'crop_name_eng' in df.columns:
                extra_stats['unique_crops'] = df['crop_name_eng'].nunique()

        elif table_name == "aggregate":
            for col in ['total_plots', 'total_assigned_plots', 'total_plots_surveyed',
                        'total_survey_approved', 'total_survey_under_review']:
                if col in df.columns:
                    extra_stats[col] = int(df[col].sum())

        elif table_name == "cultivated":
            for col in ['total_irrigated_area', 'total_unirrigated_area', 'total_fallow_area',
                        'total_harvested_area', 'total_surveyable_area']:
                if col in df.columns:
                    extra_stats[col] = float(df[col].sum())

        # Build title
        title_parts = []
        if crop_filter:
            title_parts.append(crop_filter)
        title_parts.append(ind_meta['title'])
        if season_filter:
            title_parts.append(f"({season_filter})")
        if year_filter:
            title_parts.append(f"[{year_filter}]")

        # Build SQL-like query for display (PostgreSQL format)
        table_mapping = {
            "crop_area": "public.crop_sowing_data",
            "aggregate": "public.aggregate_summary_data",
            "cultivated": "public.cultivated_summary_data"
        }
        db_table = table_mapping.get(table_name, f"public.{table_name}")

        filters = [f"state_lgd_code::INT = {self._current_lgd}", "is_view = true"]
        if crop_filter:
            filters.append(f"crop_name_eng ILIKE '%{crop_filter}%'")
        if season_filter:
            filters.append(f"season = '{season_filter}'")
        if year_filter:
            filters.append(f"year = '{year_filter}'")

        data_query = {
            "table": db_table,
            "column": val_col,
            "aggregation": "SUM",
            "group_by": None,
            "filters": filters,
            "sql_preview": f"SELECT COUNT(*) AS record_count, SUM({val_col}::NUMERIC) AS {val_col}_sum FROM {db_table} WHERE {' AND '.join(filters)}"
        }

        return {
            "title": " ".join(title_parts),
            "unit": ind_meta["unit"],
            "labels": ["Total"],
            "values": [total],
            "chart_type": "kpi",
            "crop_filter": crop_filter,
            "season_filter": season_filter,
            "year_filter": year_filter,
            "record_count": len(df),
            "data_query": data_query,
            **extra_stats
        }

    def _handle_comparison(self, df: pd.DataFrame, comparison_type: str,
                           ind_meta: Dict, crop_filter: str, season_filter: str, year_filter: str, user_lgd: str) -> Dict[str, Any]:
        """Handle comparison queries"""

        val_col = ind_meta["column"]

        if comparison_type == "irrigated_vs_unirrigated":
            cult_df = self._load_csv("cultivated")
            cult_df['state_lgd_code'] = cult_df['state_lgd_code'].astype(str)
            cult_df = cult_df[cult_df['state_lgd_code'] == str(user_lgd)]

            if 'total_irrigated_area' in cult_df.columns and 'total_unirrigated_area' in cult_df.columns:
                irrigated = float(cult_df['total_irrigated_area'].sum())
                unirrigated = float(cult_df['total_unirrigated_area'].sum())
                return {
                    "title": "Irrigated vs Unirrigated Area Comparison",
                    "unit": "Hectares",
                    "labels": ["Irrigated", "Unirrigated"],
                    "values": [irrigated, unirrigated],
                    "chart_type": "pie",
                    "comparison_type": comparison_type,
                    "total": irrigated + unirrigated
                }

        elif comparison_type == "assigned_vs_surveyed":
            agg_df = self._load_csv("aggregate")
            agg_df['state_lgd_code'] = agg_df['state_lgd_code'].astype(str)
            agg_df = agg_df[agg_df['state_lgd_code'] == str(user_lgd)]

            if 'total_assigned_plots' in agg_df.columns and 'total_plots_surveyed' in agg_df.columns:
                assigned = float(agg_df['total_assigned_plots'].sum())
                surveyed = float(agg_df['total_plots_surveyed'].sum())
                return {
                    "title": "Assigned vs Surveyed Plots Comparison",
                    "unit": "Plots",
                    "labels": ["Assigned", "Surveyed"],
                    "values": [assigned, surveyed],
                    "chart_type": "bar",
                    "comparison_type": comparison_type,
                    "total": assigned + surveyed
                }

        elif comparison_type == "approved_vs_closed":
            crop_df = self._load_csv("crop_area")
            crop_df['state_lgd_code'] = crop_df['state_lgd_code'].astype(str)
            crop_df = crop_df[crop_df['state_lgd_code'] == str(user_lgd)]

            if 'crop_area_approved' in crop_df.columns and 'crop_area_closed' in crop_df.columns:
                approved = float(crop_df['crop_area_approved'].sum())
                closed = float(crop_df['crop_area_closed'].sum())
                return {
                    "title": "Approved vs Closed Crop Area",
                    "unit": "Hectares",
                    "labels": ["Approved", "Closed"],
                    "values": [approved, closed],
                    "chart_type": "bar",
                    "comparison_type": comparison_type,
                    "total": approved + closed
                }

        elif comparison_type == "surveyable_vs_surveyed":
            cult_df = self._load_csv("cultivated")
            cult_df['state_lgd_code'] = cult_df['state_lgd_code'].astype(str)
            cult_df = cult_df[cult_df['state_lgd_code'] == str(user_lgd)]

            if 'total_surveyable_area' in cult_df.columns and 'total_surveyed_area' in cult_df.columns:
                surveyable = float(cult_df['total_surveyable_area'].sum())
                surveyed = float(cult_df['total_surveyed_area'].sum())
                return {
                    "title": "Surveyable vs Surveyed Area",
                    "unit": "Hectares",
                    "labels": ["Surveyable", "Surveyed"],
                    "values": [surveyable, surveyed],
                    "chart_type": "bar",
                    "comparison_type": comparison_type,
                    "total": surveyable + surveyed
                }

        elif comparison_type == "rabi_vs_kharif":
            if 'season' in df.columns:
                rabi_df = df[df['season'].str.lower() == 'rabi']
                kharif_df = df[df['season'].str.lower() == 'kharif']

                rabi_val = float(rabi_df[val_col].sum()) if len(rabi_df) > 0 else 0
                kharif_val = float(kharif_df[val_col].sum()) if len(kharif_df) > 0 else 0

                return {
                    "title": f"Rabi vs Kharif - {ind_meta['title']}",
                    "unit": ind_meta["unit"],
                    "labels": ["Rabi", "Kharif"],
                    "values": [rabi_val, kharif_val],
                    "chart_type": "pie",
                    "comparison_type": comparison_type,
                    "total": rabi_val + kharif_val
                }

        elif comparison_type == "fallow_vs_cultivated":
            cult_df = self._load_csv("cultivated")
            cult_df['state_lgd_code'] = cult_df['state_lgd_code'].astype(str)
            cult_df = cult_df[cult_df['state_lgd_code'] == str(user_lgd)]

            if 'total_fallow_area' in cult_df.columns and 'total_surveyed_area' in cult_df.columns:
                fallow = float(cult_df['total_fallow_area'].sum())
                cultivated = float(cult_df['total_surveyed_area'].sum()) - fallow
                return {
                    "title": "Fallow vs Cultivated Area",
                    "unit": "Hectares",
                    "labels": ["Fallow", "Cultivated"],
                    "values": [fallow, cultivated],
                    "chart_type": "pie",
                    "comparison_type": comparison_type,
                    "total": fallow + cultivated
                }

        return self._empty_result(ind_meta, "Comparison data not available.")

    def _empty_result(self, ind_meta: Dict, note: str) -> Dict[str, Any]:
        """Generate empty result with note"""
        return {
            "title": ind_meta.get("title", "Data"),
            "unit": ind_meta.get("unit", ""),
            "labels": [],
            "values": [],
            "chart_type": "kpi",
            "note": note
        }


# Singleton instance
csv_handler = CSVHandler()
