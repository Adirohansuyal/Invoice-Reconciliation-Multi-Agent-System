import os, json
from tqdm import tqdm
from graph import build_graph

with open("purchase_orders.json") as f:
    po_db = json.load(f)

app = build_graph()

invoice_files = [f for f in os.listdir("invoices") if f.endswith(".pdf")]

for file in tqdm(invoice_files, desc="Processing Invoices"):
    state = {
        "file_path": os.path.join("invoices", file),
        "po_db": po_db,
        "reasoning": []
    }

    final_state = app.invoke(state)

    print("\n" + "="*80)
    print("📄", file)
    print("🤖 Decision:", final_state["decision"])
    print("🧠 Reasoning:", final_state["reasoning"])
    print("⚠️ Issues:", final_state.get("issues"))

    with open(f"outputs/{file}.json", "w") as f:
        json.dump(final_state, f, indent=2)
