# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 alchevaluation
"""English desktop interface for the real-options-agent scenario/EMV engine.

Each scenario is edited in its own tab with an initial investment, a discount
rate, dated cash flows and a probability. The expected monetary value (EMV) is
the sum of every scenario NPV multiplied by its probability; the probabilities
of all scenarios must add up to 100%.

Run from the project root: .venv\\Scripts\\python.exe app.py
The project must be installed in that environment with pip install -e .
"""

from math import fsum, isclose

import tkinter as tk
from tkinter import messagebox, ttk

from real_options_agent import PROBABILITY_TOLERANCE, CashFlow, Scenario, evaluate_scenarios

TITLE_FONT = ("Segoe UI", 22, "bold")
SUBTITLE_FONT = ("Segoe UI", 12)
RESULT_FONT = ("Segoe UI", 22, "bold")

# (name, probability %, initial investment, discount rate %, ((time, amount), ...))
EXAMPLE_SCENARIOS = (
    ("Downside", "25", "150", "12", ((1, 60), (2, 70))),
    ("Base", "50", "150", "10", ((1, 110), (2, 121))),
    ("Upside", "25", "150", "8", ((1, 150), (2, 180))),
)


def parse_number(text, label):
    """Parse a decimal typed by the user, naming the field in the error."""
    try:
        return float(text.strip())
    except ValueError as exc:
        raise ValueError(f"{label} must be a number. Use a dot for decimals.") from exc


def probability_error(total_fraction):
    """Return the error text when probabilities do not add up to 100%, else None."""
    if isclose(total_fraction, 1.0, rel_tol=0, abs_tol=PROBABILITY_TOLERANCE):
        return None
    return (f"The probabilities of all scenarios add up to {total_fraction * 100:.10g}%, "
            "but they must add up to exactly 100%. Adjust the probabilities and calculate again.")


class ScenarioTab(ttk.Frame):
    """Editor for one scenario: probability, investment, rate and cash flows."""

    def __init__(self, master, on_change, name="", probability="", investment="", rate="", flows=()):
        super().__init__(master, padding=14)
        self.on_change = on_change
        self.name = tk.StringVar(value=name)
        self.probability = tk.StringVar(value=probability)
        self.investment = tk.StringVar(value=investment)
        self.rate = tk.StringVar(value=rate)
        self.time = tk.StringVar(value="1")
        self.amount = tk.StringVar()
        self.status = tk.StringVar()
        self._build()
        for time, amount in flows:
            self.table.insert("", "end", values=(str(time), str(amount)))
        for variable in (self.name, self.probability, self.investment, self.rate):
            variable.trace_add("write", lambda *_: self.on_change())

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        settings = ttk.LabelFrame(self, text="Scenario assumptions", padding=14)
        settings.grid(row=0, column=0, sticky="ew")
        for column in (1, 3):
            settings.columnconfigure(column, weight=1)
        ttk.Label(settings, text="Scenario name").grid(row=0, column=0, sticky="w", padx=(0, 10))
        ttk.Entry(settings, textvariable=self.name, width=18).grid(row=0, column=1, sticky="ew")
        ttk.Label(settings, text="Probability (%)").grid(row=0, column=2, sticky="w", padx=(24, 10))
        ttk.Entry(settings, textvariable=self.probability, width=18).grid(row=0, column=3, sticky="ew")
        ttk.Label(settings, text="Initial investment").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(8, 0))
        ttk.Entry(settings, textvariable=self.investment, width=18).grid(row=1, column=1, sticky="ew", pady=(8, 0))
        ttk.Label(settings, text="Discount rate (%)").grid(row=1, column=2, sticky="w", padx=(24, 10), pady=(8, 0))
        ttk.Entry(settings, textvariable=self.rate, width=18).grid(row=1, column=3, sticky="ew", pady=(8, 0))
        ttk.Label(settings, text="Use one currency and the same period for the rate and cash flow times.").grid(
            row=2, column=0, columnspan=4, sticky="w", pady=(10, 0))

        editor = ttk.Frame(self, padding=(0, 12, 0, 6))
        editor.grid(row=1, column=0, sticky="ew")
        ttk.Label(editor, text="Time (periods)").grid(row=0, column=0, sticky="w")
        ttk.Label(editor, text="Cash flow amount").grid(row=0, column=1, sticky="w", padx=(12, 0))
        ttk.Entry(editor, textvariable=self.time, width=16).grid(row=1, column=0, sticky="w", pady=4)
        amount_entry = ttk.Entry(editor, textvariable=self.amount, width=22)
        amount_entry.grid(row=1, column=1, padx=12, pady=4)
        amount_entry.bind("<Return>", lambda _: self.add_flow())
        ttk.Button(editor, text="Add cash flow", command=self.add_flow).grid(row=1, column=2, padx=(0, 8))
        ttk.Button(editor, text="Remove selected", command=self.remove_selected).grid(row=1, column=3)

        table_frame = ttk.Frame(self)
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        self.table = ttk.Treeview(table_frame, columns=("time", "amount"), show="headings", height=5)
        self.table.heading("time", text="Time (periods)")
        self.table.heading("amount", text="Cash flow amount")
        self.table.column("time", anchor="center", width=180)
        self.table.column("amount", anchor="e", width=320)
        self.table.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.bind("<Delete>", lambda _: self.remove_selected())

        ttk.Label(self, textvariable=self.status, wraplength=700).grid(row=3, column=0, sticky="w", pady=(6, 0))

    def display_name(self, index):
        return self.name.get().strip() or f"Scenario {index + 1}"

    def add_flow(self):
        try:
            flow = CashFlow(parse_number(self.time.get(), "Time"),
                            parse_number(self.amount.get(), "Cash flow amount"))
        except ValueError as exc:
            self.status.set(f"Cannot add cash flow: {exc}")
            return
        self.table.insert("", "end", values=(repr(flow.time), repr(flow.amount)))
        self.amount.set("")
        self.status.set("")
        self.on_change()

    def remove_selected(self):
        selected = self.table.selection()
        if not selected:
            self.status.set("Select at least one cash flow to remove.")
            return
        self.table.delete(*selected)
        self.status.set("")
        self.on_change()

    def cash_flows(self):
        return [CashFlow(*(float(value) for value in self.table.item(row, "values")))
                for row in self.table.get_children()]

    def to_scenario(self, index):
        """Build the engine Scenario from the fields; ValueError names the tab."""
        label = self.display_name(index)
        try:
            probability = parse_number(self.probability.get(), "Probability (%)")
            if not 0 <= probability <= 100:
                raise ValueError("Probability (%) must lie between 0 and 100.")
            investment = parse_number(self.investment.get(), "Initial investment")
            rate = parse_number(self.rate.get(), "Discount rate (%)")
            return Scenario(label, probability / 100, self.cash_flows(), investment, rate / 100)
        except ValueError as exc:
            raise ValueError(f"{label}: {exc}") from exc


class EMVApp(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=24)
        self.pack(fill="both", expand=True)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self.tabs = []
        self.emv = tk.StringVar(value="—")
        self.total_probability = tk.StringVar(value="—")
        self.probability_of_loss = tk.StringVar(value="—")
        self.standard_deviation = tk.StringVar(value="—")
        self.status = tk.StringVar()
        self._build()
        self.load_example()

    def _build(self):
        ttk.Label(self, text="Real Options Agent", font=TITLE_FONT).grid(row=0, column=0, sticky="w")
        ttk.Label(self, text="Scenario NPV and expected monetary value (EMV) calculator",
                  font=SUBTITLE_FONT).grid(row=1, column=0, sticky="w", pady=(2, 14))

        toolbar = ttk.Frame(self)
        toolbar.grid(row=2, column=0, sticky="ew", pady=(0, 6))
        ttk.Button(toolbar, text="Add scenario", command=self.add_scenario).pack(side="left")
        ttk.Button(toolbar, text="Remove current scenario", command=self.remove_scenario).pack(
            side="left", padx=10)
        ttk.Button(toolbar, text="Load example", command=self.load_example).pack(side="left")

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=3, column=0, sticky="nsew")

        actions = ttk.Frame(self, padding=(0, 12, 0, 4))
        actions.grid(row=4, column=0, sticky="ew")
        ttk.Button(actions, text="Calculate EMV", command=self.calculate).pack(side="left")
        ttk.Label(self, textvariable=self.status, wraplength=760).grid(row=5, column=0, sticky="w", pady=(0, 10))

        results = ttk.LabelFrame(self, text="Results · currency units", padding=14)
        results.grid(row=6, column=0, sticky="ew")
        results.columnconfigure(0, weight=1)
        self.summary = ttk.Treeview(
            results, columns=("scenario", "probability", "investment", "rate", "npv", "weighted"),
            show="headings", height=4)
        for column, heading, anchor, width in (
                ("scenario", "Scenario", "w", 160),
                ("probability", "Probability", "e", 90),
                ("investment", "Investment", "e", 110),
                ("rate", "Rate", "e", 70),
                ("npv", "NPV", "e", 120),
                ("weighted", "Probability × NPV", "e", 140)):
            self.summary.heading(column, text=heading)
            self.summary.column(column, anchor=anchor, width=width, stretch=column == "scenario")
        self.summary.grid(row=0, column=0, columnspan=3, sticky="ew")

        ttk.Label(results, text="Expected monetary value (EMV)").grid(row=1, column=0, sticky="w", pady=(12, 0))
        ttk.Label(results, textvariable=self.emv, font=RESULT_FONT).grid(row=2, column=0, sticky="w")
        details = ttk.Frame(results)
        details.grid(row=1, column=1, rowspan=2, columnspan=2, sticky="e")
        for row, (caption, variable) in enumerate((
                ("Sum of probabilities", self.total_probability),
                ("Probability of negative NPV", self.probability_of_loss),
                ("NPV standard deviation", self.standard_deviation))):
            ttk.Label(details, text=caption).grid(row=row, column=0, sticky="w", padx=(0, 12))
            ttk.Label(details, textvariable=variable).grid(row=row, column=1, sticky="e")

        ttk.Label(self, text="Enter decimals with a dot, without thousands separators. Probabilities and rates are in percent.\n"
                  "Each scenario has its own investment (deducted at time zero), discount rate and cash flows.\n"
                  "EMV = Σ probability × NPV over mutually exclusive scenarios whose probabilities add up to 100%.",
                  wraplength=760).grid(row=7, column=0, sticky="w", pady=(16, 0))

    # Scenario management ---------------------------------------------------

    def add_scenario(self, *args, select=True):
        tab = ScenarioTab(self.notebook, self._invalidate, *args)
        self.tabs.append(tab)
        self.notebook.add(tab, text=tab.display_name(len(self.tabs) - 1))
        if select:
            self.notebook.select(tab)
        self._invalidate()
        return tab

    def _current_tab(self):
        current = self.notebook.select()
        for tab in self.tabs:
            if str(tab) == current:
                return tab
        return None

    def remove_scenario(self):
        tab = self._current_tab()
        if tab is None:
            self.status.set("Select a scenario to remove.")
            return
        if len(self.tabs) == 1:
            self.status.set("Keep at least one scenario. Edit it instead of removing it.")
            return
        self.notebook.forget(tab)
        self.tabs.remove(tab)
        tab.destroy()
        self._invalidate()

    def _clear_scenarios(self):
        for tab in self.tabs:
            self.notebook.forget(tab)
            tab.destroy()
        self.tabs = []

    def load_example(self):
        self._clear_scenarios()
        for scenario in EXAMPLE_SCENARIOS:
            self.add_scenario(*scenario, select=False)
        if self.tabs:
            self.notebook.select(self.tabs[0])
        self.calculate()

    # Results ---------------------------------------------------------------

    def _refresh_tab_titles(self):
        for index, tab in enumerate(self.tabs):
            self.notebook.tab(tab, text=tab.display_name(index))

    def _invalidate(self):
        self._refresh_tab_titles()
        for variable in (self.emv, self.total_probability, self.probability_of_loss, self.standard_deviation):
            variable.set("—")
        children = self.summary.get_children()
        if children:
            self.summary.delete(*children)
        self.status.set("Inputs changed. Calculate to update the results.")

    def _report_error(self, title, message):
        self.status.set(f"Cannot calculate: {message}")
        messagebox.showerror(title, message, parent=self)

    def calculate(self):
        self._invalidate()
        try:
            scenarios = [tab.to_scenario(index) for index, tab in enumerate(self.tabs)]
            if not scenarios:
                raise ValueError("Add at least one scenario.")
            names = [scenario.name for scenario in scenarios]
            duplicated = next((name for name in names if names.count(name) > 1), None)
            if duplicated is not None:
                raise ValueError(f"Scenario names must be unique: '{duplicated}' is used more than once.")
        except ValueError as exc:
            self._report_error("Invalid scenario input", str(exc))
            return
        error = probability_error(fsum(scenario.probability for scenario in scenarios))
        if error:
            self._report_error("Probabilities must add up to 100%", error)
            return
        try:
            analysis = evaluate_scenarios(scenarios)
        except ValueError as exc:
            self._report_error("Cannot calculate EMV", str(exc))
            return
        for outcome in analysis.outcomes:
            self.summary.insert("", "end", values=(
                outcome.name, f"{outcome.probability:.2%}", f"{outcome.dcf.initial_investment:,.2f}",
                f"{outcome.discount_rate:.2%}", f"{outcome.dcf.npv:,.2f}",
                f"{outcome.weighted_npv + 0.0:,.2f}"))  # + 0.0 avoids printing -0.00
        self.emv.set(f"{analysis.emv:,.2f}")
        self.total_probability.set(f"{fsum(o.probability for o in analysis.outcomes):.2%}")
        self.probability_of_loss.set(f"{analysis.probability_of_loss:.2%}")
        self.standard_deviation.set(f"{analysis.standard_deviation:,.2f}")
        self.status.set(f"EMV calculated from {len(scenarios)} scenario(s): "
                        "sum of each scenario NPV multiplied by its probability.")


def main():
    root = tk.Tk()
    root.title("Real Options Agent | Scenario EMV Calculator")
    root.geometry("900x860")
    root.minsize(820, 800)
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    EMVApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
