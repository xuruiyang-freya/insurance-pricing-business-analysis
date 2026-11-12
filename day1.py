from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.datasets import fetch_openml
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import PoissonRegressor
from sklearn.metrics import mean_poisson_deviance

OUT = Path(__file__).resolve().parent / 'outputs'
OUT.mkdir(exist_ok=True)
print('Downloading public freMTPL2 frequency dataset from OpenML (ID 41214)...')
frame = fetch_openml(data_id=41214, as_frame=True, parser='auto').frame
frame.columns = [str(c).strip() for c in frame.columns]
required = ['Exposure', 'ClaimNb', 'DrivAge', 'VehAge', 'BonusMalus', 'Area']
missing = [c for c in required if c not in frame.columns]
if missing: raise ValueError(f'Missing expected columns: {missing}. Available: {frame.columns.tolist()}')
df = frame.copy()
for c in ['Exposure','ClaimNb','DrivAge','VehAge','BonusMalus']:
    df[c] = pd.to_numeric(df[c], errors='coerce')
df = df.dropna(subset=required)
df = df[(df.Exposure > 0) & (df.ClaimNb >= 0) & (df.DrivAge >= 18) & (df.VehAge >= 0)].copy()
df['Area'] = df['Area'].astype(str)
df['driver_group'] = pd.cut(df.DrivAge, [17,25,35,50,65,np.inf], labels=['18-25','26-35','36-50','51-65','66+'])
df['vehicle_group'] = pd.cut(df.VehAge, [-1,2,5,10,np.inf], labels=['0-2','3-5','6-10','11+'])

def aggregate(col):
    a = df.groupby(col, observed=True).agg(policies=('ClaimNb','size'), exposure=('Exposure','sum'), claims=('ClaimNb','sum')).reset_index()
    a['claims_per_policy_year'] = a['claims']/a['exposure']
    return a
for col in ['driver_group','vehicle_group','Area']:
    a = aggregate(col)
    a.to_csv(OUT / f'frequency_by_{col}.csv', index=False)
    fig,ax=plt.subplots(figsize=(8,4.5))
    ax.bar(a[col].astype(str),a['claims_per_policy_year'])
    ax.set(title=f'Claim frequency by {col}',xlabel=col,ylabel='Claims per policy-year')
    fig.tight_layout();fig.savefig(OUT / f'frequency_by_{col}.png',dpi=160);plt.close(fig)

# Stable, time-independent train/test partition. PoissonRegressor predicts expected claim count;
# using exposure as sample weight on annualized claim rate approximates an exposure offset.
rng = np.random.default_rng(42)
mask = rng.random(len(df)) < 0.8
features = ['DrivAge','VehAge','BonusMalus','Area']
train,test = df.loc[mask],df.loc[~mask]
pre = ColumnTransformer([('area',OneHotEncoder(handle_unknown='ignore'),['Area']),('numeric','passthrough',['DrivAge','VehAge','BonusMalus'])])
model = Pipeline([('pre',pre),('glm',PoissonRegressor(alpha=1.0,max_iter=500))])
model.fit(train[features],train.ClaimNb/train.Exposure,glm__sample_weight=train.Exposure)
rate = np.clip(model.predict(test[features]),1e-8,None)
# Exposure-weighted Poisson deviance of observed annualized claim rates.
score = mean_poisson_deviance(test.ClaimNb/test.Exposure,rate,sample_weight=test.Exposure)
baseline = train.ClaimNb.sum()/train.Exposure.sum()
baseline_score = mean_poisson_deviance(test.ClaimNb/test.Exposure,np.full(len(test),baseline),sample_weight=test.Exposure)
# Illustrative pricing only: severity is a hypothetical EUR 2,000 per claim, NOT learned from this dataset.
example = test[['DrivAge','VehAge','BonusMalus','Area','Exposure','ClaimNb']].head(30).copy()
example['predicted_claims_per_year']=rate[:30]
example['assumed_severity_eur']=2000.0
example['illustrative_pure_premium_eur']=example.predicted_claims_per_year*2000.0
example.to_csv(OUT/'illustrative_rating_table.csv',index=False)
summary = pd.DataFrame([{
    'rows_clean':len(df),'policies_train':len(train),'policies_test':len(test),
    'total_exposure_years':df.Exposure.sum(),'total_claims':df.ClaimNb.sum(),
    'observed_claim_frequency':df.ClaimNb.sum()/df.Exposure.sum(),
    'test_poisson_deviance_model':score,'test_poisson_deviance_baseline':baseline_score,
    'severity_assumption_eur':2000.0
}])
summary.to_csv(OUT/'model_summary.csv',index=False)
print(summary.to_string(index=False))
print('Saved outputs to:',OUT)
