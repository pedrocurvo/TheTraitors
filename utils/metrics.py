import pandas as pd


def compute_traitors_game_metrics(csv_file):
    """
    Computes various metrics for The Traitors game based on voting data stored in a CSV file.

    Parameters:
        csv_file (str): Path to the CSV file containing voting data.

    Returns:
        dict: A dictionary containing the computed metrics.
    """
    # Load the CSV file
    df = pd.read_csv(csv_file)

    # Get traitors and faithfuls
    traitors = df[df["Role"] == "Traitor"]["Player_ID"].unique()
    faithfuls = df[df["Role"] == "Faithful"]["Player_ID"].unique()

    # Traitor Agreement Score (TAS)
    tas_r = (
        df[df["Vote_Type"] == "Traitor"]
        .groupby("Round")["Vote_Target"]
        .apply(lambda x: x.value_counts().max() / len(x))
    )
    tas = tas_r.mean()

    # Faithful Agreement Score (FAS)
    fas_r = (
        df[(df["Vote_Type"] == "General") & (df["Role"] == "Faithful")]
        .groupby("Round")["Vote_Target"]
        .apply(lambda x: x.value_counts().max() / len(x))
    )
    fas = fas_r.mean()

    # Faithful Correctness Rate (FCR)
    fcr_r = (
        df[(df["Vote_Type"] == "General") & (df["Role"] == "Faithful")]
        .groupby("Round")["Vote_Target"]
        .apply(lambda x: (x.isin(traitors)).sum() / len(x))
    )
    fcr = fcr_r.mean()

    # Traitor Survival Rate (TSR)
    initial_traitors = len(traitors)
    eliminated_traitors = df[df["Eliminated"].isin(traitors)]["Eliminated"].nunique()
    tsr = (
        (initial_traitors - eliminated_traitors) / initial_traitors
        if initial_traitors > 0
        else 0
    )

    # Faithful Survival Rate (FSR)
    initial_faithfuls = len(faithfuls)
    eliminated_faithfuls = df[df["Eliminated"].isin(faithfuls)]["Eliminated"].nunique()
    fsr = (
        (initial_faithfuls - eliminated_faithfuls) / initial_faithfuls
        if initial_faithfuls > 0
        else 0
    )

    # Deception Effectiveness Score (DES)
    def deception_success(group):
        eliminated_player = group["Eliminated"].iloc[0]
        return (
            all(group["Vote_Target"] == eliminated_player)
            and eliminated_player in faithfuls
        )

    des_r = df[df["Vote_Type"] == "Traitor"].groupby("Round").apply(deception_success)
    des = des_r.mean()

    # Information Diffusion Rate (IDR)
    idr_r = (
        df[(df["Vote_Type"] == "General") & (df["Role"] == "Faithful")]
        .groupby("Round")["Vote_Target"]
        .apply(lambda x: (x.isin(traitors)).sum() / len(x))
    )
    idr = idr_r.mean()

    # Betrayal Recognition Rate (BRR)
    def betrayal_recognition(group):
        traitor_votes = group[group["Vote_Target"].isin(traitors)]
        max_voted = group["Vote_Target"].value_counts().idxmax()
        return (
            (traitor_votes["Vote_Target"] != max_voted).sum() / len(traitor_votes)
            if len(traitor_votes) > 0
            else 0
        )

    brr_r = (
        df[(df["Vote_Type"] == "General") & (df["Role"] == "Faithful")]
        .groupby("Round")
        .apply(betrayal_recognition)
    )
    brr = brr_r.mean()

    # Vote Switching Frequency (VSF)
    df["Prev_Vote"] = df.groupby("Player_ID")["Vote_Target"].shift(1)
    df["Vote_Changed"] = df["Vote_Target"] != df["Prev_Vote"]
    vsf_r = df.groupby("Round")["Vote_Changed"].mean()
    vsf = vsf_r.mean()

    # Trust Network Stability (TNS)
    tns_r = df.groupby("Round")["Vote_Changed"].apply(lambda x: 1 - x.mean())
    tns = tns_r.mean()

    # Return all metrics in a dictionary
    return {
        "Traitor Agreement Score (TAS)": round(tas, 3),
        "Faithful Agreement Score (FAS)": round(fas, 3),
        "Faithful Correctness Rate (FCR)": round(fcr, 3),
        "Traitor Survival Rate (TSR)": round(tsr, 3),
        "Faithful Survival Rate (FSR)": round(fsr, 3),
        "Deception Effectiveness Score (DES)": round(des, 3),
        "Information Diffusion Rate (IDR)": round(idr, 3),
        "Betrayal Recognition Rate (BRR)": round(brr, 3),
        "Vote Switching Frequency (VSF)": round(vsf, 3),
        "Trust Network Stability (TNS)": round(tns, 3),
    }
