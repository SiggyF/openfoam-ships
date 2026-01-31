import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
import logging
from pathlib import Path
import json
import pickle

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RESULTS_FILE = Path("results/dtc_sweep.csv")
MODEL_OUTPUT = Path("results/dtc_surrogate_model.pkl")
PLOT_OUTPUT = Path("results/dtc_surrogate_plot.png")

# DTC Hull Parameters
# Scale factor for DTC is usually around 1:59.407 (Lpp_ship=173.8m, Lpp_model=something)
# But here we are simulating a 3m model.
# ESI DTC is often 1:40 or similar depending on the specific model test.
# Let's stick to the model scale units for the surrogate for now (Power vs Velocity at model scale).
LENGTH_MODEL = 3.0 
RHO = 998.8 # Water density (kg/m3)

# Literature Data (Placeholder - Optional)
LITERATURE_DATA = []

def load_data(filepath):
    """Load simulation results."""
    if not filepath.exists():
        raise FileNotFoundError(f"Results file not found: {filepath}")
    return pd.read_csv(filepath)

def calculate_coefficients(df, scale=1.0):
    """Calculate non-dimensional coefficients (Ct, Fn) if not present."""
    # Assuming df has 'velocity' (m/s) and 'force_x' (N)
    
    # Model scale length
    # L_model = LPP * scale
    
    # For now, we will focus on P vs V fitting directly for the surrogate
    df['power'] = df['force_x'] * df['velocity']
    return df

def train_model(df):
    """Train a polynomial regression model: P = f(V)."""
    X = df[['velocity']]
    y = df['power']
    
    # Physics suggests P ~ V^3, so distinct features fit well
    # We use a cubic polynomial
    degree = 3
    model = make_pipeline(PolynomialFeatures(degree), LinearRegression())
    model.fit(X, y)
    
    return model

def plot_results(model, df, output_path):
    """Plot simulation data, model fit, and literature comparison."""
    plt.figure(figsize=(10, 6))
    
    # 1. Plot Simulation Data
    plt.scatter(df['velocity'], df['power'], color='blue', label='Simulation (OpenFOAM)', zorder=5)
    
    # 2. Plot Model Fit
    v_range = np.linspace(df['velocity'].min() * 0.9, df['velocity'].max() * 1.1, 100).reshape(-1, 1)
    p_pred = model.predict(v_range)
    plt.plot(v_range, p_pred, color='red', linestyle='--', label=f'Surrogate Model (Poly Deg 3)')
    
    # 3. Plot Literature (Qualitative check if units align, otherwise separate axis)
    # Note: Literature is usually Fr vs Ct. We need to convert to V vs P for direct comparison
    # or plotting Fr vs Ct. 
    # For this script, we'll keep it simple: P vs V.
    
    plt.title('DTC Hull: Effective Power vs. Velocity (Model Scale)')
    plt.xlabel('Velocity (m/s)')
    plt.ylabel('Effective Power (W)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig(output_path)
    logging.info(f"Plot saved to {output_path}")

def main():
    try:
        logging.info("Loading data...")
        # Mock data for testing script interaction if file doesn't exist
        if not RESULTS_FILE.exists():
            logging.warning(f"{RESULTS_FILE} not found. Using mock data for testing.")
            df = pd.DataFrame({
                'velocity': [0.5, 1.0, 1.5, 2.0, 2.2],
                'force_x': [10, 40, 90, 160, 200]
            })
        else:
            df = load_data(RESULTS_FILE)
            
        df = calculate_coefficients(df)
        
        logging.info("Training surrogate model...")
        model = train_model(df)
        
        logging.info("Plotting results...")
        plot_results(model, df, PLOT_OUTPUT)
        
        # Save model
        with open(MODEL_OUTPUT, 'wb') as f:
            pickle.dump(model, f)
        logging.info(f"Model saved to {MODEL_OUTPUT}")
        
    except Exception as e:
        logging.error(f"Training failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()
