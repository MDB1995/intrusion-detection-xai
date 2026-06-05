import pandas as pd
import numpy as np
from ctgan import CTGAN

# ── Load original data ─────────────────────────────────
print("Loading data...")
df = pd.read_csv('kddcup99.csv')

# Convert label to binary
df['label'] = df['label'].apply(lambda x: 0 if x == 'normal' else 1)

# ── Focus on rare attacks only ─────────────────────────
# These are the attack types with very few examples
rare_attacks = df[df['label'] == 1].sample(500, random_state=42)
print(f"Training CTGAN on {len(rare_attacks)} attack samples...")

# ── Define categorical columns ─────────────────────────
categorical_cols = ['protocol_type', 'service', 'flag']

# ── Train CTGAN ────────────────────────────────────────
print("Training CTGAN... this will take a few minutes...")
ctgan = CTGAN(epochs=10, verbose=True)
ctgan.fit(rare_attacks, categorical_cols)

# ── Generate synthetic samples ─────────────────────────
print("Generating 500 synthetic attack samples...")
synthetic_data = ctgan.sample(500)

print("\n Synthetic data generated!")
print("Shape:", synthetic_data.shape)
print("\nSample synthetic data:")
print(synthetic_data[['protocol_type', 'src_bytes', 
                        'dst_bytes', 'count', 'label']].head(10))

# ── Save synthetic data ────────────────────────────────
synthetic_data.to_csv('synthetic_attacks.csv', index=False)
print("\n Saved: synthetic_attacks.csv")