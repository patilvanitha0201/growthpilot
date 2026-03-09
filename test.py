
import pandas as pd
from scoring import score_accounts
from insights import get_insight

df = pd.read_csv("data/accounts.csv")
scored = score_accounts(df)

# Test on the single most at-risk account only
worst_account = scored.iloc[0].to_dict()

print(f"Testing insight for: {worst_account['company_name']}")
print(f"Health Score: {worst_account['health_score']} {worst_account['risk_tier']}")
print("---")

insight = get_insight(worst_account)
print("RISK REASON:")
print(insight["risk_reason"])
print()
print("RECOMMENDED ACTION:")
print(insight["recommended_action"])