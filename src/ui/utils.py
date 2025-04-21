# src/ui/utils.py

import streamlit as st

def show_congratulations():
    """Show a congratulations message and balloons when all keywords are analyzed."""
    # Show celebration
    st.balloons()
    
    # Create a clear confirmation with CSS
    st.markdown("""
    <style>
    .completion-alert {
        background-color: #4CAF50;
        color: white;
        padding: 20px;
        border-radius: 8px;
        margin: 20px 0;
        text-align: center;
        font-size: 18px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .completion-alert h2 {
        margin-top: 0;
        color: white;
    }
    .completion-alert ul {
        text-align: left;
        display: inline-block;
        margin-top: 10px;
    }
    .highlight-text {
        font-weight: bold;
        text-decoration: underline;
    }
    </style>
    <div class="completion-alert">
        <h2>🎉 Congratulations! 🎉</h2>
        <p>You have successfully analyzed <span class="highlight-text">all keywords</span> for this ISP!</p>
        <p>Next steps:</p>
        <ul>
            <li>Load a new ISP for further analysis from the sidebar or</li>
            <li>Export the results using the "Export Results" section below</li>
        </ul>
        <p><strong>⚠️ Remember to save your progress by clicking "Save Analysis" in the sidebar!</strong></p>
    </div>
    """, unsafe_allow_html=True)