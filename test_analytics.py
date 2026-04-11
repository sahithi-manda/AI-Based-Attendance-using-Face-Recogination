import sys
print("Testing Analytics...")
try:
    from core import analytics
    print(1)
    ar = analytics.get_at_risk_students()
    print("At Risk length:", len(ar))
    pa = analytics.get_predictive_alerts()
    print("Predictive length:", len(pa))
    print("SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
    print("FAIL")
