import json

import frappe
from ury.ury_pos.api import getBranch
from frappe.utils import get_datetime


# #######################################################################################################
def send_fetch_table_order_status_to_pos(branch, user, event):
    custom_branch_in_english = frappe.get_cached_value("Branch", branch, 'custom_branch_in_english')
    kot_channel = "{}_{}_{}".format("kot_update", custom_branch_in_english, user)
    frappe.publish_realtime(
        kot_channel,
        {"event": event},
    )
# #######################################################################################################


def send_fetch_kot_socket_to_mosaic(branch, event):
    custom_branch_in_english = frappe.get_cached_value("Branch", branch, 'custom_branch_in_english')
    kot_channel = "{}_{}_fetch".format("kot_update", custom_branch_in_english)
    frappe.publish_realtime(
        kot_channel,
        {"event": event},
    )


# Function to set order status in a KOT document
@frappe.whitelist()
def serve_kot(name, time):
    current_time = get_datetime()
    creation_time = frappe.db.get_value("URY KOT",name,"creation")

    production_time = current_time - creation_time
    production_time_minutes = production_time.total_seconds() / 60
    frappe.db.set_value("URY KOT", name, "start_time_serv", time)
    frappe.db.set_value("URY KOT",name,"production_time",production_time_minutes)
    frappe.db.set_value("URY KOT", name, "order_status", "Served")

    branch = frappe.db.get_value("URY KOT", name, "branch")

    send_fetch_kot_socket_to_mosaic(branch, "serve_kot")


@frappe.whitelist()
def strike_kot_item(item_name, striked):
    frappe.db.set_value("URY KOT Items", item_name, "striked", striked)
    parent = frappe.db.get_value("URY KOT Items", item_name, "parent")

    branch = frappe.db.get_value("URY KOT", parent, "branch")

    send_fetch_kot_socket_to_mosaic(branch, "strike_kot_item")


# Function to mark it as verified by a user in cancel type KOT
@frappe.whitelist()
def confirm_cancel_kot(name, user):
    frappe.db.set_value("URY KOT", name, "verified", 1)
    frappe.db.set_value("URY KOT", name, "verified_by", user)

    branch = frappe.db.get_value("URY KOT", name, "branch")

    send_fetch_kot_socket_to_mosaic(branch, "confirm_cancel_kot")


@frappe.whitelist(allow_guest=True)
def get_site_name():
    return {"site_name": frappe.local.site}

@frappe.whitelist()
def kot_list():
    today = frappe.utils.now()

    branch = getBranch()
    custom_branch_in_english = frappe.db.get_value("Branch", branch, 'custom_branch_in_english')

    production_units_for_current_user = []
    production_units_roles_map = {}
    production_units = frappe.get_all("URY Production Unit", fields=["name", 
        "role_responsible_for_updating_kot_items_status", 
        "role_responsible_for_confirming_cancelled_kot", 
        "role_responsible_for_serving_kot"])
    
    user_roles = frappe.get_roles(frappe.session.user)
    is_restaurant_manager = "URY Restaurant Manager" in user_roles

    if not is_restaurant_manager:
        for production_unit in production_units:
            production_units_roles_map[production_unit.name] = {
                'role_responsible_for_updating_kot_items_status': production_unit.role_responsible_for_updating_kot_items_status,
                'role_responsible_for_confirming_cancelled_kot': production_unit.role_responsible_for_confirming_cancelled_kot,
                'role_responsible_for_serving_kot': production_unit.role_responsible_for_serving_kot,
            }

            if any(role in user_roles for role in [
                production_unit.role_responsible_for_updating_kot_items_status,
                production_unit.role_responsible_for_confirming_cancelled_kot,
                production_unit.role_responsible_for_serving_kot
            ]):
                if production_unit.name not in production_units_for_current_user:
                    production_units_for_current_user.append(production_unit.name)

    kot_alert_time = frappe.db.get_value(
        "POS Profile", {"branch": branch}, "custom_kot_warning_time"
    )
    daily_order_number = frappe.db.get_value(
        "POS Profile", {"branch": branch}, "custom_reset_order_number_daily"
    )
    three_hours_ago = frappe.utils.add_to_date(today, hours=-3)
    audio_alert = frappe.db.get_value(
        "POS Profile", {"branch": branch}, "custom_kot_alert"
    )

    kot_filters = {
        "order_status": "Ready For Prepare",
        "branch": branch,
        "type": [
            "in",
            [
                "New Order",
                "Order Modified",
                "Duplicate",
                "Cancelled",
                "Partially cancelled",
            ],
        ],
        "docstatus": 1,
        "verified": 0,
        "creation": (">=", three_hours_ago),
    }

    if not is_restaurant_manager:
        kot_filters["production"] = ["in", production_units_for_current_user]

    kotList = frappe.get_list(
        "URY KOT",
        fields=["name"],
        filters=kot_filters,
        order_by="creation desc",
    )
    KOT = []
    for kot in kotList:
        kotdoc = frappe.get_doc("URY KOT", kot.name)
        kotjson = json.loads(frappe.as_json(kotdoc))
        KOT.append(kotjson)
    return {
        "KOT": KOT,
        "Branch": branch,
        "custom_branch_in_english": custom_branch_in_english,
        "kot_alert_time": kot_alert_time,
        "audio_alert": audio_alert,
        "daily_order_number":daily_order_number,
        "production_units_roles_map": production_units_roles_map,
    }

