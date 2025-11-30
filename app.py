import streamlit as st
# Force redeploy
import pandas as pd
import plotly.graph_objects as go

# Page Config
st.set_page_config(layout="wide", page_title="Drain Oil Analysis Dashboard")

# Data Definitions
# Table 2: Fe Limits
# Structure: {Fuel_Type: {Normal_Max: val, Raised_Max: val, Alert_Min: val}}
# Abnormal range is (Raised_Max, Alert_Min]
FE_LIMITS = {
    "ULSFO": {"Normal_Max": 25, "Raised_Max": 40, "Alert_Min": 300},
    "VLSFO": {"Normal_Max": 40, "Raised_Max": 80, "Alert_Min": 300},
    "HSFO": {"Normal_Max": 100, "Raised_Max": 200, "Alert_Min": 800}
}

# Table 4: BN Limits
# Structure: {BN_Target: {Fuel_Type: {Normal_Min: val, Low_Min: val, Alert_Max: val}}}
BN_LIMITS = {
    "BN 40": {
        "ULSFO": {"Normal_Min": 24, "Low_Min": 16, "Alert_Max": 15},
        "VLSFO": {"Normal_Min": 20, "Low_Min": 16, "Alert_Max": 15},
        # HSFO missing in table for BN 40
    },
    "BN 70": {
        "ULSFO": {"Normal_Min": 42, "Low_Min": 28, "Alert_Max": 27},
        "VLSFO": {"Normal_Min": 35, "Low_Min": 28, "Alert_Max": 27},
        "HSFO": {"Normal_Min": 21, "Low_Min": 14, "Alert_Max": 13},
    },
    "BN 100": {
        "ULSFO": {"Normal_Min": 60, "Low_Min": 40, "Alert_Max": 39},
        "VLSFO": {"Normal_Min": 50, "Low_Min": 40, "Alert_Max": 39},
        "HSFO": {"Normal_Min": 30, "Low_Min": 20, "Alert_Max": 19},
    },
    "BN 140": {
        "ULSFO": {"Normal_Min": 84, "Low_Min": 56, "Alert_Max": 55},
        "VLSFO": {"Normal_Min": 70, "Low_Min": 56, "Alert_Max": 55},
        "HSFO": {"Normal_Min": 42, "Low_Min": 28, "Alert_Max": 27},
    }
}

# Sidebar Filters
with st.sidebar:
    with st.expander("Filters", expanded=True):
        # BN Target
        bn_options = ["All"] + list(BN_LIMITS.keys())
        selected_bn = st.selectbox("BN_Target", bn_options)

        # Category (Fuel Type)
        if selected_bn == "All":
            fuel_options = ["All"] + list(FE_LIMITS.keys())
        else:
            # Filter Fuel options based on available data for selected BN
            valid_fuels = list(BN_LIMITS[selected_bn].keys())
            fuel_options = ["All"] + valid_fuels
        
        selected_fuel = st.selectbox("Category (Fuel Type)", fuel_options)

# Main Content
st.title("Drain Oil Analysis Control Limits")

if selected_fuel == "All" or selected_bn == "All":
    st.info("Please select a specific Category and BN Target to view the Control Limit Chart.")
    
    # Show Data Tables instead
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Iron (Fe) Limits [mg/kg]")
        df_fe = pd.DataFrame.from_dict(FE_LIMITS, orient='index')
        df_fe = df_fe[['Normal_Max', 'Raised_Max', 'Alert_Min']]
        df_fe.columns = ['Normal (<=)', 'Raised (<=)', 'Alert (>)']
        st.dataframe(df_fe)
        
    with col2:
        st.subheader("Residual BN Limits")
        # Flatten BN data for display
        bn_data = []
        for bn_key, fuels in BN_LIMITS.items():
            for fuel_key, limits in fuels.items():
                row = limits.copy()
                row['BN_Target'] = bn_key
                row['Fuel_Type'] = fuel_key
                bn_data.append(row)
        df_bn = pd.DataFrame(bn_data)
        if not df_bn.empty:
            df_bn = df_bn[['BN_Target', 'Fuel_Type', 'Normal_Min', 'Low_Min', 'Alert_Max']]
            df_bn.columns = ['BN Target', 'Fuel Type', 'Normal Min', 'Low Min', 'Alert Max']
            st.dataframe(df_bn)

else:
    # Get Limits
    fe_lim = FE_LIMITS[selected_fuel]
    bn_lim = BN_LIMITS[selected_bn][selected_fuel]
    
    # Extract numeric BN target
    bn_val = int(selected_bn.split()[1])

    # Chart Parameters
    max_x = bn_val + 10 # BN axis
    max_y = fe_lim['Alert_Min'] + 50 # Fe axis
    
    # Create Plot
    fig = go.Figure()

    # 1. Alert Zone (Red) - Background
    # We can just set the plot background or draw a large rect
    fig.add_shape(type="rect",
        x0=0, y0=0, x1=max_x, y1=max_y,
        fillcolor="red", opacity=1, layer="below", line_width=0,
        name="Alert"
    )
    
    # 2. Abnormal Zone (Orange) - Fe
    # Covers area where Fe is NOT Alert, but is Abnormal.
    # Abnormal Fe is > Raised_Max and <= Alert_Min.
    # BN must be > Alert_Max (otherwise it's Red).
    # Rect: X [Alert_Max, max_x], Y [0, Alert_Min]
    fig.add_shape(type="rect",
        x0=bn_lim['Alert_Max'], y0=0, 
        x1=max_x, y1=fe_lim['Alert_Min'],
        fillcolor="orange", opacity=1, layer="below", line_width=0,
        name="Abnormal"
    )

    # 3. Raised/Low Zone (Yellow)
    # Covers area where Fe is Normal/Raised AND BN is Normal/Low.
    # Fe <= Raised_Max.
    # BN >= Low_Min.
    # Rect: X [Low_Min, max_x], Y [0, fe_lim['Raised_Max']]
    fig.add_shape(type="rect",
        x0=bn_lim['Low_Min'], y0=0, 
        x1=max_x, y1=fe_lim['Raised_Max'],
        fillcolor="yellow", opacity=1, layer="below", line_width=0,
        name="Raised/Low"
    )

    # 4. Normal Zone (Green)
    # Fe <= Normal_Max
    # BN >= Normal_Min
    # Rect: X [Normal_Min, max_x], Y [0, fe_lim['Normal_Max']]
    fig.add_shape(type="rect",
        x0=bn_lim['Normal_Min'], y0=0, 
        x1=max_x, y1=fe_lim['Normal_Max'],
        fillcolor="green", opacity=1, layer="below", line_width=0,
        name="Normal"
    )

    # Add dummy traces for Legend
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', marker=dict(color='green', size=10, symbol='square'), name='Normal'))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', marker=dict(color='yellow', size=10, symbol='square'), name='Raised/Low'))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', marker=dict(color='orange', size=10, symbol='square'), name='Abnormal'))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', marker=dict(color='red', size=10, symbol='square'), name='Alert'))

    # Layout Updates
    fig.update_layout(
        title=f"Residual BN and Iron Control Limit - {selected_bn} ({selected_fuel})",
        xaxis_title="Residual BN",
        yaxis_title="Iron (Fe) [mg/kg]",
        xaxis=dict(range=[0, max_x]),
        yaxis=dict(range=[0, max_y]),
        width=1000,
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.markdown("Source : Everllence Service Letter, SL2025-776/NHN")
st.markdown("Prepared by *Mark CHUANG*")
st.caption("v1.1")
