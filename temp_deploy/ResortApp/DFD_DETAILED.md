
# Detailed Data Flow Diagram (DFD) - Orchid Resort System

This document provides a detailed breakdown of the data flow within the Orchid Resort Management System, visualizing how information moves between external entities, processes, and data stores.

## Level 0: Context Diagram
*The highest level view, showing the system as a single black box interacting with external entities.*

```mermaid
graph TD
    Guest[Guest]
    Admin[Admin/Manager]
    Staff[Staff/Housekeeping/Chef]
    Vendor[Vendor]
    
    System((Orchid Resort <br/> Management System))
    
    %% Guest Interactions
    Guest -->|Booking Request| System
    Guest -->|Food/Service Order| System
    Guest -->|Payment| System
    System -->|Booking Confirmation| Guest
    System -->|Invoice/Bill| Guest
    
    %% Admin Interactions
    Admin -->|Manage Rates/Rooms| System
    Admin -->|Approve Purchases| System
    System -->|Financial Reports| Admin
    System -->|Inventory Alerts| Admin
    
    %% Staff Interactions
    Staff -->|Update Room Status| System
    Staff -->|Request Stock| System
    Staff -->|Log Maintenance| System
    System -->|Assigned Tasks| Staff
    
    %% Vendor Interactions
    Vendor -->|Supply Goods| System
    System -->|Purchase Order| Vendor
    System -->|Payment| Vendor
```

---

## Level 1: System Decomposition
*Breaking down the main system into its core functional modules.*

```mermaid
graph TD
    %% Entities
    Guest[Guest]
    Staff[Staff]
    Admin[Admin]
    
    %% Processes
    P1((1.0 Booking <br/> Management))
    P2((2.0 Service & <br/> Food Operations))
    P3((3.0 Inventory <br/> Management))
    P4((4.0 Billing & <br/> Checkout))
    
    %% Data Stores
    D1[(Booking Data)]
    D2[(Room Data)]
    D3[(Service/Food DB)]
    D4[(Inventory DB)]
    D5[(Billing DB)]
    
    %% Flow
    Guest -->|Request Room| P1
    P1 <-->|Check Availability| D2
    P1 -->|Create Booking| D1
    P1 -->|Confirm| Guest
    
    Guest -->|Order Food/Service| P2
    P2 <-->|Get Menu/Service List| D3
    P2 -->|Log Order| D5
    P2 -->|Notify| Staff
    
    Staff -->|Request Stock| P3
    P3 <-->|Update Stock Levels| D4
    P3 -->|Issue Items| Staff
    
    Guest -->|Request Checkout| P4
    P4 <-->|Fetch Charges| D5
    P4 <-->|Fetch Usage| D4
    P4 <-->|Fetch Room Rate| D1
    P4 -->|Generate Bill| Guest
```

---

## Level 2: Detailed Process Breakdown

### 2.1 Inventory Management Process
*Detailed flow of how inventory is purchased, stocked, and issued.*

```mermaid
graph LR
    Vendor[Vendor]
    Staff[Staff]
    
    %% Sub-Processes
    P3_1(3.1 Create Purchase Order)
    P3_2(3.2 Receive Goods / GRN)
    P3_3(3.3 Issue Stock)
    P3_4(3.4 Stock Audit & Waste)
    
    %% Stores
    StockDB[(Inventory Stock)]
    PurchaseDB[(Purchase Records)]
    
    %% Flows
    Staff -->|Create PO| P3_1
    P3_1 -->|Send PO| Vendor
    P3_1 -->|Save PO| PurchaseDB
    
    Vendor -->|Deliver Goods| P3_2
    P3_2 -->|Update Stock| StockDB
    P3_2 -->|Update PO Status| PurchaseDB
    
    Staff -->|Request Item| P3_3
    P3_3 <-->|Check Availability| StockDB
    P3_3 -->|Deduct Stock| StockDB
    
    Staff -->|Log Waste/Spoilage| P3_4
    P3_4 -->|Adjust Stock| StockDB
```

### 2.2 Billing & Checkout Logic
*The complex logic of aggregating charges from various sources to form the final bill.*

```mermaid
graph TB
    %% Inputs
    Req[Checkout Request]
    
    %% Processes
    P4_1(4.1 Verify Room Status)
    P4_2(4.2 Audit Consumables)
    P4_3(4.3 Check Asset Damages)
    P4_4(4.4 Aggregate Charges)
    P4_5(4.5 Calculate Tax/GST)
    P4_6(4.6 Generate Final Bill)
    
    %% Data
    RoomDB[(Room Status)]
    OrderDB[(Food/Service Orders)]
    InvDB[(Inventory Audit)]
    BillDB[(Bill Records)]
    
    %% Flow
    Req --> P4_1
    P4_1 <-->|Check Housekeeping| RoomDB
    
    Req --> P4_2
    P4_2 <-->|Compare Used vs Limit| InvDB
    P4_2 -->|Calculate Extra Charge| P4_4
    
    Req --> P4_3
    P4_3 <-->|Check Fixed Assets| InvDB
    P4_3 -->|Add Damage Cost| P4_4
    
    P4_4 <-->|Fetch Food/Service Charges| OrderDB
    P4_4 --> P4_5
    P4_5 -->|Apply GST Rules| P4_6
    P4_6 -->|Save Bill| BillDB
    P4_6 -->|Print| Guest[Guest]
```

## Detailed Explanation of Processes

### 1. Booking Management
*   **Input:** Guest details, Check-in/out dates, Room type.
*   **Process:** The system checks `Room Data` for availability. If available, it creates a record in `Booking Data` and continually updates the room status (Available -> Booked -> Occupied).
*   **Output:** Booking ID, Confirmation SMS/Email.

### 2. Service & Food Operations
*   **Input:** Food Orders (Dine-in/Room Service), Laundry requests, Housekeeping requests.
*   **Process:** Orders are logged against the `Booking ID` and `Room ID`. The kitchen staff receives the order, prepares it, and updates status.
*   **Inventory Link:** Preparing food deducts ingredients from `Inventory DB` (Logic 1.2).
*   **Output:** Service delivered, Charge added to user's "Unbilled" list.

### 3. Inventory Management
*   **Purchase:** Purchasing creates a PO. When goods arrive, `GRN (Goods Received Note)` is processed, increasing `Location Stock`.
*   **Issuance:** Staff "indents" or requests items. If approved, stock moves from "Main Warehouse" to "Kitchen" or "Housekeeping".
*   **Consumption:**
    *   **Consumables:** Deducted when moved to a room or used in a service.
    *   **Fixed Assets:** Tracked by location. Moved but not "consumed" unless damaged/lost.

### 4. Billing & Checkout (The Core Logic)
This is the most critical phase where all data converges.
1.  **Checkout Request:** A pre-check initiated by the Front Desk.
2.  **Verification:**
    *   Housekeeping checks the room.
    *   **Consumables Audit:** System compares "Initial Stock" vs "Actual Left". If usage > complimentary limit, the excess is charged.
    *   **Asset Check:** Verified against the `Asset Registry`. Missing/Damaged items trigger a charge.
3.  **Aggregation:** The system pulls:
    *   Room Charges (Days * Rate).
    *   Food Orders (sum of `food_orders`).
    *   Service Charges (Laundry, Spa, etc.).
    *   Inventory Charges (Consumables overuse).
    *   Damage Charges (Asset damages).
4.  **Taxation:** Appropriate GST (12%, 18%, etc.) is applied to each category separately.
5.  **Finalization:** Payment is processed, and the Booking is marked "Completed". inventory for the room is reset.
