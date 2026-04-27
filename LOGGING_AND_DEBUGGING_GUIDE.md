# Comprehensive Logging & Debugging Framework

## Problem Statement

**Current State**:
- Trade rejection reasons scattered across 7 functions
- Hard to trace: "Why was this trade skipped?"
- ML confidence not logged per-decision
- Filter interactions invisible

**Solution**: Unified decision trace that shows exactly what happened.

---

## Architecture: Decision Trace Logger

### Core Concept

```
Every trade decision → single TradeDecisionTrace object → structured log
Instead of multiple print() statements, capture decision data in a dataclass
Then serialize to JSON for analysis
```

---

## Implementation

### 1. Decision Trace Dataclass

**File**: `trade_decision_trace.py` (NEW)

```python
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from datetime import datetime
import json

@dataclass
class FilterCheckResult:
    """Individual filter evaluation result."""
    filter_name: str                    # e.g., "HTF_Alignment"
    passed: bool                        # Hard pass/soft pass
    score: float                        # 0-100 (for soft filters)
    reason: str                         # Explanation
    weight: float                       # Filter weight in decision
    blocked_trade: bool = False         # Did this filter veto the trade?

@dataclass
class TradeDecisionTrace:
    """Complete decision trace for a single trade evaluation."""
    
    # Trade context
    timestamp: str                      # ISO format
    symbol: str
    direction: str                      # "buy" or "sell"
    price: float
    entry_zone: Dict                    # {low, high, type}
    
    # Hard gates (critical, no entry if failed)
    gates_passed: bool
    gate_results: List[FilterCheckResult] = field(default_factory=list)
    
    # Soft filters (contribute to score)
    filter_results: List[FilterCheckResult] = field(default_factory=list)
    
    # ML scoring
    ml_score: float = 0.0               # 0-100
    ml_info: Dict = field(default_factory=dict)  # Model type, confidence level, etc.
    feature_score: float = 0.0          # 0-100
    
    # Final decision
    combined_score: float = 0.0         # 0-100
    size_multiplier: float = 0.0        # Position size adjustment
    should_trade: bool = False
    decision_reason: str = ""
    
    # Debug info
    supporting_factors: List[str] = field(default_factory=list)
    blocking_factors: List[str] = field(default_factory=list)
    
    # Risk/Reward
    sl: float = 0.0
    tp: float = 0.0
    rr_ratio: float = 0.0
    
    # Session info
    session: str = ""                   # london_open, ny_open, etc.
    hour: int = 0
    
    def to_json(self) -> str:
        """Serialize to JSON for logging/analysis."""
        return json.dumps(asdict(self), indent=2, default=str)
    
    def to_simple_string(self) -> str:
        """Human-readable one-liner."""
        status = "TRADE" if self.should_trade else "SKIP"
        return (
            f"[{self.timestamp}] {self.symbol} {self.direction.upper()} "
            f"@ {self.price:.5f} | {status} (Score: {self.combined_score:.0f}/100) "
            f"| {self.decision_reason[:50]}"
        )
    
    def log_detailed(self, logger) -> None:
        """Log full decision trace to logger."""
        logger.info(f"\n{'='*80}")
        logger.info(f"TRADE DECISION TRACE: {self.symbol} {self.direction.upper()}")
        logger.info(f"{'='*80}")
        logger.info(f"Timestamp: {self.timestamp}")
        logger.info(f"Price: {self.price:.5f} | Entry Zone: {self.entry_zone}")
        logger.info(f"Session: {self.session} (Hour {self.hour} UTC)")
        
        # Hard gates
        logger.info(f"\n[HARD GATES] {'✓ PASSED' if self.gates_passed else '✗ FAILED'}")
        for gate in self.gate_results:
            status = "✓" if gate.passed else "✗"
            logger.info(f"  {status} {gate.filter_name}: {gate.reason}")
        
        if not self.gates_passed:
            logger.info(f"\n➜ DECISION: BLOCKED AT GATE ({self.gate_results[0].reason})")
            return
        
        # Soft filters
        logger.info(f"\n[SOFT FILTERS] (Total Score: {self.combined_score:.0f}/100)")
        for filt in self.filter_results:
            bar = "█" * int(filt.score / 5) + "░" * (20 - int(filt.score / 5))
            logger.info(
                f"  {bar} {filt.filter_name:25s} {filt.score:5.0f}/100 "
                f"(W:{filt.weight:.0%}) - {filt.reason[:40]}"
            )
        
        # ML vs. Heuristics breakdown
        logger.info(f"\n[SCORING BREAKDOWN]")
        logger.info(f"  ML Model: {self.ml_score:.0f}/100 ({self.ml_info.get('confidence_level', '?')})")
        logger.info(f"  Features: {self.feature_score:.0f}/100")
        logger.info(f"  Combined: {self.combined_score:.0f}/100 (65% ML + 35% Features)")
        
        # Risk/Reward
        logger.info(f"\n[RISK/REWARD]")
        logger.info(f"  Entry: {self.price:.5f}")
        logger.info(f"  Stop Loss: {self.sl:.5f}")
        logger.info(f"  Take Profit: {self.tp:.5f}")
        logger.info(f"  R:R Ratio: 1:{self.rr_ratio:.2f}")
        
        # Position sizing
        logger.info(f"\n[POSITION SIZING]")
        if self.combined_score < 60:
            size_desc = "SKIP (too risky)"
        elif self.combined_score < 75:
            size_desc = "SMALL (0.3-0.7x)"
        elif self.combined_score < 85:
            size_desc = "STANDARD (0.7-1.0x)"
        else:
            size_desc = "AGGRESSIVE (1.0-1.2x)"
        logger.info(f"  Size Multiplier: {self.size_multiplier:.2f}x ({size_desc})")
        
        # Supporting factors
        if self.supporting_factors:
            logger.info(f"\n[SUPPORTING FACTORS] ({len(self.supporting_factors)} total)")
            for factor in self.supporting_factors:
                logger.info(f"  ✓ {factor}")
        
        # Blocking factors
        if self.blocking_factors:
            logger.info(f"\n[BLOCKING FACTORS] ({len(self.blocking_factors)} total)")
            for factor in self.blocking_factors:
                logger.info(f"  ✗ {factor}")
        
        # Final decision
        logger.info(f"\n{'='*80}")
        logger.info(f"FINAL DECISION: {'✓ TRADE APPROVED' if self.should_trade else '✗ TRADE SKIPPED'}")
        logger.info(f"Reason: {self.decision_reason}")
        logger.info(f"{'='*80}\n")

class TradeDecisionLogger:
    """Manages logging of all trade decisions."""
    
    def __init__(self, log_file: str = "trade_decisions.log", json_file: str = "trade_decisions.jsonl"):
        import logging
        
        # Text log
        self.logger = logging.getLogger("TradeDecisions")
        self.logger.setLevel(logging.DEBUG)
        
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        self.logger.addHandler(handler)
        
        # JSON log (one trace per line)
        self.json_file = json_file
    
    def log_decision(self, trace: TradeDecisionTrace) -> None:
        """Log a decision (text + JSON)."""
        # Text log
        trace.log_detailed(self.logger)
        
        # JSON log (append)
        try:
            with open(self.json_file, 'a') as f:
                f.write(trace.to_json() + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write JSON log: {e}")
    
    def log_simple(self, trace: TradeDecisionTrace) -> None:
        """Log one-liner to both files."""
        simple = trace.to_simple_string()
        self.logger.info(simple)
        
        # JSON log
        try:
            with open(self.json_file, 'a') as f:
                f.write(trace.to_json() + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write JSON log: {e}")

# Global logger instance
trade_decision_logger = TradeDecisionLogger()

```

---

### 2. Integration into Decision Engine

**Modify `unified_trade_decision()` to use TradeDecisionTrace**:

```python
def unified_trade_decision_v2_with_logging(symbol, ml_confidence, features, df, entry, sl, tp):
    """
    ML-centric decision with comprehensive logging.
    """
    from trade_decision_trace import TradeDecisionTrace, FilterCheckResult, trade_decision_logger
    
    # Initialize trace
    trace = TradeDecisionTrace(
        timestamp=datetime.now().isoformat(),
        symbol=symbol,
        direction="buy",  # Will be updated
        price=df.iloc[-1]['close'],
        entry_zone={'type': 'fvg'},
        sl=sl,
        tp=tp,
        session=features.get('session', 'unknown'),
        hour=features.get('hour', 0)
    )
    
    # Analyze both directions
    buy_context = analyze_direction("buy")
    sell_context = analyze_direction("sell")
    
    # === STEP 1: HARD GATES ===
    # Gate 1: Entry zone valid
    entry_zone_ok = is_price_in_entry_zone(buy_context)
    trace.gate_results.append(FilterCheckResult(
        filter_name="Entry Zone Valid",
        passed=entry_zone_ok,
        score=100 if entry_zone_ok else 0,
        reason="Price within 50 pips of FVG/POI" if entry_zone_ok else "Price >50 pips from structure",
        weight=1.0,
        blocked_trade=not entry_zone_ok
    ))
    
    # Gate 2: HTF aligned
    htf_ok = is_htf_aligned(buy_context)
    trace.gate_results.append(FilterCheckResult(
        filter_name="HTF Alignment",
        passed=htf_ok,
        score=100 if htf_ok else 0,
        reason="H4 trend aligns" if htf_ok else "H4 trend opposes signal",
        weight=1.0,
        blocked_trade=not htf_ok
    ))
    
    trace.gates_passed = entry_zone_ok and htf_ok
    
    if not trace.gates_passed:
        trace.should_trade = False
        trace.decision_reason = f"Blocked at gate: {[g.reason for g in trace.gate_results if not g.passed][0]}"
        trace.blocking_factors = [g.reason for g in trace.gate_results if not g.passed]
        trade_decision_logger.log_decision(trace)
        return False, None, 0.0, trace.decision_reason, None
    
    # === STEP 2: SOFT FILTERS ===
    # Filter 1: BOS + Pullback
    bos_score, bos_reason = score_bos_pullback(buy_context)
    trace.filter_results.append(FilterCheckResult(
        filter_name="BOS_Pullback",
        passed=bos_score >= 25,
        score=bos_score,
        reason=bos_reason,
        weight=0.40
    ))
    
    # Filter 2: Volume impulse
    vol_score, vol_reason = score_volume_impulse(buy_context)
    trace.filter_results.append(FilterCheckResult(
        filter_name="Volume_Impulse",
        passed=vol_score >= 15,
        score=vol_score,
        reason=vol_reason,
        weight=0.30
    ))
    
    # Filter 3: Risk/Reward
    rr_score, rr_reason = score_risk_reward(buy_context)
    trace.filter_results.append(FilterCheckResult(
        filter_name="Risk_Reward",
        passed=rr_score >= 12,
        score=rr_score,
        reason=rr_reason,
        weight=0.20
    ))
    
    # Filter 4: Market regime
    regime_score, regime_reason = score_market_regime(buy_context)
    trace.filter_results.append(FilterCheckResult(
        filter_name="Market_Regime",
        passed=regime_score >= 5,
        score=regime_score,
        reason=regime_reason,
        weight=0.10
    ))
    
    # === STEP 3: ML SCORING ===
    from ml_decision_engine import MLDecisionEngine
    ml_engine = MLDecisionEngine(f'autoencoder_{symbol}.h5')
    trace.ml_score, trace.ml_info = ml_engine.score_setup(buy_context)
    
    # === STEP 4: FEATURE SCORING ===
    trace.feature_score = analyze_geometry(buy_context, entry, sl, tp)
    
    # === STEP 5: COMBINE ===
    trace.combined_score = 0.65 * trace.ml_score + 0.35 * trace.feature_score
    trace.supporting_factors = [f.reason for f in trace.filter_results if f.passed]
    trace.blocking_factors = [f.reason for f in trace.filter_results if not f.passed]
    
    # === STEP 6: DECISION ===
    if trace.combined_score < 60:
        trace.should_trade = False
        trace.decision_reason = f"Score {trace.combined_score:.0f}/100 below minimum 60"
        trace.size_multiplier = 0.0
    elif trace.combined_score < 75:
        trace.should_trade = True
        trace.decision_reason = f"ML-approved trade (score {trace.combined_score:.0f}/100)"
        trace.size_multiplier = 0.7
    else:
        trace.should_trade = True
        trace.decision_reason = f"ML-approved trade (high confidence {trace.combined_score:.0f}/100)"
        trace.size_multiplier = min(1.2, 1.0 + (trace.combined_score - 85) / 15)
    
    # === LOGGING ===
    trade_decision_logger.log_decision(trace)
    
    return trace.should_trade, "buy", trace.combined_score, trace.decision_reason, buy_context

```

---

### 3. Analysis Tools

**File**: `analyze_trade_logs.py` (NEW)

```python
import json
import pandas as pd
from pathlib import Path
from collections import defaultdict

def parse_trade_decision_log(json_log_file: str) -> pd.DataFrame:
    """
    Parse JSONL trade decision log into DataFrame for analysis.
    """
    records = []
    with open(json_log_file, 'r') as f:
        for line in f:
            try:
                record = json.loads(line)
                records.append(record)
            except:
                continue
    
    return pd.DataFrame(records)

def analyze_decisions(df: pd.DataFrame) -> Dict:
    """
    Analyze trade decision patterns.
    
    Returns:
        dict with:
        - Total decisions
        - % traded vs. skipped
        - Avg score for trades vs. skips
        - Filter effectiveness (which filters block most?)
        - Blocking reason frequency
        - Supporting factor frequency
    """
    
    total = len(df)
    traded = len(df[df['should_trade'] == True])
    skipped = len(df[df['should_trade'] == False])
    
    # Score analysis
    trade_scores = df[df['should_trade'] == True]['combined_score']
    skip_scores = df[df['should_trade'] == False]['combined_score']
    
    # Blocking reasons
    blocking_reasons = defaultdict(int)
    for reasons in df['blocking_factors']:
        for reason in reasons:
            blocking_reasons[reason] += 1
    
    # Supporting factors
    supporting_factors = defaultdict(int)
    for factors in df['supporting_factors']:
        for factor in factors:
            supporting_factors[factor] += 1
    
    return {
        'total_decisions': total,
        'traded': traded,
        'skipped': skipped,
        'trade_pct': traded / total if total > 0 else 0,
        'avg_score_traded': float(trade_scores.mean()) if len(trade_scores) > 0 else 0,
        'avg_score_skipped': float(skip_scores.mean()) if len(skip_scores) > 0 else 0,
        'blocking_reasons': dict(sorted(blocking_reasons.items(), key=lambda x: x[1], reverse=True)),
        'supporting_factors': dict(sorted(supporting_factors.items(), key=lambda x: x[1], reverse=True)),
    }

def print_analysis(analysis: Dict) -> None:
    """Pretty-print analysis."""
    print("\n" + "="*80)
    print("TRADE DECISION ANALYSIS")
    print("="*80)
    print(f"Total Decisions: {analysis['total_decisions']}")
    print(f"  Traded: {analysis['traded']} ({analysis['trade_pct']:.1%})")
    print(f"  Skipped: {analysis['skipped']}")
    print(f"\nScore Analysis:")
    print(f"  Avg Score (Traded): {analysis['avg_score_traded']:.0f}/100")
    print(f"  Avg Score (Skipped): {analysis['avg_score_skipped']:.0f}/100")
    print(f"\nTop Blocking Reasons:")
    for reason, count in list(analysis['blocking_reasons'].items())[:5]:
        print(f"  • {reason}: {count} times")
    print(f"\nTop Supporting Factors:")
    for factor, count in list(analysis['supporting_factors'].items())[:5]:
        print(f"  • {factor}: {count} times")
    print("="*80 + "\n")

# Example usage
if __name__ == "__main__":
    df = parse_trade_decision_log("trade_decisions.jsonl")
    analysis = analyze_decisions(df)
    print_analysis(analysis)

```

---

## Expected Log Output

### Text Log (trade_decisions.log)

```
================================================================================
TRADE DECISION TRACE: EURUSD BUY
================================================================================
Timestamp: 2025-12-22T14:35:20.123456
Price: 1.04560 | Entry Zone: {'type': 'fvg'}
Session: london_open (Hour 7 UTC)

[HARD GATES] ✓ PASSED
  ✓ Entry Zone Valid: Price within 50 pips of FVG/POI
  ✓ HTF Alignment: H4 trend aligns

[SOFT FILTERS] (Total Score: 78/100)
  ████████████████░░░░ BOS_Pullback                35/100 (W:40%) - BOS confirmed, 55% retrace
  ██████████░░░░░░░░░░ Volume_Impulse             30/100 (W:30%) - Large candle, 1.3x volume
  ██████████████████░░ Risk_Reward                18/100 (W:20%) - 1:2.5 R:R ratio
  ████████░░░░░░░░░░░░  Market_Regime              8/100 (W:10%) - Trending up, continuation

[SCORING BREAKDOWN]
  ML Model: 82/100 (high)
  Features: 65/100
  Combined: 78/100 (65% ML + 35% Features)

[RISK/REWARD]
  Entry: 1.04560
  Stop Loss: 1.04410
  Take Profit: 1.04820
  R:R Ratio: 1:2.50

[POSITION SIZING]
  Size Multiplier: 1.00x (STANDARD (0.7-1.0x))

[SUPPORTING FACTORS] (4 total)
  ✓ BOS confirmed, 55% retrace
  ✓ Large candle, 1.3x volume
  ✓ 1:2.5 R:R ratio
  ✓ Trending up, continuation

[BLOCKING FACTORS] (0 total)

================================================================================
FINAL DECISION: ✓ TRADE APPROVED
Reason: ML-approved trade (high confidence 78/100)
================================================================================
```

### JSON Log (trade_decisions.jsonl)

```json
{
  "timestamp": "2025-12-22T14:35:20.123456",
  "symbol": "EURUSD",
  "direction": "buy",
  "price": 1.04560,
  "entry_zone": {"type": "fvg"},
  "gates_passed": true,
  "gate_results": [
    {
      "filter_name": "Entry Zone Valid",
      "passed": true,
      "score": 100.0,
      "reason": "Price within 50 pips of FVG/POI",
      "weight": 1.0,
      "blocked_trade": false
    },
    ...
  ],
  "filter_results": [...],
  "ml_score": 82.0,
  "ml_info": {"confidence_level": "high", "model_type": "autoencoder"},
  "feature_score": 65.0,
  "combined_score": 78.0,
  "size_multiplier": 1.0,
  "should_trade": true,
  "decision_reason": "ML-approved trade (high confidence 78/100)",
  "supporting_factors": ["BOS confirmed, 55% retrace", ...],
  "blocking_factors": [],
  "sl": 1.04410,
  "tp": 1.04820,
  "rr_ratio": 2.5,
  "session": "london_open",
  "hour": 7
}
```

---

## Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **Debug Time** | 30-60 min | <5 min |
| **Visibility** | "Trade skipped" | "Blocked: ML score 45/100 (fuzzy pattern)" |
| **Analysis** | Manual guess | Systematic log analysis |
| **Adaptation** | Guess which filter to adjust | Data-driven tuning |
| **ML Feedback** | None | Clear: "This setup needed X feature" |

---

## Next Steps

1. **Implement** `trade_decision_trace.py` and `TradeDecisionLogger`
2. **Integrate** into `unified_trade_decision()` 
3. **Deploy** with logging enabled
4. **Analyze** after 100 decisions: Which filters block most? Which support most?
5. **Iterate**: Use logs to refine thresholds

