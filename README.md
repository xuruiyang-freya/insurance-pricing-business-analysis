# Day 1: Insurance Pricing & Business Analysis

## Run
1. Install Python 3.10+.
2. Open a terminal in this folder.
3. Run `python -m pip install -r requirements.txt`.
4. Run `python day1.py`.
5. Check the new `outputs/` folder for CSV files and charts.

Data: OpenML dataset ID 41214, freMTPL2 frequency data (French motor third-party liability insurance). Internet required on first run. No proprietary CGU/IAG data is used.

The model predicts claim frequency (claims per policy-year). It **does not estimate claim severity**. The EUR 2,000 severity used in the illustrative rating table is a hypothetical assumption, not an empirical estimate or an Australian market premium. This is an educational portfolio project, not production insurance pricing. A full technical premium would require actual severity data, expenses, margins, regulatory constraints, fairness and governance review.

Outputs: frequency tables/charts by driver age, vehicle age and area; model summary; illustrative rating table. The Poisson regression is an initial baseline, not an actuarially validated production model.

If OpenML is temporarily unavailable, try again later. Do not substitute simulated results without clearly labelling them.
