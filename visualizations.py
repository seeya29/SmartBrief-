import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import json
import os

def create_dashboard(emails_df, brief_summary="", reward_history=None, q_table_file='q_table.json', feedback_file='feedback_log.csv', auto_open=True, save_as_image=False):
    print("📊 Creating Analytics Dashboard...")

    fig, axs = plt.subplots(1, 3, figsize=(18, 6))

    # Subplot 1: Email Importance Distribution
    if "importance" not in emails_df.columns:
        print("⚠️ 'importance' column not found, assigning dummy scores.")
        emails_df["importance"] = [0.0] * len(emails_df)

    sns.histplot(emails_df["importance"], bins=5, kde=True, color='skyblue', ax=axs[0])
    axs[0].set_title("📧 Email Importance Distribution")
    axs[0].set_xlabel("Importance Score")

    # Subplot 2: Reward Progression
    if reward_history:
        axs[1].plot(reward_history, marker='o', linestyle='-', color='green')
        axs[1].set_title("🎯 Reward Over Episodes")
        axs[1].set_xlabel("Episode")
        axs[1].set_ylabel("Total Reward")
    else:
        axs[1].text(0.5, 0.5, "No reward history", ha='center', va='center')
        axs[1].set_title("🎯 Reward Over Episodes")

    # Subplot 3: Top Q-values (if q_table exists)
    if os.path.exists(q_table_file):
        with open(q_table_file, 'r') as f:
            q_table = json.load(f)
        q_scores = [(state, sum(actions.values())) for state, actions in q_table.items()]
        top_q = sorted(q_scores, key=lambda x: x[1], reverse=True)[:10]
        states, scores = zip(*top_q)
        sns.barplot(x=scores, y=states, ax=axs[2], palette='viridis')
        axs[2].set_title("🏆 Top Q-Value States")
        axs[2].set_xlabel("Q-Value")
        axs[2].set_ylabel("State")
    else:
        axs[2].text(0.5, 0.5, "No Q-table found", ha='center', va='center')
        axs[2].set_title("🏆 Top Q-Value States")

    plt.suptitle("📊 Smart Inbox RL Dashboard", fontsize=16)
    plt.tight_layout()

    if save_as_image:
        path = os.path.join(os.getcwd(), "dashboard.png")
        plt.savefig(path)
        print(f"[✔] Saved dashboard as {path}")

    if auto_open:
        plt.show()
