"""
Streamlit UI - Inbox View

Displays a data table of invoices that require human intervention.
"""

import pandas as pd
import streamlit as st

from utils.api_client import get_pending_invoices


def render_inbox():
    st.title("📥 Auditor Inbox")
    st.markdown("Invoices flagged by the AI Agent requiring human review.")

    try:
        with st.spinner("Fetching pending invoices..."):
            invoices = get_pending_invoices()
    except Exception:
        st.error(
            "Failed to connect to the Agent Service. "
            "Please ensure the backend is running."
        )
        return

    if not invoices:
        st.success("🎉 All caught up! No invoices require review.")
        return

    # Convert to Pandas DataFrame for nice Streamlit rendering
    df = pd.DataFrame(invoices)
    
    # Format the display
    display_df = df[[
        "invoice_number", 
        "vendor_name", 
        "total_amount", 
        "recommendation", 
        "created_at"
    ]].copy()
    
    display_df["created_at"] = pd.to_datetime(display_df["created_at"]).dt.strftime('%Y-%m-%d %H:%M')
    
    # Capitalize recommendation
    display_df["recommendation"] = display_df["recommendation"].str.upper()

    st.dataframe(
        display_df,
        column_config={
            "invoice_number": "Invoice #",
            "vendor_name": "Vendor",
            "total_amount": st.column_config.NumberColumn(
                "Total Amount",
                format="$%.2f"
            ),
            "recommendation": "Status",
            "created_at": "Processed At",
        },
        use_container_width=True,
        hide_index=True,
    )
    
    st.markdown("---")
    st.subheader("Action Required")
    
    # Simple selection mechanism
    selected_id = st.selectbox(
        "Select an Invoice to Review",
        options=df["invoice_id"].tolist(),
        format_func=lambda x: f"{df[df['invoice_id'] == x]['invoice_number'].values[0]} - {df[df['invoice_id'] == x]['vendor_name'].values[0]}"
    )
    
    if st.button("Review Invoice", type="primary"):
        st.session_state.selected_invoice_id = selected_id
        st.session_state.current_page = "Review"
        st.rerun()
