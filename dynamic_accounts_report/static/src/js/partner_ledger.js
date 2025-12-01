/** @odoo-module */
const { Component } = owl;
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { useRef, useState } from "@odoo/owl";
import { BlockUI } from "@web/core/ui/block_ui";
import { download } from "@web/core/network/download";
const actionRegistry = registry.category("actions");

class PartnerLedger extends Component {
    setup() {
        super.setup(...arguments);
        this.initial_render = true;
        this.orm = useService("orm");
        this.action = useService("action");
        this.tbody = useRef("tbody");
        this.unfoldButton = useRef("unfoldButton");
        this.dialog = useService("dialog");

        this.state = useState({
            partners: null,
            data: null,
            total: null,
            title: null,
            currency: null,
            filter_applied: null,
            selected_partner: [],
            selected_partner_rec: [],
            total_debit: null,
            total_debit_display: null,
            total_credit: null,
            partner_list: null,
            total_list: null,
            date_range: null,
            account: null,
            options: null,
            message_list: [],
        });

        this.load_data((this.initial_render = true));
    }

    formatNumberWithSeparators(number) {
        const parsedNumber = parseFloat(number);
        if (isNaN(parsedNumber)) {
            return "0.00";
        }
        return parsedNumber.toLocaleString("en-US", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }

    async load_data() {
        // Loads the data for the partner ledger report.
        let partner_list = [];
        let partner_totals = "";
        let totalDebitSum = 0;
        let totalCreditSum = 0;
        let currency;
        const self = this;
        const action_title = self.props.action.display_name;

        try {
            self.state.data = await self.orm.call(
                "account.partner.ledger",
                "view_report",
                [[this.wizard_id], action_title]
            );
            const dataArray = self.state.data;

            Object.entries(dataArray).forEach(([key, value]) => {
                if (key !== "partner_totals") {
                    partner_list.push(key);
                    value.forEach((entry) => {
                        entry[0].debit_display = this.formatNumberWithSeparators(
                            entry[0].debit || 0
                        );
                        entry[0].credit_display = this.formatNumberWithSeparators(
                            entry[0].credit || 0
                        );
                        entry[0].amount_currency_display =
                            this.formatNumberWithSeparators(
                                entry[0].amount_currency || 0
                            );
                        // products / product_prices / product_quantities
                        // are already provided by backend; no extra JS needed
                    });
                } else {
                    partner_totals = value;
                }
            });

            Object.values(partner_totals).forEach((partner) => {
                currency = partner.currency_id;
                totalDebitSum += partner.total_debit || 0;
                totalCreditSum += partner.total_credit || 0;
                partner.total_debit_display = this.formatNumberWithSeparators(
                    partner.total_debit || 0
                );
                partner.total_credit_display = this.formatNumberWithSeparators(
                    partner.total_credit || 0
                );
            });

            self.state.partners = partner_list;
            self.state.partner_list = partner_list;
            self.state.total_list = partner_totals;
            self.state.total = partner_totals;
            self.state.currency = currency;
            self.state.total_debit = totalDebitSum;
            self.state.total_debit_display = this.formatNumberWithSeparators(
                self.state.total_debit || 0
            );
            self.state.total_credit = totalCreditSum;
            self.state.total_credit_display = this.formatNumberWithSeparators(
                self.state.total_credit || 0
            );
            self.state.title = action_title;
        } catch (el) {
            window.location.href;
        }
    }

    async printPdf(ev) {
        // Generates and displays a PDF report for the partner ledger.
        ev.preventDefault();

        const totals = {
            total_debit: this.state.total_debit,
            total_debit_display: this.state.total_debit_display,
            total_credit: this.state.total_credit,
            total_credit_display: this.state.total_credit_display,
            currency: this.state.currency,
        };
        const action_title = this.props.action.display_name;

        return this.action.doAction({
            type: "ir.actions.report",
            report_type: "qweb-pdf",
            report_name: "dynamic_accounts_report.partner_ledger",
            report_file: "dynamic_accounts_report.partner_ledger",
            data: {
                partners: this.state.partners,
                filters: this.filter(),
                grand_total: totals,
                data: this.state.data,
                total: this.state.total,
                title: action_title,
                report_name: this.props.action.display_name,
            },
            display_name: this.props.action.display_name,
        });
    }

    filter() {
        const self = this;
        let startDate,
            endDate,
            startYear,
            startMonth,
            startDay,
            endYear,
            endMonth,
            endDay;

        if (self.state.date_range) {
            const today = new Date();
            if (self.state.date_range === "year") {
                startDate = new Date(today.getFullYear(), 0, 1);
                endDate = new Date(today.getFullYear(), 11, 31);
            } else if (self.state.date_range === "quarter") {
                const currentQuarter = Math.floor(today.getMonth() / 3);
                startDate = new Date(today.getFullYear(), currentQuarter * 3, 1);
                endDate = new Date(today.getFullYear(), (currentQuarter + 1) * 3, 0);
            } else if (self.state.date_range === "month") {
                startDate = new Date(today.getFullYear(), today.getMonth(), 1);
                endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            } else if (self.state.date_range === "last-month") {
                startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
                endDate = new Date(today.getFullYear(), today.getMonth(), 0);
            } else if (self.state.date_range === "last-year") {
                startDate = new Date(today.getFullYear() - 1, 0, 1);
                endDate = new Date(today.getFullYear() - 1, 11, 31);
            } else if (self.state.date_range === "last-quarter") {
                const lastQuarter = Math.floor((today.getMonth() - 3) / 3);
                startDate = new Date(today.getFullYear(), lastQuarter * 3, 1);
                endDate = new Date(today.getFullYear(), (lastQuarter + 1) * 3, 0);
            }

            if (startDate) {
                startYear = startDate.getFullYear();
                startMonth = startDate.getMonth() + 1;
                startDay = startDate.getDate();
            }
            if (endDate) {
                endYear = endDate.getFullYear();
                endMonth = endDate.getMonth() + 1;
                endDay = endDate.getDate();
            }
        }

        const filters = {
            partner: self.state.selected_partner_rec,
            account: self.state.account,
            options: self.state.options,
            start_date: null,
            end_date: null,
        };

        if (
            startYear !== undefined &&
            startMonth !== undefined &&
            startDay !== undefined &&
            endYear !== undefined &&
            endMonth !== undefined &&
            endDay !== undefined
        ) {
            filters.start_date = `${startYear}-${
                startMonth < 10 ? "0" : ""
            }${startMonth}-${startDay < 10 ? "0" : ""}${startDay}`;
            filters.end_date = `${endYear}-${
                endMonth < 10 ? "0" : ""
            }${endMonth}-${endDay < 10 ? "0" : ""}${endDay}`;
        }
        return filters;
    }

    async print_xlsx() {
        // Generates and downloads an XLSX report for the partner ledger.
        const self = this;

        const totals = {
            total_debit: this.state.total_debit,
            total_credit: this.state.total_credit,
            currency: this.state.currency,
        };
        const action_title = self.props.action.display_name;

        const datas = {
            partners: self.state.partners,
            data: self.state.data,
            total: self.state.total,
            title: action_title,
            filters: this.filter(),
            grand_total: totals,
        };

        const action = {
            data: {
                model: "account.partner.ledger",
                data: JSON.stringify(datas),
                output_format: "xlsx",
                report_action: self.props.action.xml_id,
                report_name: action_title,
            },
        };
        BlockUI;
        await download({
            url: "/xlsx_report",
            data: action.data,
            complete: () => unblockUI,
            error: (error) => self.call("crash_manager", "rpc_error", error),
        });
    }

    gotoJournalEntry(ev) {
        // Go to single journal entry
        return this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "account.move",
            res_id: parseInt(ev.target.attributes["data-id"].value, 10),
            views: [[false, "form"]],
            target: "current",
        });
    }

    gotoJournalItem(ev) {
        // Go to journal items list for partner
        return this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "account.move.line",
            name: "Journal Items",
            views: [[false, "list"]],
            domain: [
                ["partner_id", "=", parseInt(ev.target.attributes["data-id"].value, 10)],
                ["account_type", "in", ["liability_payable", "asset_receivable"]],
            ],
            target: "current",
        });
    }

    openPartner(ev) {
        // Open partner form
        return this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "res.partner",
            res_id: parseInt(ev.target.attributes["data-id"].value, 10),
            views: [[false, "form"]],
            target: "current",
        });
    }

    async applyFilter(val, ev, is_delete = false) {
        // Applies filters and reloads data.
        let partner_list = [];
        let partner_totals = "";
        this.state.partners = null;
        this.state.data = null;
        this.state.total = null;
        this.state.filter_applied = true;
        let totalDebitSum = 0;
        let totalCreditSum = 0;
        let currency;

        if (ev) {
            if (
                ev.input &&
                ev.input.attributes.placeholder &&
                ev.input.attributes.placeholder.value === "Partner" &&
                !is_delete
            ) {
                this.state.selected_partner.push(val[0].id);
                this.state.selected_partner_rec.push(val[0]);
            } else if (is_delete) {
                const index = this.state.selected_partner_rec.indexOf(val);
                this.state.selected_partner_rec.splice(index, 1);
                this.state.selected_partner = this.state.selected_partner_rec.map(
                    (rec) => rec.id
                );
            }
        } else {
            const attr = val.target.attributes["data-value"];
            if (val.target.name === "start_date") {
                this.state.date_range = {
                    ...this.state.date_range,
                    start_date: val.target.value,
                };
            } else if (val.target.name === "end_date") {
                this.state.date_range = {
                    ...this.state.date_range,
                    end_date: val.target.value,
                };
            } else if (attr && attr.value === "month") {
                this.state.date_range = "month";
            } else if (attr && attr.value === "year") {
                this.state.date_range = "year";
            } else if (attr && attr.value === "quarter") {
                this.state.date_range = "quarter";
            } else if (attr && attr.value === "last-month") {
                this.state.date_range = "last-month";
            } else if (attr && attr.value === "last-year") {
                this.state.date_range = "last-year";
            } else if (attr && attr.value === "last-quarter") {
                this.state.date_range = "last-quarter";
            } else if (attr && attr.value === "receivable") {
                if (val.target.classList.contains("selected-filter")) {
                    const { Receivable, ...updatedAccount } = this.state.account || {};
                    this.state.account = updatedAccount;
                    val.target.classList.remove("selected-filter");
                } else {
                    this.state.account = {
                        ...(this.state.account || {}),
                        Receivable: true,
                    };
                    val.target.classList.add("selected-filter");
                }
            } else if (attr && attr.value === "payable") {
                if (val.target.classList.contains("selected-filter")) {
                    const { Payable, ...updatedAccount } = this.state.account || {};
                    this.state.account = updatedAccount;
                    val.target.classList.remove("selected-filter");
                } else {
                    this.state.account = {
                        ...(this.state.account || {}),
                        Payable: true,
                    };
                    val.target.classList.add("selected-filter");
                }
            } else if (attr && attr.value === "draft") {
                if (val.target.classList.contains("selected-filter")) {
                    const { draft, ...updatedOptions } = this.state.options || {};
                    this.state.options = updatedOptions;
                    val.target.classList.remove("selected-filter");
                } else {
                    this.state.options = {
                        ...(this.state.options || {}),
                        draft: true,
                    };
                    val.target.classList.add("selected-filter");
                }
            }
        }

        const filtered_data = await this.orm.call(
            "account.partner.ledger",
            "get_filter_values",
            [
                this.state.selected_partner,
                this.state.date_range,
                this.state.account,
                this.state.options,
            ]
        );

        // Same processing as load_data: build lists + format numbers
        Object.entries(filtered_data).forEach(([key, value]) => {
            if (key !== "partner_totals") {
                partner_list.push(key);
                value.forEach((entry) => {
                    entry[0].debit_display = this.formatNumberWithSeparators(
                        entry[0].debit || 0
                    );
                    entry[0].credit_display = this.formatNumberWithSeparators(
                        entry[0].credit || 0
                    );
                    entry[0].amount_currency_display =
                        this.formatNumberWithSeparators(
                            entry[0].amount_currency || 0
                        );
                    // products fields are already present from backend
                });
            } else {
                partner_totals = value;
                Object.values(partner_totals).forEach((pt) => {
                    currency = pt.currency_id;
                    totalDebitSum += pt.total_debit || 0;
                    totalCreditSum += pt.total_credit || 0;
                    pt.total_debit_display = this.formatNumberWithSeparators(
                        pt.total_debit || 0
                    );
                    pt.total_credit_display = this.formatNumberWithSeparators(
                        pt.total_credit || 0
                    );
                });
            }
        });

        this.state.partners = partner_list;
        this.state.data = filtered_data;
        this.state.total = partner_totals;
        this.state.total_debit = totalDebitSum;
        this.state.total_credit = totalCreditSum;
        this.state.total_debit_display = this.formatNumberWithSeparators(
            totalDebitSum || 0
        );
        this.state.total_credit_display = this.formatNumberWithSeparators(
            totalCreditSum || 0
        );
        this.state.currency = currency;

        if (
            this.unfoldButton.el &&
            this.unfoldButton.el.classList.contains("selected-filter")
        ) {
            this.unfoldButton.el.classList.remove("selected-filter");
        }
    }

    getDomain() {
        return [];
    }

    async unfoldAll(ev) {
        // Expand / collapse all partner sections
        if (!ev.target.classList.contains("selected-filter")) {
            for (let i = 0; i < this.tbody.el.children.length; i++) {
                this.tbody.el.children[i].classList.add("show");
            }
            ev.target.classList.add("selected-filter");
        } else {
            for (let i = 0; i < this.tbody.el.children.length; i++) {
                this.tbody.el.children[i].classList.remove("show");
            }
            ev.target.classList.remove("selected-filter");
        }
    }
}

PartnerLedger.defaultProps = {
    resIds: [],
};

PartnerLedger.template = "pl_template_new";
actionRegistry.add("p_l", PartnerLedger);
