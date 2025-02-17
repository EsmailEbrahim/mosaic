import frappe


def set_order_number(doc, event):
    pos_profile = doc.pos_profile
    if doc.order_type == "Aggregators":
        last_invoice = frappe.get_value(
            "POS Opening Entry",
            {"pos_profile": pos_profile, "status": "Open"},
            "custom_ury_last_aggregator_invoice",
        )
    else:
        last_invoice = frappe.get_value(
            "POS Opening Entry",
            {"pos_profile": pos_profile, "status": "Open"},
            "custom_ury_last_invoice",
        )
    
    use_custom_range = frappe.get_value(
        "POS Profile",
        doc.pos_profile,
        'custom_use_range_of_custom_numbers_for_ury_order_number'
    )
    
    if use_custom_range:
        custom_start = frappe.get_value(
            "POS Profile",
            doc.pos_profile,
            'custom_custom_range_starts_from'
        ) or 1
        custom_end = frappe.get_value(
            "POS Profile",
            doc.pos_profile,
            'custom_custom_range_to'
        ) or 100

        if last_invoice:
            last_invoice_number = int(last_invoice[-5:])
            current_invoice = doc.name
            current_invoice_number = int(current_invoice[-5:])
            
            order_number = (current_invoice_number - last_invoice_number) % (custom_end - custom_start + 1)
            if order_number == 0:
                order_number = custom_end - custom_start + 1
            
            order_number += custom_start - 1
            
            if order_number > 0:
                if doc.order_type == "Aggregators":
                    order_number = "AGR - " + str(order_number)
                frappe.db.set_value(
                    "POS Invoice",
                    doc.name,
                    "custom_ury_order_number",
                    order_number,
                    update_modified=False,
                )
            else:
                frappe.db.set_value(
                    "POS Invoice",
                    doc.name,
                    "custom_ury_order_number",
                    current_invoice_number,
                    update_modified=False,
                )
        else:
            pos_open_name = frappe.get_value(
                "POS Opening Entry",
                {"pos_profile": pos_profile, "status": "Open"},
                "name",
            )

            # invoice = frappe.get_last_doc(
            #     "POS Invoice", filters={"pos_profile": doc.pos_profile}
            # )

            if doc.order_type == "Aggregators":
                aggregator_invoice =frappe.get_last_doc(
                    "POS Invoice", filters={"pos_profile": doc.pos_profile,"order_type": "Aggregators"}
                )
                aggregator_invoice_number = int(aggregator_invoice.name[-5:]) if aggregator_invoice else 0
                aggregator_last_order_number = aggregator_invoice_number - 1

                frappe.db.set_value(
                    "POS Opening Entry", pos_open_name, "custom_ury_last_aggregator_invoice", aggregator_last_order_number
                )
            else:
                invoice = frappe.get_last_doc(
                    "POS Invoice", filters={"pos_profile": doc.pos_profile,"order_type": ["!=", "Aggregators"]}
                )

                invoice_number = int(invoice.name[-5:]) if invoice else 0
                last_order_number = invoice_number - 1

                frappe.db.set_value(
                    "POS Opening Entry", pos_open_name, "custom_ury_last_invoice", last_order_number
                )
            
            default_value = f"AGR - {custom_start}" if doc.order_type == "Aggregators" else str(custom_start)
            frappe.db.set_value(
                "POS Invoice",
                doc.name,
                "custom_ury_order_number",
                default_value,
                update_modified=False,  
            )
    else:
        if last_invoice:
            last_invoice_number = int(last_invoice[-5:])

            current_invoice = doc.name

            current_invoice_number = int(current_invoice[-5:])

            order_number = current_invoice_number - last_invoice_number
            if order_number > 0:
                if doc.order_type == "Aggregators":
                    order_number = "AGR - " + str(order_number)
                frappe.db.set_value(
                    "POS Invoice",
                    doc.name,
                    "custom_ury_order_number",
                    order_number,
                    update_modified=False,
                )
            else:
                frappe.db.set_value(
                    "POS Invoice",
                    doc.name,
                    "custom_ury_order_number",
                    current_invoice_number,
                    update_modified=False,
                )
        else:
            pos_open_name = frappe.get_value(
                "POS Opening Entry",
                {"pos_profile": pos_profile, "status": "Open"},
                "name",
            )

            # invoice = frappe.get_last_doc(
            #     "POS Invoice", filters={"pos_profile": doc.pos_profile}
            # )

            if doc.order_type == "Aggregators":
                aggregator_invoice =frappe.get_last_doc(
                    "POS Invoice", filters={"pos_profile": doc.pos_profile,"order_type": "Aggregators"}
                )
                aggregator_invoice_number = int(aggregator_invoice.name[-5:])
                aggregator_last_order_number = aggregator_invoice_number - 1
                frappe.db.set_value(
                    "POS Opening Entry", pos_open_name, "custom_ury_last_aggregator_invoice", aggregator_last_order_number
                )
            else:
                invoice = frappe.get_last_doc(
                    "POS Invoice", filters={"pos_profile": doc.pos_profile,"order_type": ["!=", "Aggregators"]}
                )

                invoice_number = int(invoice.name[-5:])
                last_order_number = invoice_number - 1

                frappe.db.set_value(
                    "POS Opening Entry", pos_open_name, "custom_ury_last_invoice", last_order_number
                )
            
            default_value = "AGR - 1" if doc.order_type == "Aggregators" else "1"
            frappe.db.set_value(
                "POS Invoice",
                doc.name,
                "custom_ury_order_number",
                default_value,
                update_modified=False,  
            )


def set_last_invoice_in_pos_open(doc, event):
    try:
        invoice = frappe.get_last_doc(
            "POS Invoice", filters={"pos_profile": doc.pos_profile,"order_type": ["!=", "Aggregators"]}
        )
        doc.custom_ury_last_invoice = invoice.name
    except:
        pass 
    try:
        aggregator_invoice =frappe.get_last_doc(
            "POS Invoice", filters={"pos_profile": doc.pos_profile,"order_type": "Aggregators"}
        )
        doc.custom_ury_last_aggregator_invoice = aggregator_invoice.name
    except:
        pass


# def set_order_number(doc, event):
#     pos_profile = doc.pos_profile
#     if doc.order_type == "Aggregators":
#         last_invoice = frappe.get_value(
#             "POS Opening Entry",
#             {"pos_profile": pos_profile, "status": "Open"},
#             "custom_ury_last_aggregator_invoice",
#         )
#     else:
#         last_invoice = frappe.get_value(
#             "POS Opening Entry",
#             {"pos_profile": pos_profile, "status": "Open"},
#             "custom_ury_last_invoice",
#         )
#     if last_invoice:
#         last_invoice_number = int(last_invoice[-5:])

#         current_invoice = doc.name

#         current_invoice_number = int(current_invoice[-5:])

#         order_number = current_invoice_number - last_invoice_number
#         if order_number > 0:
#             if doc.order_type == "Aggregators":
#                 order_number = "AGR - " + str(order_number)
#             frappe.db.set_value(
#                 "POS Invoice",
#                 doc.name,
#                 "custom_ury_order_number",
#                 order_number,
#                 update_modified=False,
#             )
#         else:
#             frappe.db.set_value(
#                 "POS Invoice",
#                 doc.name,
#                 "custom_ury_order_number",
#                 current_invoice_number,
#                 update_modified=False,
#             )
#     else:
#         pos_open_name = frappe.get_value(
#             "POS Opening Entry",
#             {"pos_profile": pos_profile, "status": "Open"},
#             "name",
#         )

#         # invoice = frappe.get_last_doc(
#         #     "POS Invoice", filters={"pos_profile": doc.pos_profile}
#         # )

#         if doc.order_type == "Aggregators":
#             aggregator_invoice =frappe.get_last_doc(
#                 "POS Invoice", filters={"pos_profile": doc.pos_profile,"order_type": "Aggregators"}
#             )
#             aggregator_invoice_number = int(aggregator_invoice.name[-5:])
#             aggregator_last_order_number = aggregator_invoice_number - 1
#             frappe.db.set_value(
#                 "POS Opening Entry", pos_open_name, "custom_ury_last_aggregator_invoice", aggregator_last_order_number
#             )
#         else:
#             invoice = frappe.get_last_doc(
#                 "POS Invoice", filters={"pos_profile": doc.pos_profile,"order_type": ["!=", "Aggregators"]}
#             )

#             invoice_number = int(invoice.name[-5:])
#             last_order_number = invoice_number - 1

#             frappe.db.set_value(
#                 "POS Opening Entry", pos_open_name, "custom_ury_last_invoice", last_order_number
#             )
        
#         default_value = "AGR - 1" if doc.order_type == "Aggregators" else "1"
#         frappe.db.set_value(
#             "POS Invoice",
#             doc.name,
#             "custom_ury_order_number",
#             default_value,
#             update_modified=False,  
#         )