import pandas as pd
from typing import Dict, Any, List, Optional
from config import CSV_FILES, INDICATORS, DIMENSIONS

class CSVHandler:
    """Comprehensive CSV Data Handler for AgriStack Analytics"""

    # Common join keys across tables
    JOIN_KEYS = ['state_lgd_code', 'district_lgd_code', 'village_lgd_code', 'season', 'year']

    def __init__(self):
        self._cache = {}
        self._merged_cache = None

    def _load_csv(self, table_name: str) -> pd.DataFrame:
        """Load CSV with caching"""
        if table_name not in self._cache:
            self._cache[table_name] = pd.read_csv(CSV_FILES[table_name])
        return self._cache[table_name].copy()

    def _load_merged_data(self) -> pd.DataFrame:
        """Load and merge all three tables using common keys"""
        if self._merged_cache is not None:
            return self._merged_cache.copy()

        # Load all tables
        crop_df = self._load_csv("crop_area")
        agg_df = self._load_csv("aggregate")
        cult_df = self._load_csv("cultivated")

        # Standardize column types for join
        for df in [crop_df, agg_df, cult_df]:
            for col in self.JOIN_KEYS:
                if col in df.columns:
                    df[col] = df[col].astype(str)

        # Merge crop_area with aggregate
        merged = pd.merge(
            crop_df, agg_df,
            on=self.JOIN_KEYS,
            how='outer',
            suffixes=('', '_agg')
        )

        # Merge with cultivated
        merged = pd.merge(
            merged, cult_df,
            on=self.JOIN_KEYS,
            how='outer',
            suffixes=('', '_cult')
        )

        self._merged_cache = merged
        return merged.copy()

    def _needs_merged_data(self, intent: Dict[str, Any]) -> bool:
        """Check if query needs data from multiple tables"""
        indicator = intent.get("indicator", "")
        comparison = intent.get("comparison_type", "")

        # Cross-table comparisons need merged data
        cross_table_comparisons = [
            "crop_vs_survey",
            "area_vs_plots"
        ]

        if comparison in cross_table_comparisons:
            return True

        return False

    def execute_analytics(self, intent: Dict[str, Any], user_lgd: str) -> Dict[str, Any]:
        """Execute analytics query based on intent"""

        # Handle overview/dashboard queries
        if intent.get("indicator") == "overview":
            return self._overview_result(user_lgd)

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

        # Handle comparison queries
        if comparison_type:
            return self._handle_comparison(df, comparison_type, ind_meta, crop_filter, season_filter, user_lgd)

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

        # Group and aggregate
        result = df.groupby(label_col)[val_col].sum()

        # Sort: chronologically for year, by value for others
        if dimension_key == "year":
            result = result.sort_index(ascending=True)  # Chronological order
        else:
            result = result.sort_values(ascending=False)
            result = result.head(top_n)  # Limit only non-year dimensions

        total = result.sum()
        labels = [str(i) for i in result.index]
        values = [float(v) for v in result.values]

        # Calculate percentages for insights
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

        # Determine chart type (year-wise always bar)
        if dimension_key == "year":
            chart_type = "bar"
        else:
            chart_type = "pie" if len(values) <= 6 else "bar"

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
            "record_count": len(df)
        }

    def _summary_result(self, df: pd.DataFrame, val_col: str, ind_meta: Dict,
                        crop_filter: str, season_filter: str, year_filter: str, table_name: str) -> Dict[str, Any]:
        """Generate summary KPI result"""

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
            **extra_stats
        }

    def _handle_comparison(self, df: pd.DataFrame, comparison_type: str,
                           ind_meta: Dict, crop_filter: str, season_filter: str, user_lgd: str) -> Dict[str, Any]:
        """Handle comparison queries (e.g., irrigated vs unirrigated)"""

        val_col = ind_meta["column"]

        if comparison_type == "irrigated_vs_unirrigated":
            if 'total_irrigated_area' in df.columns and 'total_unirrigated_area' in df.columns:
                irrigated = float(df['total_irrigated_area'].sum())
                unirrigated = float(df['total_unirrigated_area'].sum())
                return {
                    "title": "Irrigated vs Unirrigated Area Comparison",
                    "unit": "Hectares",
                    "labels": ["Irrigated", "Unirrigated"],
                    "values": [irrigated, unirrigated],
                    "chart_type": "pie",
                    "comparison_type": comparison_type
                }

        elif comparison_type == "assigned_vs_surveyed":
            if 'total_assigned_plots' in df.columns and 'total_plots_surveyed' in df.columns:
                assigned = float(df['total_assigned_plots'].sum())
                surveyed = float(df['total_plots_surveyed'].sum())
                return {
                    "title": "Assigned vs Surveyed Plots Comparison",
                    "unit": "Plots",
                    "labels": ["Assigned", "Surveyed"],
                    "values": [assigned, surveyed],
                    "chart_type": "bar",
                    "comparison_type": comparison_type
                }

        elif comparison_type == "approved_vs_closed":
            if 'crop_area_approved' in df.columns and 'crop_area_closed' in df.columns:
                approved = float(df['crop_area_approved'].sum())
                closed = float(df['crop_area_closed'].sum())
                return {
                    "title": "Approved vs Closed Crop Area",
                    "unit": "Hectares",
                    "labels": ["Approved", "Closed"],
                    "values": [approved, closed],
                    "chart_type": "bar",
                    "comparison_type": comparison_type
                }

        elif comparison_type == "surveyable_vs_surveyed":
            if 'total_surveyable_area' in df.columns and 'total_surveyed_area' in df.columns:
                surveyable = float(df['total_surveyable_area'].sum())
                surveyed = float(df['total_surveyed_area'].sum())
                return {
                    "title": "Surveyable vs Surveyed Area",
                    "unit": "Hectares",
                    "labels": ["Surveyable", "Surveyed"],
                    "values": [surveyable, surveyed],
                    "chart_type": "bar",
                    "comparison_type": comparison_type
                }

        elif comparison_type == "rabi_vs_kharif":
            # Season comparison - needs merged or single table with season column
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
                    "comparison_type": comparison_type
                }

        elif comparison_type == "fallow_vs_cultivated":
            if 'total_fallow_area' in df.columns and 'total_surveyed_area' in df.columns:
                fallow = float(df['total_fallow_area'].sum())
                cultivated = float(df['total_surveyed_area'].sum()) - fallow
                return {
                    "title": "Fallow vs Cultivated Area",
                    "unit": "Hectares",
                    "labels": ["Fallow", "Cultivated"],
                    "values": [fallow, cultivated],
                    "chart_type": "pie",
                    "comparison_type": comparison_type
                }

        elif comparison_type == "crop_vs_survey":
            # Cross-table: crop area vs survey progress
            merged_df = self._load_merged_data()
            merged_df['state_lgd_code'] = merged_df['state_lgd_code'].astype(str)
            merged_df = merged_df[merged_df['state_lgd_code'] == str(user_lgd)]

            crop_area = float(merged_df['crop_area_approved'].sum()) if 'crop_area_approved' in merged_df.columns else 0
            surveyed_plots = float(merged_df['total_plots_surveyed'].sum()) if 'total_plots_surveyed' in merged_df.columns else 0

            return {
                "title": "Crop Area vs Survey Progress",
                "unit": "Mixed",
                "labels": ["Crop Area (Ha)", "Plots Surveyed"],
                "values": [crop_area, surveyed_plots],
                "chart_type": "bar",
                "comparison_type": comparison_type
            }

        # Default fallback
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

    def _overview_result(self, user_lgd: str) -> Dict[str, Any]:
        """Generate overview/dashboard result from all tables"""
        stats = self.get_combined_stats(user_lgd)

        # Create key metrics for display
        labels = []
        values = []

        if 'total_crop_area' in stats:
            labels.append("Crop Area (Ha)")
            values.append(stats['total_crop_area'])
        if 'total_farmers' in stats:
            labels.append("Farmers")
            values.append(stats['total_farmers'])
        if 'plots_surveyed' in stats:
            labels.append("Plots Surveyed")
            values.append(stats['plots_surveyed'])
        if 'total_surveyed_area' in stats:
            labels.append("Surveyed Area (Ha)")
            values.append(stats['total_surveyed_area'])
        if 'irrigated_area' in stats:
            labels.append("Irrigated (Ha)")
            values.append(stats['irrigated_area'])

        return {
            "title": "AgriStack Overview Dashboard",
            "unit": "Mixed",
            "labels": labels,
            "values": values,
            "chart_type": "bar",
            "record_count": len(labels),
            **stats  # Include all stats for narration
        }

    def get_combined_stats(self, user_lgd: str) -> Dict[str, Any]:
        """Get combined statistics from all three tables"""
        stats = {}

        # Crop Area stats
        crop_df = self._load_csv("crop_area")
        crop_df['state_lgd_code'] = crop_df['state_lgd_code'].astype(str)
        crop_df = crop_df[crop_df['state_lgd_code'] == str(user_lgd)]

        if 'crop_area_approved' in crop_df.columns:
            stats['total_crop_area'] = float(crop_df['crop_area_approved'].sum())
        if 'no_of_farmers' in crop_df.columns:
            stats['total_farmers'] = int(crop_df['no_of_farmers'].sum())
        if 'no_of_plots' in crop_df.columns:
            stats['total_crop_plots'] = int(crop_df['no_of_plots'].sum())
        if 'crop_name_eng' in crop_df.columns:
            stats['unique_crops'] = crop_df['crop_name_eng'].nunique()

        # Aggregate stats
        agg_df = self._load_csv("aggregate")
        agg_df['state_lgd_code'] = agg_df['state_lgd_code'].astype(str)
        agg_df = agg_df[agg_df['state_lgd_code'] == str(user_lgd)]

        if 'total_plots' in agg_df.columns:
            stats['total_plots'] = int(agg_df['total_plots'].sum())
        if 'total_plots_surveyed' in agg_df.columns:
            stats['plots_surveyed'] = int(agg_df['total_plots_surveyed'].sum())
        if 'total_survey_approved' in agg_df.columns:
            stats['surveys_approved'] = int(agg_df['total_survey_approved'].sum())
        if 'total_no_of_surveyors' in agg_df.columns:
            stats['total_surveyors'] = int(agg_df['total_no_of_surveyors'].sum())

        # Cultivated stats
        cult_df = self._load_csv("cultivated")
        cult_df['state_lgd_code'] = cult_df['state_lgd_code'].astype(str)
        cult_df = cult_df[cult_df['state_lgd_code'] == str(user_lgd)]

        if 'total_surveyed_area' in cult_df.columns:
            stats['total_surveyed_area'] = float(cult_df['total_surveyed_area'].sum())
        if 'total_irrigated_area' in cult_df.columns:
            stats['irrigated_area'] = float(cult_df['total_irrigated_area'].sum())
        if 'total_unirrigated_area' in cult_df.columns:
            stats['unirrigated_area'] = float(cult_df['total_unirrigated_area'].sum())
        if 'total_fallow_area' in cult_df.columns:
            stats['fallow_area'] = float(cult_df['total_fallow_area'].sum())

        return stats


# Singleton instance
csv_handler = CSVHandler()
