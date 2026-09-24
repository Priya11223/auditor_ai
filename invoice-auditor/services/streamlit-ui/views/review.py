"""
Streamlit UI - Review View

Displays the invoice alongside extracted data and allows the human
to submit corrections.
"""

import streamlit as st

from utils.api_client import get_invoice_details, submit_feedback


def render_review():
    st.button("← Back to Inbox", on_click=lambda: st.session_state.update({"current_page": "Inbox"}))
    
    invoice_id = st.session_state.get("selected_invoice_id")
    if not invoice_id:
        st.error("No invoice selected.")
        return

    try:
        with st.spinner("Loading invoice details..."):
            details = get_invoice_details(invoice_id)
    except Exception:
        st.error("Failed to load invoice details.")
        return

    st.title(f"Review Invoice: {details.get('extracted_raw', {}).get('invoice_number', 'Unknown')}")
    st.markdown(f"**Current Recommendation:** `{details['recommendation'].upper()}`")
    
    # --- Discrepancies Summary ---
    discrepancies = details.get("discrepancies", [])
    if discrepancies:
        st.warning(f"Found {len(discrepancies)} discrepancy(ies) requiring attention.")
        for d in discrepancies:
            icon = "🔴" if d['severity'] == 'critical' else "🟡"
            st.markdown(f"{icon} **{d['field']}** - Severity: {d['severity']}")

    # --- Side-by-Side Layout ---
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Original Document")
        # In a real system, we'd fetch the file bytes from an S3 bucket or internal endpoint
        # For this PoC, we just show the file path
        st.info(f"File Path: `{details['file_path']}`")
        st.text("Imagine a beautiful PDF viewer rendering the invoice here.")

    with col2:
        st.subheader("Extracted Data & Corrections")
        
        extracted = details.get("extracted_raw", {})
        
        # Build the form
        with st.form("correction_form"):
            st.markdown("Override any incorrect values below:")
            
            # Helper to check if a field has a discrepancy
            def has_discrepancy(field_name: str) -> bool:
                return any(d['field'] == field_name for d in discrepancies)
                
            # Render fields. Highlight them if they have a discrepancy.
            fields_to_review = ["invoice_number", "vendor_name", "po_number", "total_amount"]
            
            input_values = {}
            for field in fields_to_review:
                current_val = str(extracted.get(field, ""))
                
                label = f"{field} {'⚠️' if has_discrepancy(field) else ''}"
                
                # We use text_input for everything to allow raw string corrections
                # (Revalidation service parses it later)
                input_values[field] = st.text_input(label, value=current_val)
                
            st.markdown("---")
            auditor_email = st.text_input("Your Email (Auditor ID)", value="auditor@company.com")
            
            submitted = st.form_submit_button("Submit Corrections & Revalidate", type="primary")
            
            if submitted:
                # Find what changed
                corrections = []
                for field in fields_to_review:
                    old_val = str(extracted.get(field, ""))
                    new_val = input_values[field]
                    if old_val != new_val:
                        corrections.append({
                            "field_name": field,
                            "corrected_value": new_val
                        })
                
                if not corrections:
                    st.warning("No changes detected. Nothing to submit.")
                else:
                    payload = {
                        "corrected_by": auditor_email,
                        "corrections": corrections
                    }
                    
                    try:
                        with st.spinner("Submitting feedback and revalidating..."):
                            result = submit_feedback(invoice_id, payload)
                        
                        st.success(f"Successfully revalidated! New Status: {result['recommendation'].upper()}")
                        st.session_state.current_page = "Inbox"
                        # Use experimental_rerun or let the user click back
                        
                    except Exception as e:
                        st.error(f"Submission failed: {e}")
