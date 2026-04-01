import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.set_page_config(page_title="BBH KPI Tool", layout="wide")

st.title("📊 BBH KPI Automation Tool")

st.markdown("Upload all 6 input files to generate final KPI report")

# ==========================
# FILE UPLOAD
# ==========================

col1, col2, col3 = st.columns(3)

with col1:
    cs1 = st.file_uploader("Upload CS1.xlsx")
    ps1 = st.file_uploader("Upload PS1.xlsx")

with col2:
    cs2 = st.file_uploader("Upload CS2.xlsx")
    ps2 = st.file_uploader("Upload PS2.xlsx")

with col3:
    mapa1 = st.file_uploader("Upload MAPA1.xlsx")
    mapa2 = st.file_uploader("Upload MAPA2.xlsx")

# ==========================
# PROCESS BUTTON
# ==========================

if st.button("🚀 Generate Report"):

    if None in [cs1, cs2, ps1, ps2, mapa1, mapa2]:
        st.error("Please upload all 6 files")

    else:
        try:
            # READ FILES
            df1 = pd.read_excel(cs1)
            df2 = pd.read_excel(cs2)
            df3 = pd.read_excel(ps1)
            df4 = pd.read_excel(ps2)
            df5 = pd.read_excel(mapa1)
            df6 = pd.read_excel(mapa2)

            all_dfs = [df1, df2, df3, df4, df5, df6]

            # CLEAN
            for df in all_dfs:
                df.drop(index=1, errors='ignore', inplace=True)
                df.reset_index(drop=True, inplace=True)
                df.columns = df.columns.str.strip()

            # COLUMN STANDARDIZATION
            mapping = {
                'mapatrafficraju': 'Total CS traffic - Erl',
                'mapacsdropnum': 'Voice DCR Num',
                'mapacsdropnum_new':'Voice DCR Num',
                'mapacsdcrdenom_new':'Voice DCR Denom',
                'mapacsdcrdenom': 'Voice DCR Denom',
                'CS RRC Setup Success Rate Nom': 'CS RRC Setup Success Rate _NUM',
                'CS RRC Setup Success Rate Dnom': 'CS RRC Setup Success Rate _DENUM',
                'PS RRC Setup Success Rate Nom': 'PS RRC Setup Success Rate _NUM',
                'PS RRC Setup Success Rate Dnom': 'PS RRC Setup Success Rate _DENUM',
                'cs_rab_sr_nom': 'CS_RAB_SR_Nom',
                'cs_rab_sr_denom': 'CS_RAB_SR_denom',
                'ps_rab_sr_nom': 'PS_RAB_SR_Nom',
                'ps_rab_sr_denom': 'PS_RAB_SR_denom',
                'soft_ho_success_num': 'Soft HO Success Num',
                'soft_ho_success_denom': 'Soft HO Success Denom',
                'cs_intersys_hho_success_num': 'CS Inter Sys HHO Success Num',
                'cs_intersys_hho_success_denom': 'CS Inter Sys HHO Success Denom',
                'w17_hs_ps_dcr_num': 'W17 HS PS Drop Call Rate_NUM',
                'w17_hs_ps_dcr_denum': 'W17 HS PS Drop Call Rate_DENUM'
            }

            for df in all_dfs:
                df.rename(columns=mapping, inplace=True)

            # COMBINE
            cs_df = pd.concat([df1, df2], ignore_index=True, sort=False)
            ps_df = pd.concat([df3, df4], ignore_index=True, sort=False)
            daily_df = pd.concat([df5, df6], ignore_index=True, sort=False)

            # SAFE SELECT
            def safe_select(df, cols):
                for col in cols:
                    if col not in df.columns:
                        df[col] = np.nan
                return df[cols]

            cs_cols = ['Period start time','WBTS name','WBTS ID','WCEL name','WCEL ID',
                       'CS_RAB_SR_Nom','CS_RAB_SR_denom','Voice DCR Num','Voice DCR Denom',
                       'Soft HO Success Num','Soft HO Success Denom',
                       'CS RRC Setup Success Rate _NUM','CS RRC Setup Success Rate _DENUM',
                       'CS Inter Sys HHO Success Num','CS Inter Sys HHO Success Denom','Average RTWP']

            ps_cols = ['Period start time','WBTS name','WBTS ID','WCEL name','WCEL ID',
                       'Average number of simultaneous HSDPA users','PS_RAB_SR_Nom','PS_RAB_SR_denom',
                       'W17 HS PS Drop Call Rate_NUM','W17 HS PS Drop Call Rate_DENUM',
                       'PS RRC Setup Success Rate _NUM','PS RRC Setup Success Rate _DENUM',
                       'Act HS-DSCH end usr thp']

            daily_cols = ['Period start time','WBTS name','WBTS ID','WCEL name','WCEL ID',
                          'PSTraffic_Airtel_ASCA','CellAvailability_Airtel_ASCA','CS_Traffic24H_Airtel_ASCA']

            cs_df = safe_select(cs_df, cs_cols)
            ps_df = safe_select(ps_df, ps_cols)
            daily_df = safe_select(daily_df, daily_cols)

            # DATE
            for df in [cs_df, ps_df, daily_df]:
                df['Period start time'] = pd.to_datetime(df['Period start time'], errors='coerce').dt.date

            # MERGE
            temp = pd.merge(cs_df, ps_df, on=['Period start time','WBTS name','WBTS ID','WCEL name','WCEL ID'], how='outer')
            formula_df = pd.merge(temp, daily_df, on=['Period start time','WBTS name','WBTS ID','WCEL name','WCEL ID'], how='outer')

            # NUMERIC CLEAN
            for col in formula_df.columns:
                if col not in ['Period start time','WBTS name','WBTS ID','WCEL name','WCEL ID']:
                    formula_df[col] = pd.to_numeric(formula_df[col], errors='coerce')

            # KPI FUNCTION
            def kpi(num, den):
                return (formula_df[num] / formula_df[den].replace(0, np.nan)) * 100

            # SAFE KPI FUNCTION

            def safe_kpi(df, num, den):

                if num in df.columns and den in df.columns:
            
                    n = pd.to_numeric(df[num], errors='coerce')
                    d = pd.to_numeric(df[den], errors='coerce')
            
                    result = (n / d.replace(0, np.nan)) * 100
            
                    # ✅ CASE 1: BOTH BLANK → BLANK
                    result[(n.isna()) & (d.isna())] = np.nan
            
                    # ✅ CASE 2: BOTH ZERO → "NA"
                    result[(n == 0) & (d == 0)] = "NA"
            
                    return result
            
                return np.nan

            # KPIs
            formula_df['VOICE DROP RATE %'] = safe_kpi(formula_df, 'Voice DCR Num', 'Voice DCR Denom')
            formula_df['CS RRC SR %'] = safe_kpi(formula_df, 'CS RRC Setup Success Rate _NUM', 'CS RRC Setup Success Rate _DENUM')
            formula_df['CS RAB SR %'] = safe_kpi(formula_df, 'CS_RAB_SR_Nom', 'CS_RAB_SR_denom')
            formula_df['SHO SR %'] = safe_kpi(formula_df, 'Soft HO Success Num', 'Soft HO Success Denom')
            formula_df['HS DROP RATE %'] = safe_kpi(formula_df, 'W17 HS PS Drop Call Rate_NUM', 'W17 HS PS Drop Call Rate_DENUM')
            formula_df['PS RAB SR %'] = safe_kpi(formula_df, 'PS_RAB_SR_Nom', 'PS_RAB_SR_denom')
            formula_df['PS RRC SR %'] = safe_kpi(formula_df, 'PS RRC Setup Success Rate _NUM', 'PS RRC Setup Success Rate _DENUM')
            formula_df['CS IRAT SR %'] = safe_kpi(formula_df, 'CS Inter Sys HHO Success Num', 'CS Inter Sys HHO Success Denom')
            

            # Direct KPIs
     
            formula_df['HSDPA USERS'] = formula_df.get('Average number of simultaneous HSDPA users')
            formula_df['Act HS-DSCH end usr thp_Kbps'] = formula_df.get('Act HS-DSCH end usr thp')
            formula_df['Average RTWP'] = formula_df.get('Average RTWP', np.nan)

            # Daily KPIs
            formula_df['DATA TRAFFIC_GB(Daily)'] = pd.to_numeric(formula_df.get('PSTraffic_Airtel_ASCA'), errors='coerce') / 1024
            formula_df['24 Hours_RNA %'] = formula_df.get('CellAvailability_Airtel_ASCA', np.nan)
            formula_df['Total CS traffic - Erl(Daily)'] = formula_df.get('CS_Traffic24H_Airtel_ASCA', np.nan)

            # FINAL
            selected_cols = ['Period start time','WBTS name','WBTS ID','WCEL name','WCEL ID',
                             'VOICE DROP RATE %','CS RRC SR %','CS RAB SR %',
                             'PS RRC SR %','PS RAB SR %','CS IRAT SR %',
                             'SHO SR %','HS DROP RATE %','Act HS-DSCH end usr thp_Kbps','DATA TRAFFIC_GB(Daily)','24 Hours_RNA %',
                             'Total CS traffic - Erl(Daily)','HSDPA USERS','Average RTWP']


            for col in selected_cols:
                if col not in formula_df.columns:
                    formula_df[col] = np.nan

            df = formula_df[selected_cols]

            all_dates = df['Period start time'].drop_duplicates()

            # PIVOT
            df_melted = pd.melt(df, id_vars=['Period start time','WBTS name','WBTS ID','WCEL name','WCEL ID'],
                                var_name='Kpis', value_name='value')



            # ======================================
            # FORCE ALL KPI COMBINATIONS (CORRECT)
            # ======================================
            
            all_kpis = ['VOICE DROP RATE %','CS RRC SR %','CS RAB SR %',
                        'PS RRC SR %','PS RAB SR %','CS IRAT SR %',
                        'HSDPA USERS','SHO SR %','HS DROP RATE %',
                        'Act HS-DSCH end usr thp_Kbps',
                        'DATA TRAFFIC_GB(Daily)','24 Hours_RNA %',
                        'Total CS traffic - Erl(Daily)','Average RTWP']
            
            # Unique cells (correct combinations)
            all_cells = pd.concat([
                cs_df[['WBTS name','WBTS ID','WCEL name','WCEL ID']],
                ps_df[['WBTS name','WBTS ID','WCEL name','WCEL ID']],
                daily_df[['WBTS name','WBTS ID','WCEL name','WCEL ID']]
            ]).drop_duplicates().reset_index(drop=True)
            
            # Create correct full structure
            all_cells['key'] = 1
            all_dates = all_dates.to_frame(name='Period start time')
            all_dates['key'] = 1
            
            kpi_df = pd.DataFrame({'Kpis': all_kpis, 'key': 1})
            
            full_df = all_cells.merge(all_dates, on='key') \
                               .merge(kpi_df, on='key') \
                               .drop('key', axis=1)
            
            # Merge with actual data
            df_melted = pd.merge(
                full_df,
                df_melted,
                on=['WBTS name','WBTS ID','WCEL name','WCEL ID','Period start time','Kpis'],
                how='left'
            )
                        
            
            df_pivot = df_melted.pivot_table(
                index=['WBTS name','WBTS ID','WCEL name','WCEL ID','Kpis'],
                columns='Period start time',
                values='value',
                aggfunc='first'
                dropna=False
            ).reset_index()
            df_pivot = df_pivot.fillna("")

            # DOWNLOAD
            output = BytesIO()
            df_pivot.to_excel(output, index=False)

            st.success("✅ Report Generated Successfully")
            st.download_button("📥 Download Report", data=output.getvalue(), file_name="BBH_Output.xlsx")

        except Exception as e:
            st.error(f"Error: {str(e)}")
