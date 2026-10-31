# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 alchevaluation
"""English desktop interface for the real-options-agent DCF engine.

Run from the project root: .venv\Scripts\python.exe app.py
The project must be installed in that environment with pip install -e .
"""

import tkinter as tk
from tkinter import ttk

from real_options_agent import CashFlow, discounted_cash_flow


class DCFApp(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=24)
        self.pack(fill="both", expand=True)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)
        self.investment = tk.StringVar(value="150")
        self.rate = tk.StringVar(value="10")
        self.time = tk.StringVar(value="3")
        self.amount = tk.StringVar()
        self.pv = tk.StringVar(value="—")
        self.npv = tk.StringVar(value="—")
        self.status = tk.StringVar()
        self._build()
        for variable in (self.investment, self.rate):
            variable.trace_add("write", lambda *_: self._invalidate())
        self.load_example()

    def _build(self):
        ttk.Label(self, text="Real Options Agent", font=("Segoe UI", 22, "bold")).grid(
            row=0, column=0, sticky="w")
        ttk.Label(self, text="Discounted cash flow calculator", font=("Segoe UI", 12)).grid(
            row=1, column=0, sticky="w", pady=(2, 18))

        settings = ttk.LabelFrame(self, text="Project assumptions", padding=14)
        settings.grid(row=2, column=0, sticky="ew")
        for column in (1, 3):
            settings.columnconfigure(column, weight=1)
        ttk.Label(settings, text="Initial investment").grid(row=0, column=0, sticky="w", padx=(0, 10))
        ttk.Entry(settings, textvariable=self.investment, width=18).grid(row=0, column=1, sticky="ew")
        ttk.Label(settings, text="Discount rate (%)").grid(row=0, column=2, sticky="w", padx=(24, 10))
        ttk.Entry(settings, textvariable=self.rate, width=18).grid(row=0, column=3, sticky="ew")
        ttk.Label(settings, text="Use one currency and the same period for the rate and cash flow times.").grid(
            row=1, column=0, columnspan=4, sticky="w", pady=(10, 0))

        editor = ttk.Frame(self, padding=(0, 16, 0, 8))
        editor.grid(row=3, column=0, sticky="ew")
        ttk.Label(editor, text="Time (periods)").grid(row=0, column=0, sticky="w")
        ttk.Label(editor, text="Cash flow amount").grid(row=0, column=1, sticky="w", padx=(12, 0))
        ttk.Entry(editor, textvariable=self.time, width=16).grid(row=1, column=0, sticky="w", pady=4)
        amount_entry = ttk.Entry(editor, textvariable=self.amount, width=22)
        amount_entry.grid(row=1, column=1, padx=12, pady=4)
        amount_entry.bind("<Return>", lambda _: self.add_flow())
        ttk.Button(editor, text="Add cash flow", command=self.add_flow).grid(row=1, column=2, padx=(0, 8))
        ttk.Button(editor, text="Remove selected", command=self.remove_selected).grid(row=1, column=3)

        table_frame = ttk.Frame(self)
        table_frame.grid(row=4, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        self.table = ttk.Treeview(table_frame, columns=("time", "amount"), show="headings", height=7)
        self.table.heading("time", text="Time (periods)")
        self.table.heading("amount", text="Cash flow amount")
        self.table.column("time", anchor="center", width=200)
        self.table.column("amount", anchor="e", width=350)
        self.table.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.bind("<Delete>", lambda _: self.remove_selected())

        actions = ttk.Frame(self, padding=(0, 12))
        actions.grid(row=5, column=0, sticky="ew")
        ttk.Button(actions, text="Calculate NPV", command=self.calculate).pack(side="left")
        ttk.Button(actions, text="Load example", command=self.load_example).pack(side="left", padx=10)
        ttk.Label(self, textvariable=self.status, wraplength=700).grid(row=6, column=0, sticky="w", pady=(0, 12))

        results = ttk.LabelFrame(self, text="Results · currency units", padding=14)
        results.grid(row=7, column=0, sticky="ew")
        results.columnconfigure((0, 1), weight=1)
        ttk.Label(results, text="Present value of cash flows").grid(row=0, column=0, sticky="w")
        ttk.Label(results, text="Net present value (NPV)").grid(row=0, column=1, sticky="w")
        ttk.Label(results, textvariable=self.pv, font=("Segoe UI", 22, "bold")).grid(row=1, column=0, sticky="w")
        ttk.Label(results, textvariable=self.npv, font=("Segoe UI", 22, "bold")).grid(row=1, column=1, sticky="w")
        ttk.Label(self, text="Enter decimals with a dot, without thousands separators.\n"
                  "The initial investment is deducted at time zero; do not add it again as a cash flow.\n"
                  "This screen calculates DCF only. Real-option exercise decisions are not implemented.",
                  wraplength=710).grid(row=8, column=0, sticky="w", pady=(16, 0))

    def _invalidate(self):
        self.pv.set("—")
        self.npv.set("—")
        self.status.set("Inputs changed. Calculate to update the results.")

    @staticmethod
    def _number(text, label):
        try:
            return float(text.strip())
        except ValueError as exc:
            raise ValueError(f"{label} must be a number. Use a dot for decimals.") from exc

    def add_flow(self):
        try:
            flow = CashFlow(self._number(self.time.get(), "Time"),
                            self._number(self.amount.get(), "Cash flow amount"))
        except ValueError as exc:
            self.status.set(f"Cannot add cash flow: {exc}")
            return
        self.table.insert("", "end", values=(repr(flow.time), repr(flow.amount)))
        self.amount.set("")
        self._invalidate()

    def remove_selected(self):
        selected = self.table.selection()
        if not selected:
            self.status.set("Select at least one cash flow to remove.")
            return
        self.table.delete(*selected)
        self._invalidate()

    def load_example(self):
        self.investment.set("150")
        self.rate.set("10")
        self.time.set("3")
        self.amount.set("")
        children = self.table.get_children()
        if children:
            self.table.delete(*children)
        for time, amount in ((1, 110), (2, 121)):
            self.table.insert("", "end", values=(str(time), str(amount)))
        self.calculate()

    def calculate(self):
        self._invalidate()
        try:
            flows = [CashFlow(*(float(value) for value in self.table.item(row, "values")))
                     for row in self.table.get_children()]
            result = discounted_cash_flow(
                flows, self._number(self.rate.get(), "Discount rate") / 100,
                self._number(self.investment.get(), "Initial investment"))
        except ValueError as exc:
            self.status.set(f"Cannot calculate: {exc}")
            return
        self.pv.set(f"{result.present_value:,.2f}")
        self.npv.set(f"{result.npv:,.2f}")
        self.status.set(f"Calculated using {len(flows)} cash flow(s). NPV = present value − initial investment.")


def main():
    root = tk.Tk()
    root.title("Real Options Agent | DCF Calculator")
    root.geometry("820x740")
    root.minsize(780, 720)
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    DCFApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
