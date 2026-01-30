# Booking API Integration Guide

This guide details the integration flow for booking Hotels, Homestays/Villas, Holiday Packages, Houseboats, Activities, and Cabs.

## General Booking Flow

The booking process follows a **3-step flow** for all categories:
1.  **Draft/Review**: Submit booking details to calculate pricing (taxes, discounts).
2.  **Pricing Display**: Fetch the detailed pricing breakdown to show the user.
3.  **Confirm**: Confirm the booking (payment integration step).

### Base URL
`/api/bookings/`

---

## 1. API Endpoints

### Step 1: Create Booking Review (Draft)
**POST** `/api/bookings/review/`
- **Purpose**: Validates availability and creates a temporary draft booking.
- **Headers**: `Authorization: Bearer <token>`

### Step 2: Get Pricing Breakdown
**GET** `/api/bookings/review/?booking_id={id}`
- **Purpose**: Returns the calculated price, taxes, and breakdown for the draft booking.

### Step 3: Confirm Booking
**POST** `/api/bookings/confirm/{id}/`
- **Purpose**: Finalizes the booking with contact and traveller details.
- **Request Payload**:
```json
{
    "title": "Mr.",
    "full_name": "John Doe",
    "email": "john@example.com",
    "phone": "9876543210",
    "country_code": "+91",
    "special_requests": "Late check-in",
    "is_gst_required": true, // or false
    "gst_number": "GST123",  // Optional
    "company_name": "Acme Corp", // Optional
    "company_address": "Kochi", // Optional
    "travellers": [1, 2] // List of Traveller IDs (Optional)
}
```

### Step 4: Get Booking Details (Post-Confirmation)
**GET** `/api/bookings/{id}/`
- **Purpose**: Returns full booking details after confirmation.

---

## 2. Booking Types & Payloads

### A. Hotels
**Booking Type**: `stay`

**Request Payload (Step 1):**
```json
{
    "booking_type": "stay",
    "check_in": "2026-02-09",
    "check_out": "2026-02-11",
    "property_id": 123,
    "items": [
        {
            "room_type_id": 456,
            "room_option_id": 789,  // Optional (e.g., specific meal plan)
            "quantity": 1,
            "adults": 2,
            "children": 0
        }
    ]
}
```

**Sample Response (Step 2 - Pricing):**
```json
{
    "breakdown": [
        {
            "name": "Grand King Room - Breakfast Included",
            "sub_name": "Grand Hyatt Kochi",
            "location": "Kochi, Kerala",
            "quantity": 1,
            "nights": 2,
            "price_per_unit": "6160.00",
            "total": "12320.00",
            "image": null
        }
    ],
    "base_total": "11000.00",
    "taxes": "1320.00",
    "coupon_discount": "0",
    "coupon_applied": null,
    "final_total": "12320.00"
}
```

---

### B. Homestays & Villas (Entire Place)
**Booking Type**: `stay`

**How to Book Entire Place:**
- Even when booking an entire villa/homestay, the system treats the "Entire Property" as a specific **Room Type**.
- You must pass the `room_type_id` corresponding to the "Entire Villa" unit.
- The `property_id` is still required.

**Request Payload (Step 1):**
```json
{
    "booking_type": "stay",
    "check_in": "2026-02-15",
    "check_out": "2026-02-17",
    "property_id": 101,
    "items": [
        {
            "room_type_id": 202, // ID representing "Entire Villa"
            "quantity": 1,
            "adults": 4,
            "children": 2
        }
    ]
}
```

**Sample Response (Step 2 - Pricing):**
```json
{
    "breakdown": [
        {
            "name": "Entire Villa",
            "sub_name": "Munnar Tea Villa",
            "location": "Munnar, Kerala",
            "quantity": 1,
            "nights": 2,
            "price_per_unit": "16800.00",
            "total": "33600.00",
            "image": null
        }
    ],
    "base_total": "30000.00",
    "taxes": "3600.00",
    "coupon_discount": "0",
    "coupon_applied": null,
    "final_total": "33600.00"
}
```

---

### C. Holiday Packages
**Booking Type**: `package`

**Request Payload (Step 1):**
```json
{
    "booking_type": "package",
    "check_in": "2026-03-01",
    "check_out": "2026-03-05", // Derived from duration usually, but required field
    "items": [
        {
            "package_id": 505,
            "quantity": 1, // Number of packages (usually 1 group)
            "adults": 2,
            "children": 1
        }
    ]
}
```

**Sample Response (Step 2 - Pricing):**
```json
{
    "breakdown": [
        {
            "name": "Kerala Backwaters Special",
            "sub_name": "3 Nights / 4 Days",
            "location": "Alleppey",
            "adults": 2,
            "children": 1,
            "price_per_person": "15000.00",
            "total": "53100.0000",
            "image": null
        }
    ],
    "base_total": "45000.00",
    "taxes": "8100.0000",
    "coupon_discount": "0",
    "coupon_applied": null,
    "final_total": "53100.0000"
}
```

---

### D. Houseboats
**Booking Type**: `houseboat`

**Request Payload (Step 1):**
```json
{
    "booking_type": "houseboat",
    "check_in": "2026-02-20",
    "check_out": "2026-02-22",
    "items": [
        {
            "houseboat_id": 606,
            "quantity": 1,
            "adults": 4,
            "children": 0
        }
    ]
}
```

**Sample Response (Step 2 - Pricing):**
```json
{
    "breakdown": [
        {
            "name": "Luxury Houseboat",
            "sub_name": "",
            "location": "Alleppey",
            "quantity": 1,
            "nights": 2,
            "price_per_unit": "12000.0",
            "total": "28320.000",
            "image": null
        }
    ],
    "base_total": "24000.0",
    "taxes": "4320.000",
    "coupon_discount": "0",
    "coupon_applied": null,
    "final_total": "28320.000"
}
```

---

### E. Activities
**Booking Type**: `activity`

**Request Payload (Step 1):**
```json
{
    "booking_type": "activity",
    "check_in": "2026-02-10",
    "check_out": "2026-02-13",
    "is_insurance_opted": true,
    "items": [
        {
            "activity_id": 707,
            "quantity": 1,
            "adults": 10,
            "children": 0
        }
    ]
}
```

**Sample Response (Step 2 - Pricing):**
```json
{
    "breakdown": [
        {
            "name": "2 Days, Brahmagiri peek trekking-From Bangalore",
            "sub_name": "2 Days / 3 Nights | Moderate",
            "location": "Bangalore - Wayanad",
            "duration": "2 Days / 3 Nights",
            "adults": 10,
            "children": 0,
            "price_per_person": "945.75",
            "base_price_per_person": "1250.00",
            "total": "11159.8500",
            "image": null,
            "features": [
                {
                    "name": "Sightseeing",
                    "type": "sightseeing",
                    "is_included": true
                },
                {
                    "name": "Meals",
                    "type": "meals",
                    "is_included": true
                }
            ],
            "inclusions": [
                {
                    "name": "Professional Guide",
                    "is_included": true
                },
                {
                    "name": "Personal Expenses",
                    "is_included": false
                }
            ]
        }
    ],
    "base_total": "9457.5",
    "taxes": "1702.350",
    "coupon_discount": "0",
    "coupon_applied": null,
    "final_total": "11759.8500",
    "insurance_fee": 600
}
```

---

### F. Cabs
**Booking Type**: `cab`

**Request Payload (Step 1):**
```json
{
    "booking_type": "cab",
    "check_in": "2026-02-12",
    "check_out": "2026-02-14",
    "payment_option": "part", // "full" or "part"
    "items": [
        {
            "cab_id": 808,
            "quantity": 1,
            "adults": 4, // Passengers
            "children": 0,
            "pickup_location": "Airport",
            "drop_location": "Hotel",
            "pickup_datetime": "2026-02-12T10:00:00",
            "trip_type": "Airport Transfer"
        }
    ]
}
```

**Sample Response (Step 2 - Pricing):**
```json
{
    "breakdown": [
        {
            "name": "Sedan - Dzire or Similar",
            "sub_name": "Sedan",
            "location": "Airport",
            "pickup_location": "Airport",
            "drop_location": "Hotel",
            "pickup_datetime": "2026-02-12T10:00:00",
            "trip_type": "Airport Transfer",
            "quantity": 1,
            "nights": 2,
            "price_per_unit": "2500.00",
            "total": "5900.0000",
            "image": null,
            "payment_options": [
                {
                    "label": "Make full payment now",
                    "value": "full",
                    "amount": 2500.00,
                    "is_default": true
                },
                {
                    "label": "Make part payment now",
                    "value": "part",
                    "amount": 250.00,
                    "description": "Pay the rest to the driver"
                }
            ],
            "inclusions": [
                {
                    "name": "Parking Charges",
                    "value": "Included",
                    "is_included": true
                }
            ]
        }
    ],
    "base_total": "5000.00",
    "taxes": "900.0000",
    "coupon_discount": "0",
    "coupon_applied": null,
    "final_total": "5900.0000",
    "insurance_fee": 0
}
```

---

## 3. Full Booking Detail Response (Post-Confirmation)

After confirming the booking, the API returns the full booking object. This is also available via `GET /api/bookings/{id}/`.

**Sample Confirmed Booking Response:**
```json
{
    "id": 96,
    "formatted_id": "#96",
    "booking_type": "stay",
    "status": "confirmed",
    "refund_status": "none",
    "refund_status_display": "No Refund",
    "cancelled_at": null,
    "total_amount": "12320.00",
    "amount_paid": "0.00",
    "pricing_breakdown": {
        "breakdown": [
            {
                "name": "Grand King Room - Breakfast Included",
                "sub_name": "Grand Hyatt Kochi",
                "location": "Kochi, Kerala",
                "quantity": 1,
                "nights": 2,
                "price_per_unit": "6160.00",
                "total": "12320.00",
                "image": null
            }
        ],
        "base_total": "11000.00",
        "taxes": "1320.00",
        "coupon_discount": "0",
        "coupon_applied": null,
        "final_total": "12320.00"
    },
    "cancellation_policy": null,
    "rules": null,
    "booking_date": "30 Jan 2026, 10:56 AM",
    "title": "Mr.",
    "full_name": "John Doe",
    "email": "john@example.com",
    "phone": "9876543210",
    "country_code": "",
    "special_requests": "",
    "items": [
        {
            "id": 87,
            "property_name": "Grand Hyatt Kochi",
            "property_location": "Kochi, Kerala",
            "room_type_name": "Grand King Room",
            "check_in": "2026-02-09",
            "check_out": "2026-02-11",
            "adults": 2,
            "children": 0,
            "category_display": "Hotel"
        }
    ]
}
```
