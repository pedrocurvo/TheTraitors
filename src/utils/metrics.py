"""
Game metrics calculation for TheTraitors.
"""

import pandas as pd


def compute_traitors_game_metrics(csv_file=None, df=None):
    """
    Compute various metrics for a Traitors game.

    Args:
        csv_file (str, optional): Path to the votes CSV file
        df (DataFrame, optional): Pre-loaded DataFrame with vote data

    Returns:
        dict: Dictionary of computed metrics
    """
    if df is None:
        if csv_file is None:
            raise ValueError("Either csv_file or df must be provided")
        df = pd.read_csv(csv_file)

    metrics = {}

    # Calculate basic metrics
    metrics["total_rounds"] = df["Round"].max()
    metrics["total_votes"] = len(df)
    metrics["valid_votes"] = len(df[df["Vote_Target"].notna()])

    # Calculate role-specific metrics
    traitor_votes = df[df["Role"] == "Traitor"]
    faithful_votes = df[df["Role"] == "Faithful"]

    metrics["traitor_votes"] = len(traitor_votes)
    metrics["faithful_votes"] = len(faithful_votes)

    # Calculate voting accuracy (how often faithfuls voted for traitors)
    traitor_targets = df[
        (df["Role"] == "Faithful")
        & (df["Vote_Type"] == "General")
        & (df["Vote_Target"].notna())
    ]

    # Get info about traitor IDs from the data
    traitor_ids = set(df[df["Role"] == "Traitor"]["Player_ID"].unique())

    # Calculate how many faithful votes correctly targeted traitors
    correct_votes = traitor_targets[
        traitor_targets["Vote_Target"].astype(str).isin([str(i) for i in traitor_ids])
    ]

    if len(traitor_targets) > 0:
        metrics["faithful_accuracy"] = len(correct_votes) / len(traitor_targets)
    else:
        metrics["faithful_accuracy"] = 0

    # Calculate elimination metrics
    eliminations = df[df["Eliminated"] != False].drop_duplicates(subset=["Eliminated"])
    metrics["total_eliminations"] = len(eliminations)

    # Calculate who won
    if "Eliminated" in df.columns:
        # Get the IDs of all eliminated players
        eliminated_ids = df[df["Eliminated"] != False]["Eliminated"].unique()

        # Count traitors and faithfuls eliminated
        traitor_eliminations = sum(1 for e_id in eliminated_ids if e_id in traitor_ids)
        faithful_eliminations = len(eliminated_ids) - traitor_eliminations

        metrics["traitors_eliminated"] = traitor_eliminations
        metrics["faithfuls_eliminated"] = faithful_eliminations

        # Determine winner (if possible)
        if traitor_eliminations == len(traitor_ids):
            metrics["winner"] = "Faithfuls"
        elif faithful_eliminations >= len(traitor_ids):
            metrics["winner"] = "Traitors"
        else:
            metrics["winner"] = "Unknown/Incomplete"

    return metrics
