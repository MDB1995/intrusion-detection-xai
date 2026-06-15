from sklearn.datasets import fetch_kddcup99
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, IsolationForest
import joblib
import os

def train_and_save():
    if os.path.exists('model.pkl'):
        print("Model already exists!")
        return
        
    print("Downloading KDD99 dataset...")
    
    # Use sklearn built-in dataset
    #data = fetch_kddcup99(subset='SA', as_frame=True, percent10=True)
    data = fetch_kddcup99(as_frame=True, percent10=True)
    df = data.frame
    
    # Rename label column
    df = df.rename(columns={'labels': 'label'})
    
    # Decode bytes to string
    df['label'] = df['label'].str.decode('utf-8')
    df['protocol_type'] = df['protocol_type'].str.decode('utf-8')
    df['service'] = df['service'].str.decode('utf-8')
    df['flag'] = df['flag'].str.decode('utf-8')
    
    # Convert labels to binary
    df['label'] = df['label'].apply(lambda x: 0 if x.strip() == 'normal.' else 1)
    
    # Encode
    le = LabelEncoder()
    for col in ['protocol_type', 'service', 'flag']:
        df[col] = le.fit_transform(df[col])
    
    X = df.drop('label', axis=1)
    y = df['label']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train models
    model = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    X_normal = X_train[y_train == 0]
    anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
    anomaly_detector.fit(X_normal)
    
    # Save
    joblib.dump(model, 'model.pkl')
    joblib.dump(X_test, 'X_test.pkl')
    joblib.dump(X, 'X.pkl')
    joblib.dump(anomaly_detector, 'anomaly_model.pkl')
    
    print("✅ Done!")

if __name__ == "__main__":
    train_and_save()