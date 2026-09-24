"""
Streamlit UI - Main Entry Point

Phase 1: Minimal dashboard showing infrastructure health status.
Verifies connectivity to Agent Service.
"""

import os

import httpx
import streamlit as st

AGENT_SERVICE_URL = os.getenv(
    "AGENT_SERVICE_URL", "http://agent-service:8000"
)

st.set_page_config(
    page_title="Invoice Audit Platform",
    page_icon="📋",
    layout="wide",
)

st.title("📋 Invoice Audit & Validation Platform")
st.markdown("---")


def check_agent_health() -> dict | None:
    """Check Agent Service health."""
    try:
        response = httpx.get(
            f"{AGENT_SERVICE_URL}/health/ready",
            timeout=10.0,
        )
        if response.status_code == 200:
            return response.json()
        return {"status": "error", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


st.header("🏥 System Health")

if st.button("🔄 Check Infrastructure Health", type="primary"):
    with st.spinner("Checking all services..."):
        health_data = check_agent_health()

    if health_data and health_data.get("status") == "ready":
        st.success("✅ All systems operational")
    else:
        st.warning("⚠️ Some services may be unavailable")

    if health_data:
        # Show Agent Service status
        st.subheader("Agent Service")
        st.json(health_data)

        # Show individual dependency statuses
        deps = health_data.get("dependencies", {})
        if deps:
            cols = st.columns(len(deps))
            for i, (name, status) in enumerate(deps.items()):
                with cols[i]:
                    is_healthy = status.get("status") == "healthy"
                    icon = "✅" if is_healthy else "❌"
                    st.metric(
                        label=name.upper(),
                        value=f"{icon} {status.get('status', 'unknown')}",
                    )
else:
    st.info("Click the button above to check infrastructure health.")

st.markdown("---")
st.caption(
    "Invoice Audit & Validation Platform • Phase 1: Infrastructure"
)
