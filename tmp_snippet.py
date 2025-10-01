                st.markdown(
                    """
                    <style>
                    .status-cell {
                        display: flex;
                        justify-content: center;
                        align-items: center;
                    }
                    .status-badge {
                        display: inline-block;
                        padding: 0.25rem 0.7rem;
                        border-radius: 999px;
                        font-size: 0.85rem;
                        font-weight: 600;
                        background: #e9ecef;
                        color: #495057;
                    }
                    .status-cell.status-success button,
                    .status-cell.status-success div[data-testid="stButton"] button,
                    .status-badge.status-success {
                        background: #d1f7c4 !important;
                        color: #215732 !important;
                        border: 1px solid #b7e4a8 !important;
                    }
                    .status-cell.status-error button,
                    .status-cell.status-error div[data-testid="stButton"] button,
                    .status-badge.status-error {
                        background: #f9d7d9 !important;
                        color: #842029 !important;
                        border: 1px solid #f3b4b9 !important;
                    }
                    .status-cell.status-null button,
                    .status-cell.status-null div[data-testid="stButton"] button,
                    .status-badge.status-null {
                        background: #e9ecef !important;
                        color: #495057 !important;
                        border: 1px solid #d5d8dc !important;
                    }
                    .status-cell div[data-testid="stButton"] button {
                        border-radius: 999px;
                        font-weight: 600;
                        width: 100%;
                    }
                    .status-modal-close button {
                        background: transparent !important;
                        color: #0f172a !important;
                        border: none !important;
                        font-size: 1.2rem !important;
                        font-weight: 600 !important;
                        box-shadow: none !important;
                    }
                    .status-modal-close button:hover {
                        background: #e2e8f0 !important;
                        color: #0f172a !important;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
