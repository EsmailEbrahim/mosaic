# Copyright (c) 2023, Tridz Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import requests
import json
from frappe.utils.print_format import print_by_server
from frappe.model.document import Document


class URYKOT(Document):
    def on_submit(self):
        self.multi_print_kot()
        self.kotDisplayRealtime()

    def before_submit(self):
        self.userSetting()
        self.setPreparationTime()

    # Function for printing multiple KOTs.
    def multi_print_kot(self):
        # Function for printing a KOT on a specified printer using a print format.
        def print_kot(printer, kot_print_format):
            try:
                # Print KOT using a server function (print_by_server)
                print_by_server("URY KOT", self.name, printer, kot_print_format)
            except:
                pass

        
        pos_kot_printers = frappe.db.get_all(
            "URY Printer Settings",
            fields=["printer", "custom_kot_print_format","custom_kot_print"], 
            filters={"parent": self.pos_profile, "custom_kot_print": 1,"parenttype":"POS Profile"},
            order_by="idx"
        )
    
        pos_print_flag = True
        if self.production:
            production_unit_printers = frappe.get_all(
                "URY Printer Settings",
                fields=["printer", "custom_kot_print_format","custom_kot_print","custom_block_takeaway_kot"], 
                filters={"parent": self.production, "custom_kot_print": 1,"parenttype":"URY Production Unit"},
                order_by="idx"
            )

            # If production unit printer is specified, print KOT in production printer
            if production_unit_printers:
                for printer in production_unit_printers:
                    pos_print_flag = False
                    if printer.custom_block_takeaway_kot == 1 :
                        if self.restaurant_table and self.table_takeaway == 0:
                            print_kot(printer.printer, printer.custom_kot_print_format)
                    else:
                        print_kot(printer.printer, printer.custom_kot_print_format)

                # Check if restaurant table is specified and it's not a takeaway order
                if self.restaurant_table and self.table_takeaway == 0:
                    room = frappe.db.get_value(
                        "URY Table", self.restaurant_table, "restaurant_room"
                    )

                    room_kot_printers = frappe.get_all(
                        "URY Printer Settings",
                        fields=["printer", "custom_kot_print_format","custom_kot_print"],
                        filters={"parent": room, "custom_kot_print": 1,"parenttype":"URY Room"},
                        order_by="idx"
                    )
                    
                    # If room printer is specified, print KOT in room
                    if room_kot_printers:
                        for printer in room_kot_printers:
                            pos_print_flag = False
                            print_kot(printer.printer, printer.custom_kot_print_format)

                    if pos_print_flag == True:
                        if pos_kot_printers:
                            for printer in pos_kot_printers:
                                print_kot(printer.printer, printer.custom_kot_print_format)

                else:
                    if pos_kot_printers:
                        for printer in pos_kot_printers:
                            print_kot(printer.printer, printer.custom_kot_print_format)


    # Function for displaying KOT-related information in real-time On KDS(Kitchen Display System)
    def kotDisplayRealtime(self):
        currentBranch = self.branch
        custom_branch_in_english = frappe.db.get_value("Branch", currentBranch, 'custom_branch_in_english')

        production = self.production
        production_in_english = frappe.db.get_value("URY Production Unit", production, 'production_in_english')

        production_units_roles_map = {}
        production_units = frappe.get_all("URY Production Unit", fields=["name", 
            "role_responsible_for_updating_kot_items_status", 
            "role_responsible_for_confirming_cancelled_kot", 
            "role_responsible_for_serving_kot"])
            
        for production_unit in production_units:
            production_units_roles_map[production_unit.name] = {
                'role_responsible_for_updating_kot_items_status': production_unit.role_responsible_for_updating_kot_items_status,
                'role_responsible_for_confirming_cancelled_kot': production_unit.role_responsible_for_confirming_cancelled_kot,
                'role_responsible_for_serving_kot': production_unit.role_responsible_for_serving_kot,
            }

        kotjson = json.loads(frappe.as_json(self))
        audio_file = frappe.db.get_value(
            "POS Profile", self.pos_profile, "custom_kot_alert_sound"
        )

        # cache_key = "{}_{}_last_kot_time".format(currentBranch, production)
        # cache_key = "{}_{}_last_kot_time".format(custom_branch_in_english, production_in_english)
        cache_key = "{}_last_kot_time".format(custom_branch_in_english)
        time = frappe.cache().get_value(cache_key)

        # kot_channel = "{}_{}_{}".format("kot_update", currentBranch, production)
        # kot_channel = "{}_{}_{}".format("kot_update", custom_branch_in_english, production_in_english)
        kot_channel = "{}_{}".format("kot_update", custom_branch_in_english)
        frappe.publish_realtime(
            kot_channel,
            {"kot": kotjson, "audio_file": audio_file, "last_kot_time": time, "production_units_roles_map": production_units_roles_map},
        )
        frappe.cache().set_value(cache_key, self.time)

    def userSetting(self):
        userDoc = frappe.get_doc("User", self.owner)
        self.user = userDoc.full_name

    def setPreparationTime(self):
        items = self.get("kot_items")
        max_time = 0
        for item in items:
            # Ensure preparation_time and quantity are integers
            preparation_time = int(item.preparation_time) if item.preparation_time else 0
            quantity = int(item.quantity) if item.quantity else 0
            
            # Calculate total item preparation time
            total_item_time = preparation_time if item.parallel_preparation else preparation_time * quantity
            
            # Update max_time with the highest value
            max_time = max(max_time, total_item_time)
        
        # Set the final preparation time
        self.preparation_time = max_time
