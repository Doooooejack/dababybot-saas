"""
CONFIDENCE-BASED RISK SCALING - MIGRATION GUIDE

This document shows which trading loop calls need to be updated to pass
the confidence parameter and use the new confidence-based position sizing.

STATUS: Functions are implemented. Calls need to be updated to use them.
"""

# ============================================================================
# LOCATIONS THAT NEED UPDATING
# ============================================================================

# The following locations call place_trade_with_model_selection() but 
# DO NOT pass confidence parameter:
#
# Line 4038:    result = place_trade_with_model_selection(symbol, final_signal, lot, sl, tp, ...)
# Line 26975:   result = place_trade_with_model_selection(symbol, direction, LOT_SIZE, sl, tp, ...)
# Line 27010:   place_trade_with_model_selection(symbol, direction, lot, sl, tp, ...)
# Line 30318:   result = place_trade_with_model_selection(symbol, signal_to_use, LOT_SIZE, sl, tp, ...)
# Line 31220:   result = place_trade_with_model_selection(symbol, ml_signal, lot_size, sl, tp, ...)
# And 15+ more locations...

# ============================================================================
# WHAT NEEDS TO BE DONE
# ============================================================================

# BEFORE (current - no confidence):
# result = place_trade_with_model_selection(
#     symbol, final_signal, lot, sl, tp,
#     context={'symbol': symbol, 'signal': final_signal, 'price': entry, 'df': df}
# )

# AFTER (with confidence):
# ml_confidence = get_ml_confidence_from_your_model(symbol, final_signal)  # Get confidence from your ML model
# result = place_trade_with_model_selection(
#     symbol, final_signal, lot, sl, tp,
#     confidence=ml_confidence,  # <-- ADD THIS
#     context={'symbol': symbol, 'signal': final_signal, 'price': entry, 'df': df}
# )

# ============================================================================
# NEXT STEPS TO ACTIVATE CONFIDENCE-BASED RISK SCALING
# ============================================================================

print("""
CONFIDENCE-BASED RISK SCALING - NEXT STEPS

The system is implemented and ready, but needs one more step to activate:

STEP 1: Update Trading Loop Calls
   - Modify all place_trade_with_model_selection() calls to pass confidence
   - Get ML confidence score from your model (usually 0.50-0.99)
   - Pass as: confidence=ml_confidence
   
   Affected lines: ~20 locations in botfriday999990000th.py

STEP 2: Map ML Confidence to Risk Tiers
   - Your ML model outputs confidence (e.g., 0.92)
   - System automatically maps to tier:
     * 0.92 -> A+ -> 1.0% risk
     * 0.85 -> A  -> 0.7% risk
     * 0.75 -> B  -> 0.5% risk
     * 0.65 -> C/D -> 0.3% risk

STEP 3: Verify Integration
   - Run: python -c "from botfriday999990000th import *; print_confidence_risk_matrix()"
   - Should see confidence tier matrix
   - Test with small account first

STEP 4: Monitor Results
   - Track win rate per confidence tier
   - A+ trades should win more often than C/D trades
   - Adjust thresholds if needed

============================================================
FUNCTIONS ACTIVE AND READY:
- calculate_risk_by_confidence() - IMPLEMENTED
- calculate_lot_with_confidence_risk() - IMPLEMENTED  
- get_fixed_lot_size() - IMPLEMENTED (rewritten)
- get_confidence_tier() - IMPLEMENTED
- log_trade_decision_with_confidence() - IMPLEMENTED
- print_confidence_risk_matrix() - IMPLEMENTED

INTEGRATION STATUS:
- place_trade() accepts confidence parameter - READY
- place_trade_with_model_selection() passes to place_trade() - READY
- get_fixed_lot_size() uses confidence for sizing - READY

REMAINING: Update 20+ trading loop calls to pass confidence parameter
============================================================
""")
