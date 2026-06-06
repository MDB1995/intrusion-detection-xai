import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import shap
import matplotlib.pyplot as plt
from explain import explain_connection
import joblib

# Load your dataset
df = pd.read_csv('kddcup99.csv')
synthetic_df = pd.read_csv('synthetic_attacks.csv')
#df = pd.read_csv('synthetic_attacks.csv')  # Use synthetic data for better attack representation
#print("Dataset loaded", df.shape)
df = pd.concat([df, synthetic_df], ignore_index=True)
print("Combined dataset shape:", df.shape)

# Convert the 'label' column to binary (0 for normal, 1 for attack)
df['label'] = df['label'].apply(lambda x: 0 if x == 'normal' else 1)
print("Labels converted")
print("Normal (0):", (df['label'] == 0).sum())
print("Attack (1):", (df['label'] == 1).sum())

# Encode text columns into numbers
le = LabelEncoder()
for col in ['protocol_type', 'service', 'flag']:
    df[col] = le.fit_transform(df[col]) 
print("Categorical features encoded")

# Split features and targets
X = df.drop('label', axis=1)
y = df['label']
print("Features and target separated")
print("Features shape:", X.shape)
print("Target shape:", y.shape)

# Check for missing values
print("\n Missing values in features:", X.isnull().sum().sum())

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print("Data split into training and testing sets")
print("Training set shape:", X_train.shape)
print("Testing set shape:", X_test.shape)

# Train a Random Forest Classifier
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)                     
print("Model trained")

# Make predictions and evaluate the model
y_pred = model.predict(X_test)
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=['Normal', 'Attack']))
print("Accuracy Score:")
print(accuracy_score(y_test, y_pred))

# SHAP values for explainability
print("\nCalculating SHAP values... please wait.. ")

# Use a small sample for speed
X_sample = X_test.sample(100, random_state=42)

# Create SHAP explainer
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_sample)

# Shape is (100, 41, 2) → take attack class
shap_attack = shap_values[:, :, 1]

# Plot 1: Feature Importance Bar plot
print("Generating Feature Importance plot...")
shap.summary_plot(shap_attack, X_sample, plot_type="bar", show=False)
plt.tight_layout()
plt.savefig('feature_importance.png')
plt.close()
print("Saved: feature_importance.png")

# Plot 2: SHAP Summary plot
print("Generating SHAP Summary plot...")
shap.summary_plot(shap_attack, X_sample, show=False)
plt.tight_layout()
plt.savefig('shap_summary.png')
plt.close()
print("Saved: shap_summary.png")

print("Done!")


# Show actual values for the 100 samples
print("\nTop 5 features - actual values in your 100 samples:")
print(X_sample[['dst_bytes', 'count', 'logged_in', 
                 'src_bytes', 'srv_count']].describe())

sample_idx = 0
connection = X_sample.iloc[sample_idx]
prediction = model.predict([connection])[0]

#explain_connection(connection, shap_attack[sample_idx], prediction, X, sample_idx)

top_features, ai_explanation = explain_connection(connection, shap_attack[sample_idx], prediction, X, sample_idx)

print("\n" + "="*60)
print("SECURITY ANALYSIS REPORT")
print("="*60)
print(f"\nConnection #{sample_idx + 1} Analysis:")
print(f"   Prediction: {'ATTACK' if prediction == 1 else ' NORMAL'}")
print(f"\nTop 3 features:")
for feat, shap_val in top_features.items():
    actual_val = connection[feat]
    print(f"\n   🔹 {feat}: {actual_val:.2f} (SHAP: {shap_val:.4f})")
print("\n AI Explanation:")
print("-"*60)
print(ai_explanation)
print("="*60)


# RAG Enhanced Explanation
from rag_explain import rag_explain
print("\n" + "="*60)
print("RAG-ENHANCED THREAT INTELLIGENCE REPORT")
print("="*60)
rag_explanation, matched_threats = rag_explain(
    top_features, prediction, connection
)
print("\nMatched MITRE ATT&CK Techniques:")
for threat in matched_threats:
    print(f"  • {threat['name']} ({threat['id']})")
print("\nAI Analysis with Threat Intelligence:")
print("-"*60)
print(rag_explanation)
print("="*60)



# report = explain_connection(connection, shap_row, prediction, X)
# print(report)

# print("Shape:", df.shape)

# print("\nLabel distribution:")
# print(df['label'].value_counts())



# Save model and data for app.py to use
print("Saving model...")
joblib.dump(model, 'model.pkl')
joblib.dump(X_test, 'X_test.pkl')
joblib.dump(X, 'X.pkl')
print("Model saved!")