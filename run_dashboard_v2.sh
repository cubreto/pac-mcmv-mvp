#!/bin/bash

echo "🚀 Starting PAC-MCMV Dashboard V2 (CAIXA Integration)..."
echo "=================================================="
echo ""
echo "This dashboard includes:"
echo "- ⏰ Suspensivas analysis"
echo "- 🚦 Delay tracking (>90 days)"
echo "- 🔍 Bottleneck identification"
echo "- 📝 Text analysis of situations"
echo "- 🗺️ Geographic insights"
echo ""
echo "Dashboard will be available at: http://localhost:8502"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run on different port to keep original running
streamlit run streamlit_app/dashboard_v2.py --server.port 8502 --server.address localhost
