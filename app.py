import streamlit as st
from food_delivery import Customer, DeliveryPartner, MenuItem, Restaurant

st.set_page_config(page_title="OOP Food Delivery System", page_icon="🍔", layout="wide")

st.title("🍔 OOP Food Delivery System")
st.caption("A simple Streamlit interface using classes from food_delivery.py")

# Keep objects available while Streamlit reruns the app.
if "customers" not in st.session_state:
    st.session_state.customers = {}
if "partners" not in st.session_state:
    st.session_state.partners = {}
if "restaurants" not in st.session_state:
    st.session_state.restaurants = {}
if "orders" not in st.session_state:
    st.session_state.orders = {}
if "active_order_id" not in st.session_state:
    st.session_state.active_order_id = None


def money(value):
    return f"₹{value:,.2f}"


def get_order_label(order_id, order):
    return f"Order #{order_id} — {getattr(order, '_status', 'Unknown status')}"


# Create a demo restaurant/menu if none has been added yet.
if not st.session_state.restaurants:
    demo_restaurant = Restaurant("Bawarchi", "MG Road")
    demo_restaurant.add_item(MenuItem("Biryani", 250, False))
    demo_restaurant.add_item(MenuItem("Kebab", 180, False))
    demo_restaurant.add_item(MenuItem("Paneer Roll", 140, True))
    demo_restaurant.add_item(MenuItem("Masala Dosa", 120, True))
    st.session_state.restaurants[demo_restaurant.name] = demo_restaurant

tab_customer, tab_wallet, tab_menu, tab_order, tab_partner, tab_delivery = st.tabs([
    "👤 Create Customer",
    "💰 Wallet",
    "🍽️ Restaurant Menu",
    "🛒 Place Order",
    "🛵 Delivery Partner",
    "🔐 OTP & Delivery",
])

with tab_customer:
    st.subheader("Create a customer")
    with st.form("customer_form", clear_on_submit=True):
        customer_name = st.text_input("Customer name")
        customer_phone = st.text_input("Phone number")
        customer_address = st.text_area("Delivery address")
        create_customer = st.form_submit_button("Create Customer")

    if create_customer:
        if not customer_name.strip() or not customer_phone.strip() or not customer_address.strip():
            st.error("Please fill in the name, phone number, and address.")
        elif customer_name.strip() in st.session_state.customers:
            st.warning("A customer with that name already exists. Please use a different name.")
        else:
            customer = Customer(customer_name.strip(), customer_phone.strip(), customer_address.strip())
            st.session_state.customers[customer_name.strip()] = customer
            st.success(f"Customer '{customer_name.strip()}' created. Starting wallet balance: ₹0.00")

    if st.session_state.customers:
        st.markdown("#### Registered customers")
        for customer in st.session_state.customers.values():
            st.write(
                f"**{customer._name}** · {customer._phone} · "
                f"{customer.address} · Wallet: {money(customer._wallet_balance)}"
            )

with tab_wallet:
    st.subheader("Add money to a customer's wallet")
    if not st.session_state.customers:
        st.info("Create a customer first.")
    else:
        selected_customer_name = st.selectbox(
            "Select customer",
            list(st.session_state.customers.keys()),
            key="wallet_customer",
        )
        wallet_customer = st.session_state.customers[selected_customer_name]
        st.metric("Current wallet balance", money(wallet_customer._wallet_balance))
        with st.form("wallet_form"):
            topup_amount = st.number_input("Amount to add (₹)", min_value=0.0, step=50.0, value=500.0)
            topup_submit = st.form_submit_button("Add to Wallet")
        if topup_submit:
            wallet_customer.add_to_wallet(topup_amount)
            st.success(f"Wallet updated. New balance: {money(wallet_customer._wallet_balance)}")

with tab_menu:
    st.subheader("Restaurant menu")
    restaurant_names = list(st.session_state.restaurants.keys())
    selected_restaurant_name = st.selectbox("Choose restaurant", restaurant_names, key="menu_restaurant")
    restaurant = st.session_state.restaurants[selected_restaurant_name]
    st.write(f"**Location:** {restaurant.location}")
    menu_items = restaurant.get_menu()
    if menu_items:
        st.dataframe(
            [
                {
                    "Food item": item.name,
                    "Price": money(item.price),
                    "Type": "Vegetarian" if item.is_veg else "Non-vegetarian",
                }
                for item in menu_items
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("This restaurant's menu is empty.")

    with st.expander("Add a menu item"):
        with st.form("add_menu_item_form", clear_on_submit=True):
            new_item_name = st.text_input("Item name")
            new_item_price = st.number_input("Price (₹)", min_value=1.0, step=10.0, value=100.0)
            new_item_veg = st.checkbox("Vegetarian")
            add_item_submit = st.form_submit_button("Add Item")
        if add_item_submit:
            if not new_item_name.strip():
                st.error("Enter an item name.")
            else:
                restaurant.add_item(MenuItem(new_item_name.strip(), new_item_price, new_item_veg))
                st.success(f"Added {new_item_name.strip()} to {restaurant.name}'s menu.")

with tab_order:
    st.subheader("Place an order")
    if not st.session_state.customers:
        st.info("Create a customer first.")
    else:
        restaurant_names = list(st.session_state.restaurants.keys())
        with st.form("place_order_form"):
            order_customer_name = st.selectbox("Customer", list(st.session_state.customers.keys()))
            order_restaurant_name = st.selectbox("Restaurant", restaurant_names)
            order_restaurant = st.session_state.restaurants[order_restaurant_name]
            available_items = order_restaurant.get_menu()
            if available_items:
                selected_item_names = st.multiselect(
                    "Select food items",
                    options=[item.name for item in available_items],
                )
            else:
                selected_item_names = []
                st.warning("Add menu items to this restaurant before placing an order.")
            submit_order = st.form_submit_button("Place Order")

        if submit_order:
            customer = st.session_state.customers[order_customer_name]
            restaurant = st.session_state.restaurants[order_restaurant_name]
            item_lookup = {item.name: item for item in restaurant.get_menu()}
            chosen_items = [item_lookup[name] for name in selected_item_names if name in item_lookup]

            if not chosen_items:
                st.error("Select at least one food item.")
            else:
                order = customer.place_order(restaurant, chosen_items)
                order_id = getattr(order, "_order_id", len(st.session_state.orders) + 1)
                # Avoid collisions if an imported class uses its own order counter.
                while order_id in st.session_state.orders:
                    order_id = f"{order_id}-{len(st.session_state.orders) + 1}"
                st.session_state.orders[order_id] = {
                    "order": order,
                    "customer_name": order_customer_name,
                    "restaurant_name": order_restaurant_name,
                    "partner_name": None,
                    "items": chosen_items,
                }
                st.session_state.active_order_id = order_id
                total = order.calculate_bill()
                st.success(f"Order #{order_id} placed successfully!")
                st.write(f"**Bill total:** {money(total)}")
                st.write(f"**Estimated time:** {order.estimated_time()} minutes")
                st.info("For this OOP exercise, the OTP is stored on the order object. Share it with the delivery partner for testing.")

with tab_partner:
    st.subheader("Create a delivery partner")
    with st.form("partner_form", clear_on_submit=True):
        partner_name = st.text_input("Delivery partner name")
        partner_phone = st.text_input("Partner phone number")
        partner_vehicle = st.selectbox("Vehicle", ["Bike", "Scooter", "Bicycle", "Car"])
        create_partner = st.form_submit_button("Create Delivery Partner")

    if create_partner:
        if not partner_name.strip() or not partner_phone.strip():
            st.error("Enter the partner's name and phone number.")
        elif partner_name.strip() in st.session_state.partners:
            st.warning("A delivery partner with that name already exists.")
        else:
            partner = DeliveryPartner(partner_name.strip(), partner_phone.strip(), partner_vehicle)
            st.session_state.partners[partner_name.strip()] = partner
            st.success(f"Delivery partner '{partner_name.strip()}' created.")

    if st.session_state.partners:
        st.markdown("#### Delivery partners")
        for partner in st.session_state.partners.values():
            status = "Available" if partner.is_available else "Busy"
            st.write(f"**{partner._name}** · {partner.vehicle} · {status}")

    st.divider()
    st.markdown("#### Assign a partner to an order")
    if not st.session_state.orders:
        st.info("Place an order first.")
    elif not st.session_state.partners:
        st.info("Create a delivery partner first.")
    else:
        order_keys = list(st.session_state.orders.keys())
        chosen_order_key = st.selectbox(
            "Order",
            order_keys,
            format_func=lambda key: get_order_label(key, st.session_state.orders[key]["order"]),
            key="assign_order",
        )
        available_partners = [
            name for name, partner in st.session_state.partners.items()
            if partner.is_available or st.session_state.orders[chosen_order_key]["partner_name"] == name
        ]
        if available_partners:
            chosen_partner_name = st.selectbox("Available delivery partner", available_partners, key="assign_partner")
            if st.button("Accept Order", key="accept_order_button"):
                record = st.session_state.orders[chosen_order_key]
                partner = st.session_state.partners[chosen_partner_name]
                partner.accept_order(record["order"])
                record["partner_name"] = chosen_partner_name
                st.session_state.active_order_id = chosen_order_key
                st.success(f"{chosen_partner_name} accepted order #{chosen_order_key}.")
        else:
            st.warning("No delivery partners are currently available.")

with tab_delivery:
    st.subheader("Verify OTP and complete delivery")
    if not st.session_state.orders:
        st.info("Place an order first.")
    else:
        order_keys = list(st.session_state.orders.keys())
        default_index = order_keys.index(st.session_state.active_order_id) if st.session_state.active_order_id in order_keys else 0
        delivery_order_key = st.selectbox(
            "Select order",
            order_keys,
            index=default_index,
            format_func=lambda key: get_order_label(key, st.session_state.orders[key]["order"]),
            key="delivery_order",
        )
        record = st.session_state.orders[delivery_order_key]
        order = record["order"]
        st.write(f"**Customer:** {record['customer_name']}")
        st.write(f"**Restaurant:** {record['restaurant_name']}")
        st.write(f"**Bill:** {money(order.calculate_bill())}")
        st.write(f"**Estimated delivery:** {order.estimated_time()} minutes")
        st.write(f"**Status:** {getattr(order, '_status', 'Unknown')}")
        if getattr(order, "_status", "") != "Delivered":
            st.info(f"Demo OTP for this order: {getattr(order, '_otp', 'Check your class implementation')}")

        assigned_partner = record["partner_name"]
        if not assigned_partner:
            st.warning("Assign a delivery partner and accept the order first.")
        elif getattr(order, "_status", "") == "Delivered":
            st.success("This order has already been delivered.")
        else:
            st.write(f"**Delivery partner:** {assigned_partner}")
            with st.form("otp_form"):
                entered_otp = st.text_input("Enter delivery OTP", max_chars=6)
                verify_submit = st.form_submit_button("Verify OTP & Complete Delivery")

            if verify_submit:
                partner = st.session_state.partners[assigned_partner]
                try:
                    otp_value = int(entered_otp.strip())
                except ValueError:
                    otp_value = None

                if otp_value is None:
                    st.error("Enter a valid numeric OTP.")
                elif getattr(order, "_status", "") not in ("Accepted", "Order Accepted"):
                    st.error("The order must be accepted before delivery.")
                elif not order.verify_otp(otp_value):
                    st.error("Incorrect OTP. The order has not been delivered.")
                else:
                    partner.deliver(order, otp_value)
                    # Keep the UI robust if a project implementation uses a different accepted status.
                    if getattr(order, "_status", "") != "Delivered":
                        order.update_status("Delivered")
                    partner.is_available = True
                    customer = st.session_state.customers[record["customer_name"]]
                    customer.notify("Order delivered")
                    partner.notify("Order delivered")
                    st.success("OTP verified. Delivery completed successfully!")

st.divider()
st.caption("Note: Objects are stored in Streamlit session state and reset when the session is restarted.")
