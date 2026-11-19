from datasets import load_dataset

# Download dataset from Hugging Face
ds = load_dataset("Tobi-Bueck/customer-support-tickets")

# Access training split
df = ds["train"].to_pandas()

# Save original dataset
df.to_csv(
    "customer_support_tickets_original.csv",
    index=False,
    encoding="utf-8-sig"
)

print("Dataset downloaded successfully!")
print("Total records:", len(df))
print("Columns:", df.columns.tolist())